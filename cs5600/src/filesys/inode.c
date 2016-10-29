#include "filesys/inode.h"
#include <list.h>
#include <debug.h>
#include <round.h>
#include <string.h>
#include "filesys/filesys.h"
#include "filesys/free-map.h"
#include "threads/malloc.h"
#include "threads/thread.h"
#include <stdio.h>

/* Identifies an inode. */
#define INODE_MAGIC 0x494e4f44

/* Counts for different block types. */
#define DIRECT_BLKS 4
#define INDIRECT_BLKS 9
#define DOUBLE_INDIRECT_BLKS 1

#define INDIRECT_IDX 4
#define DOUBLE_INDIRECT_IDX 13
#define INODE_BLK_PTRS 14
#define INDIRECT_BLK_PTRS 128

/* Max file size: 4*512 + 9*128*512 + 1*128*128*512 = 8980480 */
#define MAX_FILE_SIZE 8980480

/* On-disk inode.
   Must be exactly BLOCK_SECTOR_SIZE bytes long. */
struct inode_disk
  {
    off_t length;                       /* File size in bytes. */
    unsigned magic;                     /* Magic number. */
    bool is_dir;                        /* Whether this is a directory. */
    uint32_t direct_idx;                /* Direct block inex. */
    uint32_t indirect_idx;              /* Indirect block index. */
    uint32_t double_indirect_idx;       /* Double indirect block index. */
    block_sector_t ptr[INODE_BLK_PTRS]; /* Pointers to blocks */
    uint32_t unused[108];               /* Not used. */
  };

struct indirect_block {
  block_sector_t ptr[INDIRECT_BLK_PTRS];
};

bool allocate_inode (struct inode_disk *disk_inode);
static size_t expand_indirect (struct inode *, size_t);
static size_t expand_double_indirect (struct inode *, size_t);
size_t expand_double_indirect_inner (struct inode *inode,
                                     size_t new_sectors,
                                     block_sector_t *outer_block);

static void read_block (block_sector_t sector, void *buffer);
static void write_block (block_sector_t sector, void *buffer);
static void zero_block (block_sector_t sector);

/* A buffer cache entry. */
struct buffer
  {
    block_sector_t sector;           /* The sector in the buffer. */
    uint32_t flags;                  /* Buffer state flags. */
    struct lock state;               /* Lock for accessing buffer state. */
    struct lock io;                  /* Lock for IO on buffer. */
    uint8_t data[BLOCK_SECTOR_SIZE]; /* The data in the buffer. */
  };

/* Buffer state flags. */
#define BUFFER_META 1
#define BUFFER_DIRTY 2
#define BUFFER_ACCESSED 4
#define BUFFER_PIN 8
#define BUFFER_PINS (-1 << 3)
#define BUFFER_FLUSH 16

/* Cache read ahead queue. */
struct read_aheads
  {
    struct list list;      /* Queue of sectors to be read ahead. */
    struct lock lock;      /* Lock for modifying queue. */
    struct semaphore sema; /* Semaphore for signaling workers. */
  };

/* A request for a read ahead. */
struct read_ahead
  {
    struct list_elem elem; /* List element for read ahead queue. */
    block_sector_t sector; /* Sector to read ahead. */
  };

/* Number of read ahead workers. */
#define READ_AHEAD_WORKERS 2

/* The read ahead queue. */
static struct read_aheads read_aheads;

/* Size of the buffer cache. */
#define CACHE_SIZE 64

/* Struct for the buffer cache. */
struct cache
  {
    struct buffer entries[CACHE_SIZE]; /* The entries in the cache. */
    unsigned clock;                    /* Clock for evicting sectors. */
    struct lock lock;                  /* Lock for evicting sectors. */
  };

/* The buffer cache. */
static struct cache cache;

void cache_flush_worker (void);
void cache_read_ahead_worker (void);

/* Initialize the cache buffer. */
void
cache_init (void)
{
  int i;
  struct buffer *buffer;

  /* Initialize the buffer cache. */
  lock_init (&cache.lock);
  for (i = 0; i < CACHE_SIZE; i++)
    {
      buffer = &cache.entries[i];
      buffer->sector = -1;
      lock_init (&buffer->state);
      lock_init (&buffer->io);
    }

  /* Initialize the cache flush worker. */
  thread_create ("flush", PRI_MAX, cache_flush_worker, NULL);

  /* Initialize the read ahead queue and workers. */
  list_init (&read_aheads.list);
  lock_init (&read_aheads.lock);
  sema_init (&read_aheads.sema, 0);
  for (i = 0; i < READ_AHEAD_WORKERS; i++)
    thread_create ("read_ahead", PRI_MAX, cache_read_ahead_worker, NULL);
}

/* Returns the number of sectors to allocate for an inode SIZE
   bytes long. */
static inline size_t
bytes_to_data_sectors (off_t size)
{
  return DIV_ROUND_UP (size, BLOCK_SECTOR_SIZE);
}

static size_t
bytes_to_indirect_sectors (off_t size)
{
  if (size <= BLOCK_SECTOR_SIZE*DIRECT_BLKS)
    return 0;
  size -= BLOCK_SECTOR_SIZE*DIRECT_BLKS;
  return DIV_ROUND_UP(size, BLOCK_SECTOR_SIZE*INDIRECT_BLK_PTRS);
}

static size_t bytes_to_double_indirect_sector (off_t size)
{
  if (size <= BLOCK_SECTOR_SIZE*(DIRECT_BLKS +
        INDIRECT_BLKS*INDIRECT_BLK_PTRS))
    return 0;
  return DOUBLE_INDIRECT_BLKS;
}

/* In-memory inode. */
struct inode 
  {
    struct list_elem elem;              /* Element in inode list. */
    block_sector_t sector;              /* Sector number of disk location. */
    int open_cnt;                       /* Number of openers. */
    bool removed;                       /* True if deleted, false otherwise. */
    bool is_dir;                        /* Whether inode is directory. */
    int deny_write_cnt;                 /* 0: writes ok, >0: deny writes. */
    off_t length;                       /* File size in bytes. */
    block_sector_t direct_idx;          /* Direct block index. */
    block_sector_t indirect_idx;        /* Indirect block index */
    block_sector_t double_indirect_idx; /* Double indirect block index. */
    block_sector_t ptr[INODE_BLK_PTRS]; /* Pointers to blocks. */
    struct lock lock;                   /* Lock for expansion. */
  };

/* Returns the block device sector that contains byte offset POS
   within INODE.
   Returns -1 if INODE does not contain data for a byte at offset
   POS. */
static block_sector_t
byte_to_sector (const struct inode *inode, off_t length, off_t pos) 
{
  ASSERT (inode != NULL);
  if (pos < length)
    {
      uint32_t idx;
      block_sector_t sector;
      block_sector_t *block = malloc (BLOCK_SECTOR_SIZE);

      if (pos < BLOCK_SECTOR_SIZE * DIRECT_BLKS)
        sector = inode->ptr[pos / BLOCK_SECTOR_SIZE];
      else if (pos < BLOCK_SECTOR_SIZE * (DIRECT_BLKS
               + INDIRECT_BLKS * INDIRECT_BLK_PTRS))
        {
          pos -= BLOCK_SECTOR_SIZE * DIRECT_BLKS;
          idx = pos / (BLOCK_SECTOR_SIZE * INDIRECT_BLK_PTRS) + DIRECT_BLKS;
          read_block (inode->ptr[idx], block);
          pos %= BLOCK_SECTOR_SIZE * INDIRECT_BLK_PTRS;
          sector = block[pos / BLOCK_SECTOR_SIZE];
        }
      else
        {
          read_block (inode->ptr[DOUBLE_INDIRECT_IDX], block);
          pos -= BLOCK_SECTOR_SIZE * (DIRECT_BLKS
                 + INDIRECT_BLKS * INDIRECT_BLK_PTRS);
          idx = pos / (BLOCK_SECTOR_SIZE * INDIRECT_BLK_PTRS);
          read_block (block[idx], block);
          pos %= BLOCK_SECTOR_SIZE * INDIRECT_BLK_PTRS;
          sector = block[pos / BLOCK_SECTOR_SIZE];
        }
      free (block);
      return sector;
    }
  else
    return -1;
}

/* List of open inodes, so that opening a single inode twice
   returns the same `struct inode'. */
static struct list open_inodes;
static struct lock inode_list_lock;

/* Initializes the inode module. */
void
inode_init (void) 
{
  lock_init (&inode_list_lock);
  list_init (&open_inodes);
}

struct buffer *cache_get_buffer (block_sector_t sector, bool zero);
void cache_release_buffer (struct buffer *buffer);

/* Initializes an inode with LENGTH bytes of data and
   writes the new inode to sector SECTOR on the file system
   device.
   Returns true if successful.
   Returns false if memory or disk allocation fails. */
bool
inode_create (block_sector_t sector, bool is_dir, off_t length)
{
  struct inode_disk *disk_inode;
  bool success = false;

  ASSERT (length >= 0);

  /* If this assertion fails, the inode structure is not exactly
     one sector in size, and you should fix that. */
  ASSERT (sizeof *disk_inode == BLOCK_SECTOR_SIZE);

  /* Create the inode. */
  struct buffer *buffer = cache_get_buffer (sector, true);
  disk_inode = (struct inode_disk *) buffer->data;
  disk_inode->is_dir = is_dir;
  disk_inode->length = length;
  disk_inode->magic = INODE_MAGIC;
  success = allocate_inode (disk_inode);
  buffer->flags |= BUFFER_DIRTY;
  cache_release_buffer (buffer);

  return success;
}

/* Reads an inode from SECTOR
   and returns a `struct inode' that contains it.
   Returns a null pointer if memory allocation fails. */
struct inode *
inode_open (block_sector_t sector)
{
  struct list_elem *e;
  struct inode *inode;

  lock_acquire (&inode_list_lock);

  /* Check whether this inode is already open. */
  for (e = list_begin (&open_inodes); e != list_end (&open_inodes);
       e = list_next (e)) 
    {
      inode = list_entry (e, struct inode, elem);
      if (inode->sector == sector) 
        {
          inode_reopen (inode);
          lock_release (&inode_list_lock);
          return inode; 
        }
    }

  /* Allocate memory. */
  inode = malloc (sizeof *inode);
  if (inode == NULL)
    {
      lock_release (&inode_list_lock);
      return NULL;
    }

  /* Initialize. */
  list_push_front (&open_inodes, &inode->elem);
  inode->sector = sector;
  inode->open_cnt = 1;
  inode->deny_write_cnt = 0;
  inode->removed = false;
  lock_init (&inode->lock);

  /* Retrieve the inode from disk. */
  struct buffer *buffer = cache_get_buffer (sector, false);
  struct inode_disk *data = (struct inode_disk *) buffer->data; 
  inode->length = data->length;
  inode->direct_idx = data->direct_idx;
  inode->indirect_idx = data->indirect_idx;
  inode->double_indirect_idx = data->double_indirect_idx;
  inode->is_dir = data->is_dir;
  memcpy (&inode->ptr, &data->ptr, INODE_BLK_PTRS * sizeof (block_sector_t));
  cache_release_buffer (buffer);

  lock_release (&inode_list_lock);
  return inode;
}

/* Reopens and returns INODE. */
struct inode *
inode_reopen (struct inode *inode)
{
  if (inode != NULL)
    inode->open_cnt++;
  return inode;
}

/* Returns INODE's inode number. */
block_sector_t
inode_get_inumber (const struct inode *inode)
{
  return inode->sector;
}

/* Closes INODE and writes it to disk.
   If this was the last reference to INODE, frees its memory.
   If INODE was also a removed inode, frees its blocks. */
void
inode_close (struct inode *inode) 
{
  /* Ignore null pointer. */
  if (inode == NULL)
    return;

  lock_acquire (&inode_list_lock);

  /* Release resources if this was the last opener. */
  if (--inode->open_cnt == 0)
    {
      /* Remove from inode list and release lock. */
      list_remove (&inode->elem);

      /* Deallocate blocks if removed. */
      if (inode->removed) 
        {
          free_map_release (inode->sector, 1);
          deallocate_inode (inode);
        }

      /* Else flush the inode. */
      else
        {
          struct buffer *buffer = cache_get_buffer (inode->sector, true);
          struct inode_disk *disk_inode = (struct inode_disk *) buffer->data;
          disk_inode->length = inode->length;
          disk_inode->magic = INODE_MAGIC;
          disk_inode->is_dir = inode->is_dir;
          disk_inode->direct_idx = inode->direct_idx;
          disk_inode->indirect_idx = inode->indirect_idx;
          disk_inode->double_indirect_idx = inode->double_indirect_idx;
          memcpy (&disk_inode->ptr, &inode->ptr,
                  INODE_BLK_PTRS * sizeof (block_sector_t));
          buffer->flags |= BUFFER_DIRTY;
          cache_release_buffer (buffer);
        }
      free (inode); 
    }

  lock_release (&inode_list_lock);
}


/* Marks INODE to be deleted when it is closed by the last caller who
   has it open. */
void
inode_remove (struct inode *inode) 
{
  ASSERT (inode != NULL);
  inode->removed = true;
}

/* Reads SIZE bytes from INODE into BUFFER, starting at position OFFSET.
   Returns the number of bytes actually read, which may be less
   than SIZE if an error occurs or end of file is reached. */
off_t
inode_read_at (struct inode *inode, void *buffer_, off_t size, off_t offset) 
{
  uint8_t *buffer = buffer_;
  off_t bytes_read = 0;

  off_t length = inode->length;
  if (offset >= length)
    return 0;

  while (size > 0) 
    {
      /* Disk sector to read, starting byte offset within sector. */
      block_sector_t sector_idx = byte_to_sector (inode, length, offset);
      int sector_ofs = offset % BLOCK_SECTOR_SIZE;

      /* Bytes left in inode, bytes left in sector, lesser of the two. */
      off_t inode_left = length - offset;
      int sector_left = BLOCK_SECTOR_SIZE - sector_ofs;
      int min_left = inode_left < sector_left ? inode_left : sector_left;

      /* Number of bytes to actually copy out of this sector. */
      int chunk_size = size < min_left ? size : min_left;
      if (chunk_size <= 0)
        break;

      /* Signal for a read ahead. */
      if (sector_idx + 1 < block_size (fs_device))
        cache_read_ahead (sector_idx + 1);

      struct buffer *cache_buf = cache_get_buffer (sector_idx, false);
      memcpy (buffer + bytes_read, cache_buf->data + sector_ofs, chunk_size);
      cache_release_buffer (cache_buf);

      /* Advance. */
      size -= chunk_size;
      offset += chunk_size;
      bytes_read += chunk_size;
    }

  return bytes_read;
}

/* Writes SIZE bytes from BUFFER into INODE, starting at OFFSET.
   Returns the number of bytes actually written, which may be
   less than SIZE if end of file is reached or an error occurs.
   (Normally a write at end of file would extend the inode, but
   growth is not yet implemented.) */
off_t
inode_write_at (struct inode *inode, const void *buffer_, off_t size,
                off_t offset) 
{
  const uint8_t *buffer = buffer_;
  off_t length;
  off_t bytes_written = 0;

  if (inode->deny_write_cnt > 0)
    return 0;

  /* Check for growth and acquire lock. */
  bool grow = offset + size > inode->length;
  if (grow)
    {
      if (!inode_is_dir (inode))
        lock_acquire (&inode->lock);
      length = inode_expand (inode, offset + size);
    }
  else
    length = inode->length;

  while (size > 0) 
    {
      /* Sector to write, starting byte offset within sector. */
      block_sector_t sector_idx = byte_to_sector (inode, length, offset);
      int sector_ofs = offset % BLOCK_SECTOR_SIZE;

      /* Bytes left in inode, bytes left in sector, lesser of the two. */
      off_t inode_left = length - offset;
      int sector_left = BLOCK_SECTOR_SIZE - sector_ofs;
      int min_left = inode_left < sector_left ? inode_left : sector_left;

      /* Number of bytes to actually write into this sector. */
      int chunk_size = size < min_left ? size : min_left;
      if (chunk_size <= 0)
        break;

      /* Obtain a cache buffer and write the caller's buffer to it. */
      bool zero = !(sector_ofs > 0 || chunk_size < sector_left);
      struct buffer *cache_buf = cache_get_buffer(sector_idx, zero);
      memcpy (cache_buf->data + sector_ofs, buffer + bytes_written, chunk_size);
      cache_buf->flags |= BUFFER_DIRTY;
      cache_release_buffer (cache_buf);

      /* Advance. */
      size -= chunk_size;
      offset += chunk_size;
      bytes_written += chunk_size;
    }

  /* Update inode length if growth and release lock. */
  if (grow)
    {
      inode->length = length;
      if (!inode_is_dir (inode))
        lock_release (&inode->lock);
    }

  return bytes_written;
}

/* Obtain a buffer in the cache for IO. */
struct buffer *
cache_get_buffer (block_sector_t sector, bool zero)
{
  /* Check if the sector is already in a buffer. */
  struct buffer *cache_buf, *best_buf = NULL;
  int i;
  lock_acquire (&cache.lock);
  for (i = 0; i < CACHE_SIZE; i++)
    {
      cache_buf = &cache.entries[i];
      lock_acquire (&cache_buf->state);
      if (cache_buf->sector == sector)
        {
          best_buf = cache_buf;
          break;
        }
      else
        lock_release (&cache_buf->state);
    }

  /* Select a buffer to use if not already in cache. */
  bool evict = best_buf == NULL;
  if (evict)
    {
      unsigned start = cache.clock, best_cost = BUFFER_PIN;
      bool found = false;
      do
        {
          cache_buf = &cache.entries[cache.clock];
          lock_acquire (&cache_buf->state);

          /* If best so far update and check if done. */
          if (cache_buf->flags < best_cost)
            {
              if (best_buf != NULL)
                lock_release (&best_buf->state);
              best_buf = cache_buf;
              best_cost = cache_buf->flags;
              found = !(cache_buf->flags & BUFFER_ACCESSED);
            }

          /* Else mark the buffer as not accessed. */
          else
            {
              cache_buf->flags &= ~BUFFER_ACCESSED;
              lock_release (&cache_buf->state);
            }

          cache.clock = (cache.clock + 1) % CACHE_SIZE;
        }
      while (!found && cache.clock != start || best_buf == NULL);
    }

  /* Update the chosen buffer's sector. */
  block_sector_t old_sector = best_buf->sector;
  best_buf->sector = sector;
  lock_release (&cache.lock);

  /* Update the sector and pinned flag. */
  best_buf->flags += BUFFER_PIN;
  best_buf->flags |= BUFFER_ACCESSED;
  lock_release (&best_buf->state);
  lock_acquire (&best_buf->io);
  thread_current ()->buffer_io = &best_buf->io;

  /* Evict the current sector if necessary. */
  if (evict)
    {
      if (best_buf->flags & BUFFER_DIRTY)
        {
          block_write (fs_device, old_sector, best_buf->data);
          best_buf->flags &= ~BUFFER_DIRTY;
        }
      if (zero)
        memset (best_buf->data, 0, BLOCK_SECTOR_SIZE);
      else
        block_read (fs_device, sector, best_buf->data);
    }

  /* Return the cache buffer selected. */
  return best_buf;
}

/* Unpin a buffer so it can be evicted. */
void
cache_release_buffer (struct buffer *buffer)
{
  thread_current ()->buffer_io = NULL;
  lock_release (&buffer->io);
  lock_acquire (&buffer->state);
  buffer->flags -= BUFFER_PIN;
  lock_release (&buffer->state);
}

/* Flush all dirty cache buffers to disk. */
void
cache_flush (void)
{
  int i;
  bool pinned;
  struct buffer *buffer;
  for (i = 0; i < CACHE_SIZE; i++)
    {
      buffer = &cache.entries[i];

      /* Acquire the buffer. */
      lock_acquire (&buffer->state);
      buffer->flags += BUFFER_PIN;
      lock_release (&buffer->state);
      lock_acquire (&buffer->io);

      /* Write the data to disk if dirty. */
      if (buffer->flags & BUFFER_DIRTY)
        {
          block_write (fs_device, buffer->sector, buffer->data);
          buffer->flags &= ~BUFFER_DIRTY;
        }
      
      /* Release the buffer. */
      lock_release (&buffer->io);
      lock_acquire (&buffer->state);
      buffer->flags -= BUFFER_PIN;
      lock_release (&buffer->state);
    }
}

/* Rate at which to flush buffer in ticks. */
#define FLUSH_RATE 1024

/* Worker to periodically flusher buffer. */
void
cache_flush_worker (void)
{
  for (;;)
    {
      timer_sleep (FLUSH_RATE);
      cache_flush ();
    }
}

/* Read a sector into the cache asynchronously. */
void
cache_read_ahead (block_sector_t sector)
{
  struct read_ahead *read_ahead;
  read_ahead = malloc (sizeof (struct read_ahead));
  if (read_ahead == NULL)
    return;
  read_ahead->sector = sector;
  lock_acquire (&read_aheads.lock);
  list_push_front (&read_aheads.list, &read_ahead->elem);
  lock_release (&read_aheads.lock);
  sema_up (&read_aheads.sema);
}

/* Worker for asynchronous read aheads. */
void
cache_read_ahead_worker (void)
{
  struct list_elem *e;
  struct read_ahead *read_ahead;
  struct buffer *buffer;
  for (;;)
    {
      sema_down (&read_aheads.sema);
      lock_acquire (&read_aheads.lock);
      e = list_pop_back (&read_aheads.list);
      lock_release (&read_aheads.lock);
      read_ahead = list_entry (e, struct read_ahead, elem);
      buffer = cache_get_buffer (read_ahead->sector, false);
      cache_release_buffer (buffer);
      free (read_ahead);
    }
}

/* Disables writes to INODE.
   May be called at most once per inode opener. */
void
inode_deny_write (struct inode *inode) 
{
  inode->deny_write_cnt++;
  ASSERT (inode->deny_write_cnt <= inode->open_cnt);
}

/* Re-enables writes to INODE.
   Must be called once by each inode opener who has called
   inode_deny_write() on the inode, before closing the inode. */
void
inode_allow_write (struct inode *inode) 
{
  ASSERT (inode->deny_write_cnt > 0);
  ASSERT (inode->deny_write_cnt <= inode->open_cnt);
  inode->deny_write_cnt--;
}

/* Returns the length, in bytes, of INODE's data. */
off_t
inode_length (const struct inode *inode)
{
  return inode->length;
}

/* Returns open count of inode. */
int inode_get_open_cnt (const struct inode *inode)
{
  return inode->open_cnt;
}

/* Allocate an inode. */
bool allocate_inode (struct inode_disk *disk_inode) {
  struct inode inode;
  inode.length = 0;
  inode.direct_idx = 0;
  inode.indirect_idx = 0;
  inode.double_indirect_idx = 0;
  
  inode_expand (&inode, disk_inode->length);
  disk_inode->direct_idx = inode.direct_idx;
  disk_inode->indirect_idx = inode.indirect_idx;
  disk_inode->double_indirect_idx = inode.double_indirect_idx;
  memcpy (&disk_inode->ptr, &inode.ptr,
          INODE_BLK_PTRS * sizeof(block_sector_t));
  return true;
}

/* Deallocate an inode. */
void
deallocate_inode (struct inode *inode)
{
  size_t data_sectors = bytes_to_data_sectors (inode->length);
  size_t indirect_sectors = bytes_to_indirect_sectors (inode->length);
  size_t double_indirect_sector = bytes_to_double_indirect_sector (inode->length);
  unsigned int idx = 0;

  while (data_sectors && idx < INDIRECT_IDX)
    {
      free_map_release (inode->ptr[idx], 1);
      data_sectors--;
      idx++;
    }

  while (indirect_sectors && idx < DOUBLE_INDIRECT_IDX)
    {
      size_t data_ptrs = data_sectors < INDIRECT_BLK_PTRS
                         ? data_sectors : INDIRECT_BLK_PTRS;
      deallocate_indirect (&inode->ptr[idx], data_ptrs);
      data_sectors -= data_ptrs;
      indirect_sectors--;
      idx++;
    }

  if (double_indirect_sector)
    deallocate_double_indirect (&inode->ptr[idx], indirect_sectors,
                                data_sectors);
}

/* Deallocate a double indirect block. */
void
deallocate_double_indirect (block_sector_t *ptr, size_t indirect_ptrs,
                            size_t data_ptrs)
{
  unsigned int i;
  block_sector_t *block;
  block = malloc (sizeof (block_sector_t) * INDIRECT_BLK_PTRS);

  read_block (*ptr, block);
  for (i = 0; i < indirect_ptrs; i++)
    {
      size_t data_per_block = data_ptrs < INDIRECT_BLK_PTRS ? data_ptrs
                              : INDIRECT_BLK_PTRS;
      deallocate_indirect (&block[i], data_per_block);
      data_ptrs -= data_per_block;
    }
  free_map_release(*ptr, 1);
  free (block);
}

/* Deallocate an indirect block. */
void
deallocate_indirect (block_sector_t *ptr, size_t data_ptrs)
{
  unsigned int i;
  block_sector_t *block;
  block = malloc (sizeof (block_sector_t) * INDIRECT_BLK_PTRS);

  read_block (*ptr, block);
  for (i = 0; i < data_ptrs; i++)
    free_map_release(block[i], 1);
  free_map_release(*ptr, 1);
  free (block);
}

/* Expands the size of an inode. */
off_t
inode_expand (struct inode *inode, off_t new_length)
{
  size_t new_sectors = bytes_to_data_sectors (new_length)
                       - bytes_to_data_sectors (inode->length);
  if (new_sectors == 0)
    goto done;

  /* Expand to direct indices while available. */
  while (inode->direct_idx < INDIRECT_IDX)
    {
      free_map_allocate (1, &inode->ptr[inode->direct_idx]);
      zero_block (inode->ptr[inode->direct_idx]);
      inode->direct_idx++;
      new_sectors--;
      if (new_sectors == 0)
        goto done;
    }

  /* Expand to indirect indices while available. */
  while (inode->direct_idx < DOUBLE_INDIRECT_IDX)
    {
      new_sectors = expand_indirect (inode, new_sectors);
      if (new_sectors == 0)
        goto done;
    }

  /* Example to double indirect index if necessary. */
  if (inode->direct_idx == DOUBLE_INDIRECT_IDX)
    new_sectors = expand_double_indirect (inode, new_sectors);

done:
  /* Return the expanded size. */
  return new_length - new_sectors * BLOCK_SECTOR_SIZE;
}

/* Example inode into indirect indices. */
static size_t
expand_indirect (struct inode *inode, size_t new_sectors)
{
  block_sector_t *block;
  block = malloc (sizeof (block_sector_t) * INDIRECT_BLK_PTRS);
  if (block == NULL)
    return 0;

  /* Pick an inode to use. */
  if (inode->indirect_idx == 0)
    free_map_allocate (1, &inode->ptr[inode->direct_idx]);
  else
    read_block (inode->ptr[inode->direct_idx], block);

  /* Add the new sectors. */
  while (inode->indirect_idx < INDIRECT_BLK_PTRS)
    {
      free_map_allocate (1, &block[inode->indirect_idx]);
      zero_block (block[inode->indirect_idx]);
      inode->indirect_idx++;
      new_sectors--;
      if (new_sectors == 0)
        break;
    }

  /* Write and return. */
  write_block (inode->ptr[inode->direct_idx], block);
  if (inode->indirect_idx == INDIRECT_BLK_PTRS)
    {
      inode->indirect_idx = 0;
      inode->direct_idx++;
    }
  free (block);
  return new_sectors;
}

/* Expand an inode into double indirect indices. */
static size_t
expand_double_indirect (struct inode *inode, size_t new_sectors)
{
  block_sector_t *block;
  block = malloc (sizeof (block_sector_t) * INDIRECT_BLK_PTRS);
  if (block == NULL)
    return 0;

  /* Select a block. */
  if (inode->double_indirect_idx == 0 && inode->indirect_idx == 0)
    free_map_allocate (1, &inode->ptr[inode->direct_idx]);
  else
    read_block (inode->ptr[inode->direct_idx], block);

  /* Get the new sectors in the block. */
  while (inode->indirect_idx < INDIRECT_BLK_PTRS)
    {
      new_sectors = expand_double_indirect_inner (inode, new_sectors, block);
      if (new_sectors == 0)
        break;
    }

  /* Write the block and return. */
  write_block (inode->ptr[inode->direct_idx], block);
  free (block);
  return new_sectors;
}

/* Expand inner level of a double indirect reference. */
size_t
expand_double_indirect_inner (struct inode *inode, size_t new_sectors,
                              block_sector_t *outer_block)
{
  block_sector_t *inner_block;
  inner_block = malloc (sizeof (block_sector_t) * INDIRECT_BLK_PTRS);
  if (inner_block == NULL)
    return 0;

  /* Pick block to use. */
  if (inode->double_indirect_idx == 0)
    free_map_allocate (1, &outer_block[inode->indirect_idx]);
  else
    read_block (outer_block[inode->indirect_idx], inner_block);

  /* Add new sectors. */
  while (inode->double_indirect_idx < INDIRECT_BLK_PTRS)
    {
      free_map_allocate (1, &inner_block[inode->double_indirect_idx]);
      zero_block (inner_block[inode->double_indirect_idx]);
      inode->double_indirect_idx++;
      new_sectors--;
      if (new_sectors == 0)
        break;
    }

  /* Write out the results. */
  write_block (outer_block[inode->indirect_idx], inner_block);
  if (inode->double_indirect_idx == INDIRECT_BLK_PTRS)
    {
      inode->double_indirect_idx = 0;
      inode->indirect_idx++;
    }

  free (inner_block);
  return new_sectors;
}

/* Acquire a lock on an inode */
void
inode_lock (struct inode *inode)
{
  lock_acquire (&inode->lock);
}

/* Release a lock on an inode. */
void
inode_unlock (struct inode *inode)
{
  lock_release (&inode->lock);
}

/* Return whether an inode is a directory. */
bool
inode_is_dir (const struct inode *inode)
{
  return inode->is_dir;
}

/* Read a block with caching. */
static void
read_block (block_sector_t sector, void *buffer)
{
  struct buffer *cache_buf = cache_get_buffer (sector, false);
  memcpy (buffer, cache_buf->data, BLOCK_SECTOR_SIZE);
  cache_release_buffer (cache_buf);
}

/* Write to a block with caching. */
static void
write_block (block_sector_t sector, void *buffer)
{
  struct buffer *cache_buf = cache_get_buffer (sector, true);
  memcpy (cache_buf->data, buffer, BLOCK_SECTOR_SIZE);
  cache_buf->flags |= BUFFER_DIRTY;
  cache_release_buffer (cache_buf);
}

/* Zer a block with caching. */
static void
zero_block (block_sector_t sector)
{
  struct buffer *cache_buf = cache_get_buffer (sector, true);
  memset (cache_buf->data, 0, BLOCK_SECTOR_SIZE);
  cache_buf->flags |= BUFFER_DIRTY;
  cache_release_buffer (cache_buf);
}
