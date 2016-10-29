#include "vm/swap.h"
#include "devices/block.h"
#include "devices/block.h"
#include "threads/synch.h"
#include "threads/vaddr.h"
#include <bitmap.h>
#include <stdio.h>

/* Definitions for swap. */
#define SWAP_FREE 0
#define SWAP_USED 1
#define SECTORS_PER_PAGE (PGSIZE / BLOCK_SECTOR_SIZE)
#define SLOT_SIZE 1024 * 4

/* Data structure for swap table. */
struct swap_table
  {
    struct lock lock;        /* Lock for accessing swap. */
    struct block *block;     /* Block device for swap. */
    struct bitmap *used_map; /* Map of used swap slots. */
  };

/* The swap table. */
static struct swap_table swap_table;

/* Initialize swapping. */
void swap_init (void)
{
  swap_table.block = block_get_role (BLOCK_SWAP);
  if (swap_table.block == NULL)
    PANIC ("Unable to obtain swap block!");
  size_t swap_size = block_size (swap_table.block)
                     * BLOCK_SECTOR_SIZE / PGSIZE;
  swap_table.used_map = bitmap_create (swap_size);
  if (swap_table.used_map == NULL)
    PANIC ("Unable to create swap map!");
  bitmap_set_all (swap_table.used_map, SWAP_FREE);
  lock_init (&swap_table.lock);
}

/* Swap a page of data to disk. */
int
swap_to_disk (void *page)
{
  /* Acquire a swap slot. */
  int idx = bitmap_scan_and_flip (swap_table.used_map, 0, 1, SWAP_FREE);
  if (idx == BITMAP_ERROR)
    PANIC ("No free swap slots available!");

  /* Write the page out to swap on disk. */
  int i;
  for (i = 0; i < SECTORS_PER_PAGE; i++)
    block_write (swap_table.block, idx * SECTORS_PER_PAGE + i,
                 (uint8_t *) page + i * BLOCK_SECTOR_SIZE);

  /* Return the swap index used. */
  return idx;
}

/* Swap a page back into memory. */
void
swap_to_memory (int idx, void *page)
{
  //ASSERT (bitmap_test (swap_table.used_map, idx) == SWAP_USED);

  /* Write the page back into memory. */
  int i;
  for (i = 0; i < SECTORS_PER_PAGE; i++)
    block_read (swap_table.block, idx * SECTORS_PER_PAGE + i,
                (uint8_t *) page + i * BLOCK_SECTOR_SIZE);

  /* Free the swap slot. */
  bitmap_flip (swap_table.used_map, idx);
}

/* Free a swap slot. */
void
swap_free (int idx)
{
  bitmap_set (swap_table.used_map, idx, false);
}

/* Lock access to swap. */
void
swap_lock (void)
{
  lock_acquire (&swap_table.lock);
}

/* Unlock access to swap. */
void
swap_unlock (void)
{
  lock_release (&swap_table.lock);
}
