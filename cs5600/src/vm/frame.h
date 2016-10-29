#ifndef VM_FRAME_H
#define VM_FRAME_H

#include "vm/pagetable.h"

void frame_init (void);
void frame_set_page (struct page *pg, void* upage);
void frame_lock (void);
void frame_unlock (void);

#endif /* vm/frame.h */
