#ifndef FILESYS_INODE_H
#define FILESYS_INODE_H

#include <stdbool.h>
#include "filesys/off_t.h"
#include "devices/block.h"

struct bitmap;

void inode_init (void);
bool inode_create (block_sector_t, bool, off_t);
struct inode *inode_open (block_sector_t);
struct inode *inode_reopen (struct inode *);
block_sector_t inode_get_inumber (const struct inode *);
void inode_close (struct inode *);
void inode_remove (struct inode *);
off_t inode_read_at (struct inode *, void *, off_t size, off_t offset);
off_t inode_write_at (struct inode *, const void *, off_t size, off_t offset);
void inode_deny_write (struct inode *);
void inode_allow_write (struct inode *);
off_t inode_length (const struct inode *);
int inode_get_open_cnt (const struct inode *inode);
block_sector_t inode_parent (const struct inode *);
bool inode_is_dir (const struct inode *);
off_t expand_inode (struct inode *inode, off_t new_length);
size_t expand_inode_indirect_block (struct inode *inode,
            size_t new_data_sectors);
size_t expand_inode_double_indirect_block (struct inode *inode,
             size_t new_data_sectors);
void dealloc_inode (struct inode *inode);
void dealloc_inode_indirect_block (block_sector_t *ptr, size_t data_ptrs);
void dealloc_inode_double_indirect_block (block_sector_t *ptr,
            size_t indirect_ptrs,
            size_t data_ptrs);
void inode_lock (struct inode *inode);
void inode_unlock (struct inode *inode);
void cache_init (void);
void cache_flush (void);
off_t inode_expand (struct inode *, off_t);

#endif /* filesys/inode.h */
