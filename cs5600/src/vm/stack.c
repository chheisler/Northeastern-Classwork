#include "vm/stack.h"
#include "threads/thread.h"
#include "threads/synch.h"

/* Limits on stack growth. */
#define STACK_MIN_VA (PHYS_BASE - 1024 * 1024 * 8)
#define STACK_MAX_DIFF 0x20

/* Returns whether access to address should grow stack. */
bool
stack_is_growth (void *va, void *esp)
{
  return is_user_vaddr (va)
         && esp >= STACK_MIN_VA
         && (uint8_t *) va + STACK_MAX_DIFF >= esp;
}

/* Creates a new page to place into the stack. */
struct page *
stack_page (void)
{
  struct page *pg = malloc (sizeof (struct page));
  if (pg == NULL)
    PANIC ("Unable to grow stack!");
  pg->flags = PAGE_ZERO;
  pg->flags |= PAGE_WRITE_BIT;
  return pg;
}
