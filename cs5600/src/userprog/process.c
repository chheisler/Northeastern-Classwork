#include "userprog/process.h"
#include <debug.h>
#include <inttypes.h>
#include <round.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "userprog/gdt.h"
#include "userprog/pagedir.h"
#include "userprog/tss.h"
#include "filesys/directory.h"
#include "filesys/file.h"
#include "filesys/filesys.h"
#include "threads/flags.h"
#include "threads/init.h"
#include "threads/interrupt.h"
#include "threads/palloc.h"
#include "threads/thread.h"
#include "threads/vaddr.h"
#include "threads/synch.h"
#include "vm/pagetable.h"
#include "vm/frame.h"

const uint8_t *USTACK_VADDR = (uint8_t *) PHYS_BASE - PGSIZE;
static thread_func start_process NO_RETURN;
static bool load (struct args_page *args, void (**eip) (void), void **esp);
static pid_t allocate_pid (void);
static void tokenize_args (struct args_page *args);
extern struct lock filesys_lock;

/* Starts a new thread running a user program loaded from
   FILENAME.  The new thread may be scheduled (and may even exit)
   before process_execute() returns.  Returns the new process's
   thread id, or TID_ERROR if the thread cannot be created. */
tid_t
process_execute (const char *args) 
{
  struct args_page *args_pg;
  tid_t tid = TID_ERROR;
  struct process *child;

  /* Make a copy of the arguments.
     Otherwise there's a race between the caller and load(). */
  args_pg = palloc_get_page (0);
  if (args_pg == NULL)
    return TID_ERROR;
  strlcpy (args_pg->args, args, ARGS_SIZE);

  /* Tokenize arguments. */
  tokenize_args (args_pg);
  if (args_pg->argc == BAD_ARGS)
    {
      palloc_free_page (args_pg);
      return TID_ERROR;
    }

  /* Create a new thread to execute FILE_NAME. */
  tid = thread_create (args_pg->argv[0], PRI_DEFAULT, start_process, args_pg);

  /* If a thread was created wait for process to begin or fail. */
  if (tid != TID_ERROR)
    {
      child = process_child ((pid_t) tid);
      sema_down (&child->sema);
      if (child->status == PROCESS_FAIL)
        {
          list_remove (&child->elem);
          free (child);
          return TID_ERROR;
        }
    }
  return tid;
}

/* A thread function that loads a user process and starts it
   running. */
static void
start_process (void *args_)
{
  struct args_page *args = (struct args_page *) args_;
  struct intr_frame if_;
  bool success = false;
  struct process *p;

  /* Initialize interrupt frame and load executable. */
  memset (&if_, 0, sizeof if_);
  if_.gs = if_.fs = if_.es = if_.ds = if_.ss = SEL_UDSEG;
  if_.cs = SEL_UCSEG;
  if_.eflags = FLAG_IF | FLAG_MBS;
  success = load (args, &if_.eip, &if_.esp);

done:
  /* If successful signal waiting parent, else quit. */
  palloc_free_page (args);
  p = thread_current ()->proc;
  if (success)
    sema_up (&p->sema);
  else
    {
      p->status = PROCESS_FAIL;
      thread_exit ();
    }

  /* Start the user process by simulating a return from an
     interrupt, implemented by intr_exit (in
     threads/intr-stubs.S).  Because intr_exit takes all of its
     arguments on the stack in the form of a `struct intr_frame',
     we just point the stack pointer (%esp) to our stack frame
     and jump to it. */
  asm volatile ("movl %0, %%esp; jmp intr_exit" : : "g" (&if_) : "memory");
  NOT_REACHED ();
}

/* Waits for thread TID to die and returns its exit status.  If
   it was terminated by the kernel (i.e. killed due to an
   exception), returns -1.  If TID is invalid or if it was not a
   child of the calling process, or if process_wait() has already
   been successfully called for the given TID, returns -1
   immediately, without waiting.

   This function will be implemented in problem 2-2.  For now, it
   does nothing. */
int
process_wait (tid_t child_tid) 
{
  pid_t pid = (pid_t) child_tid;
  struct process *child;
  int exit;

  /* Find child process with matching PID. */
  child = process_child (pid);

  /* Return -1 immediately if no such child exists. */
  if (child == NULL)
    return BAD_WAIT;

  /* Wait for process to exit and return value. */
  sema_down (&child->sema);
  exit = child->exit;
  list_remove (&child->elem);
  free (child);
  return exit;
}

/* Free the current process's resources and signal its parent if it exists. */
void
process_exit (void)
{
  struct thread *cur = thread_current ();
  struct process *p;
  struct process *child;
  struct fhandle *fh;
  struct map *map;
  struct list_elem *e;
  uint32_t *pd;
  int exit;

  /* Free cache buffer if we have one. */
  if (cur->buffer_io != NULL)
    lock_release (cur->buffer_io);

  /* Close our working directory. */
  dir_close (cur->dir);

  /* Remove our open file handles. */
  while (!list_empty (&cur->files))
    {
      e = list_pop_front (&cur->files);
      fh = list_entry (e, struct fhandle, elem);
      file_close (fh->file);
      free (fh);
    }

  /* Remove our open memory mapped files. */
  while (!list_empty (&cur->maps))
    {
      e = list_pop_front (&cur->maps);
      map = list_entry (e, struct map, elem);
      flush_map (map);
      file_close (map->file);
      free (map);
    }

  frame_lock ();
  
  /* Destroy the process's supplementary page table. */
  pagetable_destroy (cur->pagetable);

  /* Destroy the current process's page directory and switch back
     to the kernel-only page directory. */
  pd = cur->pagedir;
  if (pd != NULL) 
    {
      /* Correct ordering here is crucial.  We must set
         cur->pagedir to NULL before switching page directories,
         so that a timer interrupt can't switch back to the
         process page directory.  We must activate the base page
         directory before destroying the process's page
         directory, or our active page directory will be one
         that's been freed (and cleared). */
      cur->pagedir = NULL;
      pagedir_activate (NULL);
      pagedir_destroy (pd);
    }

  frame_unlock ();

  /* Let the children of the process that they're now orphaned so they
     will clean up when they exit. */
  for (e = list_begin (&cur->children);
       e != list_end (&cur->children);
       e = list_next (e))
    {
      child = list_entry (e, struct process, elem);
      lock_acquire (&child->status_mod);
      if (child->status == PROCESS_RUN)
        child->status = PROCESS_ORPHAN;
      else
        free (child);
      lock_release (&child->status_mod);
    }

  /* Signal that we've exited to a waiting parent if there is one else
     clean up our process information. Also print an exit message. */
  p = cur->proc;
  if (p != NULL)
    {
      exit = p->exit;
      lock_acquire (&p->status_mod);
      if (p->status == PROCESS_ORPHAN)
        {
          free (p);
          p = NULL;
        }
      else if (p->status != PROCESS_FAIL)
        p->status = PROCESS_DEAD;
      lock_release (&p->status_mod);
      if (p != NULL)
        sema_up (&p->sema);
      printf ("%s: exit(%d)\n", cur->name, exit);
    }
}

/* Sets up the CPU for running user code in the current
   thread.
   This function is called on every context switch. */
void
process_activate (void)
{
  struct thread *t = thread_current ();

  /* Activate thread's page tables. */
  pagedir_activate (t->pagedir);

  /* Set thread's kernel stack for use in processing
     interrupts. */
  tss_update ();
}

/* We load ELF binaries.  The following definitions are taken
   from the ELF specification, [ELF1], more-or-less verbatim.  */

/* ELF types.  See [ELF1] 1-2. */
typedef uint32_t Elf32_Word, Elf32_Addr, Elf32_Off;
typedef uint16_t Elf32_Half;

/* For use with ELF types in printf(). */
#define PE32Wx PRIx32   /* Print Elf32_Word in hexadecimal. */
#define PE32Ax PRIx32   /* Print Elf32_Addr in hexadecimal. */
#define PE32Ox PRIx32   /* Print Elf32_Off in hexadecimal. */
#define PE32Hx PRIx16   /* Print Elf32_Half in hexadecimal. */

/* Executable header.  See [ELF1] 1-4 to 1-8.
   This appears at the very beginning of an ELF binary. */
struct Elf32_Ehdr
  {
    unsigned char e_ident[16];
    Elf32_Half    e_type;
    Elf32_Half    e_machine;
    Elf32_Word    e_version;
    Elf32_Addr    e_entry;
    Elf32_Off     e_phoff;
    Elf32_Off     e_shoff;
    Elf32_Word    e_flags;
    Elf32_Half    e_ehsize;
    Elf32_Half    e_phentsize;
    Elf32_Half    e_phnum;
    Elf32_Half    e_shentsize;
    Elf32_Half    e_shnum;
    Elf32_Half    e_shstrndx;
  };

/* Program header.  See [ELF1] 2-2 to 2-4.
   There are e_phnum of these, starting at file offset e_phoff
   (see [ELF1] 1-6). */
struct Elf32_Phdr
  {
    Elf32_Word p_type;
    Elf32_Off  p_offset;
    Elf32_Addr p_vaddr;
    Elf32_Addr p_paddr;
    Elf32_Word p_filesz;
    Elf32_Word p_memsz;
    Elf32_Word p_flags;
    Elf32_Word p_align;
  };

/* Values for p_type.  See [ELF1] 2-3. */
#define PT_NULL    0            /* Ignore. */
#define PT_LOAD    1            /* Loadable segment. */
#define PT_DYNAMIC 2            /* Dynamic linking info. */
#define PT_INTERP  3            /* Name of dynamic loader. */
#define PT_NOTE    4            /* Auxiliary info. */
#define PT_SHLIB   5            /* Reserved. */
#define PT_PHDR    6            /* Program header table. */
#define PT_STACK   0x6474e551   /* Stack segment. */

/* Flags for p_flags.  See [ELF3] 2-3 and 2-4. */
#define PF_X 1          /* Executable. */
#define PF_W 2          /* Writable. */
#define PF_R 4          /* Readable. */

static bool setup_stack (struct args_page *args, void **esp);
static bool validate_segment (const struct Elf32_Phdr *, struct file *);
static bool load_segment (struct file *file, off_t ofs, uint8_t *upage,
                          uint32_t read_bytes, uint32_t zero_bytes,
                          bool writable);

/* Loads an ELF executable from ARGS into the current thread.
   Stores the executable's entry point into *EIP
   and its initial stack pointer into *ESP.
   Returns true if successful, false otherwise. */
bool
load (struct args_page *args, void (**eip) (void), void **esp) 
{
  struct thread *t = thread_current ();
  struct Elf32_Ehdr ehdr;
  struct file *file = NULL;
  struct fhandle *fh;
  off_t file_ofs;
  bool success = false;
  char *fn = args->argv[0];
  int i;

  /* Allocate and activate page directory. */
  t->pagedir = pagedir_create ();
  if (t->pagedir == NULL) 
    return success;
  process_activate ();

  /* Open executable file. */
  lock_acquire (&filesys_lock);
  file = filesys_open (fn);
  if (file == NULL) 
    {
      printf ("load: %s: open failed\n", fn);
      file_close (file);
      goto done;
    }
  else
    {
      file_deny_write (file);
      fh = malloc (sizeof (struct fhandle));
      if (fh == NULL)
        {
          file_close (file);
          goto done;
        }
      fh->fd = t->fd++;
      fh->file = file;
      list_push_back (&t->files, &fh->elem);
    }

  /* Read and verify executable header. */
  if (file_read (file, &ehdr, sizeof ehdr) != sizeof ehdr
      || memcmp (ehdr.e_ident, "\177ELF\1\1\1", 7)
      || ehdr.e_type != 2
      || ehdr.e_machine != 3
      || ehdr.e_version != 1
      || ehdr.e_phentsize != sizeof (struct Elf32_Phdr)
      || ehdr.e_phnum > 1024) 
    {
      printf ("load: %s: error loading executable\n", fn);
      goto done;
    }

  /* Read program headers. */
  file_ofs = ehdr.e_phoff;
  for (i = 0; i < ehdr.e_phnum; i++) 
    {
      struct Elf32_Phdr phdr;

      if (file_ofs < 0 || file_ofs > file_length (file))
        goto done;
      file_seek (file, file_ofs);

      if (file_read (file, &phdr, sizeof phdr) != sizeof phdr)
        goto done;
      file_ofs += sizeof phdr;
      switch (phdr.p_type) 
        {
        case PT_NULL:
        case PT_NOTE:
        case PT_PHDR:
        case PT_STACK:
        default:
          /* Ignore this segment. */
          break;
        case PT_DYNAMIC:
        case PT_INTERP:
        case PT_SHLIB:
          goto done;
        case PT_LOAD:
          if (validate_segment (&phdr, file)) 
            {
              bool writable = (phdr.p_flags & PF_W) != 0;
              uint32_t file_page = phdr.p_offset & ~PGMASK;
              uint32_t mem_page = phdr.p_vaddr & ~PGMASK;
              uint32_t page_offset = phdr.p_vaddr & PGMASK;
              uint32_t read_bytes, zero_bytes;
              if (phdr.p_filesz > 0)
                {
                  /* Normal segment.
                     Read initial part from disk and zero the rest. */
                  read_bytes = page_offset + phdr.p_filesz;
                  zero_bytes = (ROUND_UP (page_offset + phdr.p_memsz, PGSIZE)
                                - read_bytes);
                }
              else 
                {
                  /* Entirely zero.
                     Don't read anything from disk. */
                  read_bytes = 0;
                  zero_bytes = ROUND_UP (page_offset + phdr.p_memsz, PGSIZE);
                }
              if (!load_segment (file, file_page, (void *) mem_page,
                                 read_bytes, zero_bytes, writable))
                goto done;
            }
          else
            goto done;
          break;
        }
    }

  /* Set up stack. */
  if (!setup_stack (args, esp))
    goto done;

  /* Start address. */
  *eip = (void (*) (void)) ehdr.e_entry;

  /* If we reached here startup was successful. */
  success = true;

done:
  lock_release (&filesys_lock);
  return success;
}

/* load() helpers. */

/* Tokenizes arguments, returning argc or -1 if there was an error. */
static void
tokenize_args (struct args_page *args)
{
  char **argv = args->argv;
  int argc = 0;
  char *token, *save;

  /* Tokenize the given arguments */
  for (token = strtok_r (args->args, ARG_DELIM, &save);
       token != NULL;
       token = strtok_r (NULL, ARG_DELIM, &save))
    {
      if (argc == ARGV_SIZE)
        {
          printf("Too many arguments!\n");
          argc = BAD_ARGS;
          break;
        }
      argv[argc++] = token;
    }
  args->argc = argc;
}

/* Checks whether PHDR describes a valid, loadable segment in
   FILE and returns true if so, false otherwise. */
static bool
validate_segment (const struct Elf32_Phdr *phdr, struct file *file) 
{
  /* p_offset and p_vaddr must have the same page offset. */
  if ((phdr->p_offset & PGMASK) != (phdr->p_vaddr & PGMASK)) 
    return false; 

  /* p_offset must point within FILE. */
  if (phdr->p_offset > (Elf32_Off) file_length (file)) 
    return false;

  /* p_memsz must be at least as big as p_filesz. */
  if (phdr->p_memsz < phdr->p_filesz) 
    return false; 

  /* The segment must not be empty. */
  if (phdr->p_memsz == 0)
    return false;
  
  /* The virtual memory region must both start and end within the
     user address space range. */
  if (!is_user_vaddr ((void *) phdr->p_vaddr))
    return false;
  if (!is_user_vaddr ((void *) (phdr->p_vaddr + phdr->p_memsz)))
    return false;

  /* The region cannot "wrap around" across the kernel virtual
     address space. */
  if (phdr->p_vaddr + phdr->p_memsz < phdr->p_vaddr)
    return false;

  /* Disallow mapping page 0.
     Not only is it a bad idea to map page 0, but if we allowed
     it then user code that passed a null pointer to system calls
     could quite likely panic the kernel by way of null pointer
     assertions in memcpy(), etc. */
  if (phdr->p_vaddr < PGSIZE)
    return false;

  /* It's okay. */
  return true;
}

/* Loads a segment starting at offset OFS in FILE at address
   UPAGE.  In total, READ_BYTES + ZERO_BYTES bytes of virtual
   memory are initialized, as follows:

        - READ_BYTES bytes at UPAGE must be read from FILE
          starting at offset OFS.

        - ZERO_BYTES bytes at UPAGE + READ_BYTES must be zeroed.

   The pages initialized by this function must be writable by the
   user process if WRITABLE is true, read-only otherwise.

   Return true if successful, false if a memory allocation error
   or disk read error occurs. */
static bool
load_segment (struct file *file, off_t ofs, uint8_t *upage,
              uint32_t read_bytes, uint32_t zero_bytes, bool writable) 
{
  struct page *pg;
  
  ASSERT ((read_bytes + zero_bytes) % PGSIZE == 0);
  ASSERT (pg_ofs (upage) == 0);
  ASSERT (ofs % PGSIZE == 0);

  while (read_bytes > 0 || zero_bytes > 0) 
    {
      /* Calculate how to fill this page.
         We will read PAGE_READ_BYTES bytes from FILE
         and zero the final PAGE_ZERO_BYTES bytes. */
      size_t page_read_bytes = read_bytes < PGSIZE ? read_bytes : PGSIZE;
      size_t page_zero_bytes = PGSIZE - page_read_bytes;

      /* Add an entry to the supplementary page table. */
      pg = malloc (sizeof (struct page));
      if (pg == NULL)
        {
          return false;
        }
      if (page_zero_bytes == PGSIZE)
        {
          pg->flags = PAGE_ZERO;
          pg->data = NULL;
        }
      else
        {
          pg->flags = PAGE_EXEC;
          struct file_page *fp = malloc (sizeof (struct file_page));
          if (fp == NULL)
            return false;
          fp->file = file;
          fp->offset = ofs;
          fp->size = page_read_bytes;
          pg->data = (uintptr_t) fp;
        }
      pg->flags |= writable ? PAGE_WRITE_BIT : 0;
      pagetable_set_page (&thread_current ()->pagetable, pg, upage);

      /* Advance. */
      read_bytes -= page_read_bytes;
      zero_bytes -= page_zero_bytes;
      upage += PGSIZE;
      ofs += PGSIZE;
    }
  return true;
}

static bool stack_push_args (struct args_page *args, void **esp);

/* Create a minimal stack by mapping a zeroed page at the top of
   user virtual memory. */
static bool
setup_stack (struct args_page *args, void **esp)
{
  uint8_t *kpage;
  bool success = false;
  struct page *pg;

  pg = malloc (sizeof (struct page));
  if (pg == NULL)
    return false;
  pg->flags = PAGE_ZERO;
  pg->flags |= PAGE_WRITE_BIT;
  pg->data = NULL;
  pagetable_set_page (&thread_current ()->pagetable, pg, USTACK_VADDR);
  frame_set_page (pg, USTACK_VADDR);
  *esp = PHYS_BASE;
  success = stack_push_args (args, esp);
  if (!success)
    palloc_free_page (USTACK_VADDR);
  return success;
}

static bool stack_push_byte (uint8_t val, void **esp);
static bool stack_push_word (uint32_t val, void **esp);

/* Push arguments into the stack. */
static bool
stack_push_args (struct args_page *args, void **esp)
{
  char **argv;
  int argc, i, j;
  size_t len;

  /* Get arguments and argument count. */
  argv = args->argv;
  argc = args->argc;

  /* Place arguments into stack. */
  for (i = argc - 1; i >= 0; i--)
    {
      len = strlen (argv[i]);
      for (j = len; j >= 0; j--)
        if (!stack_push_byte ((uint8_t) argv[i][j], esp))
          return false;
      argv[i] = *esp;
    }

  /* Word align the stack. */
  for (i = (uintptr_t) *esp % sizeof (uint32_t); i > 0; i--)
    if (!stack_push_byte (NULL, esp))
      return false;
  
  /* Place pointers to arguments onto stack. */
  if (!stack_push_word (NULL, esp))
    return false;
  for (i = argc - 1; i >= 0; i--)
    if (!stack_push_word ((uint32_t) argv[i], esp))
      return false;
  argv = *esp;

  /* Place argv, argc and dummy return pointer ont stack. */
  return stack_push_word ((uint32_t) argv, esp)
         && stack_push_word ((uint32_t) argc, esp)
         && stack_push_word (NULL, esp);
}

/* Push a byte of data onto the stack. */
static bool
stack_push_byte (uint8_t val, void **esp)
{
  *esp -= sizeof(uint8_t);
  if (*esp < USTACK_VADDR)
    return false;
  *((uint8_t *) (*esp)) = val;
  return true;
}

/* Push a word of data onto the stack. */
static bool
stack_push_word (uint32_t val, void **esp)
{
  *esp -= sizeof(uint32_t);
  if (*esp < USTACK_VADDR)
    return false;
  *((uint32_t *) (*esp)) = val;
  return true;
}

/* Returns child of current thread with given PID or NULL If non exists. */
struct process *
process_child (pid_t pid)
{
  struct thread *cur;
  struct list_elem *e;
  struct process *child;

  cur = thread_current ();
  for (e = list_begin (&cur->children);
       e != list_end (&cur->children);
       e = list_next (e))
    {
      child = list_entry (e, struct process, elem);
      if (child->pid == pid)
        return child;
    }
  return NULL;
}

/* Flush a memory mapped file to disk. */
void
flush_map (struct map *map)
{
  struct thread *cur = thread_current ();
  void *upage, *kpage;
  size_t write_left = map->size, written = 0, to_write;
 
  frame_lock ();
  while (write_left > 0)
    {
      to_write = (write_left < PGSIZE) ? write_left : PGSIZE;
      upage = map->base + written;
      kpage = pagedir_get_page (cur->pagedir, upage);
      if (kpage != NULL && pagedir_is_dirty (cur->pagedir, upage))
        {
          lock_acquire (&filesys_lock);
          file_seek (map->file, written);
          if (file_write (map->file, kpage, to_write) != to_write)
            PANIC ("Unable to write data back to file!");
          lock_release (&filesys_lock);
        }
      write_left -= to_write;
      written += to_write;
    }
  frame_unlock ();
}

