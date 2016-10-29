#ifndef VM_PAGETABLE_H
#define VM_PAGETABLE_H

#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>
#include "threads/vaddr.h"
#include "threads/synch.h"
#include "filesys/file.h"

/* Type definition for a supplementary page table node. */
typedef uint32_t *pt_node_t;

/* Struct for supplemental page table entries. */
struct page
  {
    uint32_t flags;   /* Flags for the page. */
    uint32_t data;    /* Where to locate the data for the page. */
  };

/* Page flags masks and values. */
#define PAGE_TYPE_BITS 3
#define PAGE_WRITE_BIT 4
#define PAGE_ZERO 0
#define PAGE_SWAP 1
#define PAGE_EXEC 2
#define PAGE_MMAP 3
/* Entry in the supplementary page table for data in a file. */
struct file_page
  {
    struct file *file; /* Open file handle to the file. */
    size_t offset;     /* The offset within the file.  */
    size_t size;       /* The size of the data in the file. */
  };

/* Supplementary page table functions. */
void pagetable_set_page (pt_node_t *pt, struct page *pg, void *va);
struct page *pagetable_get_page (pt_node_t pt, void *va);
void pagetable_destroy (uint32_t *pt);
void pagetable_clear (pt_node_t *pt, void *va, size_t size);

#endif /* vm/pagetable.h */
