#ifndef VM_SWAP_H
#define VM_SWAP_H

#include <stdbool.h>

void swap_init (void);
int swap_to_disk (void *page);
void swap_to_memory (int idx, void *page);
void swap_free (int idx);
void swap_lock (void);
void swap_unlock (void);

#endif /* vm/swap.h */
