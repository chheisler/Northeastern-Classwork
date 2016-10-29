#include <bitmap.h>
#include <stdlib.h>
#include "threads/vaddr.h"
#include "threads/palloc.h"
#include "threads/interrupt.h"
#include "threads/thread.h"
#include "threads/synch.h"
#include "vm/pagetable.h"
#include "filesys/file.h"
#include "filesys/filesys.h"
#include "vm/stack.h"

/* Lock for file system access. */
extern struct lock filesys_lock;

/* The frame table for user memory. */
struct frame_table
  {
    struct frame *entries;  /* Array of frames in the table. */
    size_t size;            /* The size of the frame table. */
    size_t clock;           /* Current index for eviction algorithm. */
    struct lock lock;       /* Lock for synchronizing access. */
    struct bitmap *pin_map; /* Bitmap of pinned frame indices. */
  };

/* A frame in the frame table. */
struct frame
  {
    struct thread *thread; /* The thread that owns this frame. */
    void *page;            /* The user page address mapped to this frame. */
  };

/* The frame table. */
static struct frame_table frame_table;

/* Initialize the frame table. */
void
frame_init (void)
{
  size_t ft_size = palloc_user_pool_size ();
  frame_table.entries = malloc (ft_size * sizeof (struct frame));
  if (frame_table.entries == NULL)
    PANIC ("Unable to allocate space for frame table!");
  frame_table.size = ft_size;
  frame_table.clock = 0;
  lock_init (&frame_table.lock);
  frame_table.pin_map = bitmap_create (frame_table.size);
  if (frame_table.pin_map == NULL)
    PANIC ("Unable to allocate space for pinned map!");
}

void set_page (struct page *pg, void *upage, bool pin);
size_t frame_no (void *kpage);

/* Allocate a frame for a user page in a page directory. */
void
frame_set_page (struct page *pg, void* upage)
{
  lock_acquire (&frame_table.lock);
  set_page (pg, upage, false);
}

/* Pin the frame for a virtual user address in memory. */
void
frame_pin (void *upage)
{
  void *kpage;
  size_t frame_idx;
  struct thread *cur = thread_current ();

  /* Check whether we still have a frame for the page. */
  lock_acquire (&frame_table.lock);
  kpage = pagedir_get_page (cur->pagedir, upage);
  
  /* If we don't have a frame get one first. */
  if (kpage == NULL)
    {
      struct page *pg = pagetable_get_page (cur->pagetable, upage);

      /* If no entry in page table check for stack growth. */
      if (pg == NULL)
        {
          if (stack_is_growth (upage, cur->esp))
            {
              pg = stack_page ();
              pagetable_set_page (cur->pagetable, pg, upage);
            }
          else
            {
              lock_release (&frame_table.lock);
              cur->proc->exit = -1;
              thread_exit ();
            }
        }
      set_page (pg, upage, true); 
    }

  /* If we already have a frame pin it immediately. */
  else
    {
      frame_idx = frame_no (kpage);
      bitmap_set (frame_table.pin_map, frame_idx, true);
      lock_release (&frame_table.lock);
    }
}

/* Unpin the frame for a virtual user address. */
void
frame_unpin (void *upage)
{
  struct thread *cur = thread_current ();
  void *kpage = pagedir_get_page (cur->pagedir, upage);
  bitmap_set (frame_table.pin_map, frame_no (kpage), false);
}

/* Allocate a frame for a virtual user address. */
void
set_page (struct page *pg, void *upage, bool pin)
{
  struct thread *cur = thread_current ();
  size_t start = frame_table.clock, idx = -1, alt_idx = -1;
  bool found, dirty_alt, accessed, dirty;
  struct frame *f;
  struct page *evict;
  void *kpage;

  ASSERT (pg_ofs (upage) == 0);
  ASSERT (pagedir_get_page (cur->pagedir, upage) == NULL);
  ASSERT (lock_held_by_current_thread (&frame_table.lock));

  /* Relinquish the filesystem if we have it. */
  bool locked = lock_held_by_current_thread (&filesys_lock);
  if (locked)
    lock_release (&filesys_lock);

  /* Try to obtain an unused page of user memory. */
  kpage = palloc_get_page (PAL_USER | PAL_ZERO);
  found = kpage != NULL;

  /* If we were able to get a page of memory use it. */
  if (found)
      idx = frame_no (kpage);

  /* Else find a page to evict. */
  else
    {
      do
        {
          f = &frame_table.entries[frame_table.clock];
          if (!bitmap_test (frame_table.pin_map, frame_table.clock))
            {
              /* If the page has not been recently accessed us it. */
              accessed = pagedir_is_accessed (f->thread->pagedir, f->page);
              if (!accessed)
                idx = frame_table.clock;

              /* Else check if page is better backup candidate. */
              else
                {
                  pagedir_set_accessed (f->thread->pagedir, f->page, false);
                  dirty = pagedir_is_dirty (f->thread->pagedir, f->page);
                  if (alt_idx == -1 || dirty_alt && !dirty)
                    {
                      alt_idx = frame_table.clock;
                      dirty_alt = dirty;
                    }
                }
            }
          frame_table.clock = (frame_table.clock + 1) % frame_table.size;
        }
      while (idx == -1 && frame_table.clock != start);
      idx = (idx == -1) ? alt_idx : idx;
      ASSERT (idx != -1);
      kpage = palloc_user_pool_base () + PGSIZE * idx;
    }
  f = &frame_table.entries[idx];

  /* If no frame was found check whether the frame to evict is dirty. */
  if (!found)
    {
      dirty = pagedir_is_dirty (f->thread->pagedir, f->page);
      pagedir_clear_page (f->thread->pagedir, f->page);
      if (dirty)
        {
          evict = pagetable_get_page (f->thread->pagetable, f->page);
          if ((pg->flags & PAGE_TYPE_BITS) == PAGE_MMAP)
            lock_acquire (&filesys_lock);
          else
            {
              if ((evict->flags & PAGE_TYPE_BITS) == PAGE_EXEC)
                free (evict->data);
              evict->flags &= ~PAGE_TYPE_BITS;
              evict->flags |= PAGE_SWAP;
              swap_lock ();
            }
        }
    }

  /* Pin the frame and release the frame table lock. */
  bitmap_set (frame_table.pin_map, idx, true);
  lock_release (&frame_table.lock);

  /* If no page was found evict the best candidate and use its page. */
  if (!found && dirty)
    {
      /* If the page is memory mapped write it back to the file. */
      if ((evict->flags & PAGE_TYPE_BITS) == PAGE_MMAP)
        {
          struct file_page *fp = (struct file_page *) pg->data;
          //lock_acquire (&filesys_lock);
          file_seek (fp->file, fp->offset);
          if (file_write (fp->file, kpage, fp->size) != fp->size)
            PANIC ("Unable to write data back to file!");
          lock_release (&filesys_lock);
        }

      /* Else write it to swap. */
      else
        {
          evict->data = swap_to_disk (kpage);
          swap_unlock ();
        }
    }

  /* If the page is a swap page bring it in from swap. */
  if ((pg->flags & PAGE_TYPE_BITS) == PAGE_SWAP)
    {
      swap_lock ();
      if (!swap_to_memory (pg->data, kpage))
        PANIC ("Unable to swap data back into memory!");
      swap_unlock ();
    }

  /* If the page is a zero page just zero it. */
  else if ((pg->flags & PAGE_TYPE_BITS) == PAGE_ZERO)
    {
      memset (kpage, 0, PGSIZE);
    }

  /* If the page is a file bring it in from the file. */
  else if ((pg->flags & PAGE_TYPE_BITS) == PAGE_EXEC
           || (pg->flags & PAGE_TYPE_BITS) == PAGE_MMAP)
    {
      struct file_page *fp = (struct file_page *) pg->data;
      lock_acquire (&filesys_lock);
      file_seek (fp->file, fp->offset);
      if (file_read (fp->file, kpage, fp->size) != fp->size)
        PANIC ("Unable to read file into frame!");
      lock_release (&filesys_lock);
      memset (kpage + fp->size, 0, PGSIZE - fp->size);
    }

  /* We should never get here, if we do something is wrong. */
  else
    {
      PANIC ("Unknown page type!");
    }

  /* Add the page to the frame table and install it. */
  f->thread = cur;
  f->page = upage;
  pagedir_set_page (cur->pagedir, upage, kpage, pg->flags & PAGE_WRITE_BIT);
  dirty = (pg->flags & PAGE_TYPE_BITS) == PAGE_SWAP;
  pagedir_set_dirty (cur->pagedir, upage, dirty);

  /* Release our pin if we don't need it anymore. */
  if (!pin)
    bitmap_set (frame_table.pin_map, idx, false);

  /* Reclaim the filesystem if we were using it. */
  if (locked)
      lock_acquire (&filesys_lock);
}

/* Return the frame number for a physical memory page. */
size_t
frame_no (void *kpage)
{
  return pg_no (kpage - (uintptr_t) palloc_user_pool_base ());
}

/* Lock the frame table. */
void
frame_lock (void)
{
  lock_acquire (&frame_table.lock);
}

/* Unlock the frame table. */
void
frame_unlock (void)
{
  lock_release (&frame_table.lock);
}
