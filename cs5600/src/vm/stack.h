#ifndef VM_STACK H
#define VM_STACK_H

#include <stdbool.h>
#include "threads/vaddr.h"
#include "vm/pagetable.h"

/* Functions for growing the stack. */
bool stack_is_growth (void *va, void *esp);
struct page *stack_page (void);

#endif /* vm/stack.h */
