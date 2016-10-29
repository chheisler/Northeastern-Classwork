#include "vm/pagetable.h"
#include <stddef.h>
#include <stdlib.h>
#include "threads/vaddr.h"
#include "vm/frame.h"
#include "vm/swap.h"
#include "threads/palloc.h"
#include "userprog/pagedir.h"
#include "threads/thread.h"
#include "threads/synch.h"
#include "filesys/filesys.h"

/* Lock for filesystem. */
extern struct lock filesys_lock;

/* Definitions for traversing the supplemental page table. */
#define PT_DEPTH 4
#define PT_NODE_LEN 32
#define PT_NODE_SIZE sizeof (uint32_t *) * PT_NODE_LEN
#define PT_IDX_SHIFT 5
#define PT_IDX_BITS 0x1f

/* Retrieve a page from the supplementary page table. */
struct page *
pagetable_get_page (pt_node_t pt, void *va)
{
  int i, idx;

  /* Follow the table until we hit a null node or find the page. */
  for (i = PT_DEPTH - 1; i >= 0; i--)
    {
      if (pt == NULL)
        return pt;
      idx = (uintptr_t) pg_no (va) >> PT_IDX_SHIFT * i & PT_IDX_BITS;
      pt = (pt_node_t) pt[idx];
    }

  return (struct page *) pt;
}

/* Add a page to the supplementary page table. */
void
pagetable_set_page (pt_node_t *pt, struct page *pg, void *va)
{
  int i, idx;

  ASSERT (is_user_vaddr (va));

  for (i = PT_DEPTH - 1; i >= 0; i--)
    {
      /* If the node doesn't exist yet create it. */
      if (*pt == NULL)
        {
          *pt = malloc (PT_NODE_SIZE);
          if (*pt == NULL)
            PANIC ("Unable to expand supplementary page table!");
          memset (*pt, 0, PT_NODE_SIZE);
        }

      /* Get the next index and node. */
      idx = (uintptr_t) pg_no (va) >> PT_IDX_SHIFT * i & PT_IDX_BITS;
      pt = (pt_node_t *) (&(*pt)[idx]);
    }

  *pt = pg;
}

void clear_page (struct page *pg);

/* Destroy a process's supplementary page table. */
void
pagetable_destroy (pt_node_t pt)
{
  destroy (pt, 0, 0);
}

/* Recursively destroy a process's supplementary page table. */
void
destroy (pt_node_t pt, int depth)
{
  int i;

  /* If this node is null return. */
  if (pt == NULL)
    return;

  /* If we've reached the bottom clear the page. */
  if (depth == PT_DEPTH)
    {
      clear_page ((struct page *) pt);
    }

  /* Else recurse on all of the node's children. */
  else
    {
      depth++;
      for (i = 0; i < PT_NODE_LEN; i++)
        destroy ((pt_node_t) pt[i], depth);
    }

  free (pt);
}

size_t clear (pt_node_t *pt, void *va, size_t size, size_t max, int depth);

/* Clear a range of virtual memory from the a page table. */
void
pagetable_clear (pt_node_t *pt, void *va, size_t size)
{
  size_t max = ((unsigned) -1 >> PGBITS) + 1;

  frame_lock ();
  clear (pt, va, size, max, 0);
  frame_unlock ();
}

/* Recursively clear a section of a process's supplementary page table. */
size_t
clear (pt_node_t *pt, void *va, size_t size, size_t max, int depth)
{
  ASSERT (is_user_vaddr (va));
  size_t cleared = 0;

  /* If we're at the bottom of the table clear the page. */
  if (depth == PT_DEPTH)
    {
      struct page *pg = (struct page *) (*pt);
      clear_page (pg);
      struct thread *cur = thread_current ();
      void *kpage = pagedir_get_page (cur->pagedir, va);
      if (kpage != NULL)
        {
          pagedir_clear_page (cur->pagedir, va);
          palloc_free_page (kpage);
        }
      cleared = 1;
    }

  /* Else clear our children until we reach the size to clear. */
  else
    {
      int idx = (uintptr_t) pg_no (va) >> PT_IDX_SHIFT
              * (PT_DEPTH - 1 - depth) & PT_IDX_BITS;
      while (idx < PT_NODE_SIZE && cleared < size)
        {
          pt_node_t *next = (pt_node_t *) (&(*pt)[idx++]);
          cleared += clear (next, va + cleared * PGSIZE, size,
                            max / PT_NODE_LEN, depth + 1);
        }
    }

  /* If we cleared everything lowr down the table free this node. */
  if (cleared == max)
    {
      free (*pt);
      *pt = NULL;
    }

  return cleared;
}

/* Clear a page in the table. */
void
clear_page (struct page *pg)
{
  if ((pg->flags & PAGE_TYPE_BITS) == PAGE_EXEC
      || (pg->flags & PAGE_TYPE_BITS) == PAGE_MMAP)
    free (pg->data);
  else if ((pg->flags & PAGE_TYPE_BITS) == PAGE_SWAP)
      swap_free (pg->data);
}
