#include "userprog/syscall.h"
#include "userprog/process.h"
#include <stdio.h>
#include <syscall-nr.h>
#include "threads/interrupt.h"
#include "threads/thread.h"
#include "threads/vaddr.h"
#include "threads/synch.h"
#include "filesys/file.h"
#include "filesys/filesys.h"
#include "filesys/inode.h"
#include "filesys/directory.h"
#include <list.h>
#include "threads/malloc.h"
#include "devices/shutdown.h"
#include <round.h>

static struct file *file_desc_find (int fd);
static void syscall_handler (struct intr_frame *);
static struct file *get_file (int fd);
static void *check_uaddr (void *uaddr);
static size_t buffer_io (int fd, void *buffer, size_t size, bool write);
extern struct lock filesys_lock;

void
syscall_init (void) 
{
  intr_register_int (0x30, 3, INTR_ON, syscall_handler, "syscall");
}

/* Syscall implementing functions. */
static void sys_halt (void);
static void sys_exit (int status);
static uint32_t sys_exec (const char *cmd_line);
static uint32_t sys_wait (pid_t pid);
static uint32_t sys_create (const char *file, unsigned size);
static uint32_t sys_remove (const char *file);
static uint32_t sys_open (const char *file);
static uint32_t sys_filesize (int fd);
static uint32_t sys_read (int fd, void *buffer, unsigned size);
static uint32_t sys_write (int fd, const void *buffer, unsigned size);
static void sys_seek (int fd, unsigned pos);
static uint32_t sys_tell (int fd);
static void sys_close (int fd);
static bool sys_chdir (const char *path);
static bool sys_mkdir (const char *path);
static bool sys_readdir (int fd, char *name);
static bool sys_isdir(int fd);
static int sys_inumber (int fd);

/* Bad return values for system calls. */
#define SYSCALL_ERROR -1

/* Macros for extracting arguments from stack. */
#define ARG0 (*((uint32_t *) check_uaddr (esp + 1)))
#define ARG1 (*((uint32_t *) check_uaddr (esp + 2)))
#define ARG2 (*((uint32_t *) check_uaddr (esp + 3)))

/* Syscall handler. */
static void
syscall_handler (struct intr_frame *f)
{
  uint32_t *esp;
  struct thread *cur = thread_current ();
  /* Get the stack pointer and check if valid. */
  esp = (uint32_t *) check_uaddr (f->esp);
  cur->esp = (uint8_t *) esp;

  /* Make the syscall. */
  switch (*esp)
    {
      case SYS_HALT:
        sys_halt ();
        break;
      case SYS_EXIT:
        sys_exit ((int) ARG0);
        break;
      case SYS_EXEC:
        f->eax = sys_exec ((const char *) ARG0);
        break;
      case SYS_WAIT:
        f->eax = sys_wait ((pid_t) ARG0);
        break;
      case SYS_CREATE:
        f->eax = sys_create ((const char *) ARG0, (unsigned) ARG1);
        break;
      case SYS_REMOVE:
        f->eax = sys_remove ((const char *) ARG0);
        break;
      case SYS_OPEN:
        f->eax = sys_open ((const char *) ARG0);
        break;
      case SYS_FILESIZE:
        f->eax = sys_filesize ((int) ARG0);
        break;
      case SYS_READ:
        f->eax = sys_read ((int) ARG0, (void *) ARG1, (unsigned) ARG2);
        break;
      case SYS_WRITE:
        f->eax = sys_write ((int) ARG0, (void *) ARG1, (unsigned) ARG2);
        break;
      case SYS_SEEK:
        sys_seek ((int) ARG0, (unsigned) ARG1);
        break;
      case SYS_TELL:
        f->eax = sys_tell ((int) ARG0);
        break;
      case SYS_CLOSE:
        sys_close ((int) ARG0);
        break;
      case SYS_MMAP:
        f->eax = sys_mmap ((int) ARG0, (void *) ARG1);
        break;
      case SYS_MUNMAP:
        sys_munmap ((mapid_t) ARG0);
        break;
      case SYS_CHDIR:
        f->eax = sys_chdir ((const char *) ARG0);
        break;
      case SYS_MKDIR:
        f->eax = sys_mkdir ((char *) ARG0);
        break;
      case SYS_READDIR:
        f->eax = sys_readdir((int) ARG0, (char *) ARG1);
        break;
      case SYS_ISDIR:
        f->eax = sys_isdir((int) ARG0);
        break;
      case SYS_INUMBER:
        f->eax = sys_inumber ((int) ARG0);
        break;
      default:
        printf ("Invalid syscall!\n");
        cur->proc->exit = SYSCALL_ERROR;
        thread_exit ();
    }

  /* Clear the esp value for the thread. */
  cur->esp = NULL;
}

/* Implementation of SYS_HALT */
static void 
sys_halt (void)
{
  shutdown_power_off ();
}

/* Implementation of SYS_EXIT */
static void
sys_exit (int exit)
{
  /* Set our exit status so parent can still WAIT on it. */
  thread_current ()->proc->exit = exit;

  /* Exit the thread. */
  thread_exit ();
}

/* Implementation of SYS_EXEC */
static uint32_t
sys_exec (const char *cmd_line)
{
  /* Check that pointer is valid. */
  check_uaddr (cmd_line);

  /* Call into process_execute to start. */
  return (uint32_t) process_execute (cmd_line);
}

/* Implementation of SYS_WAIT */
static uint32_t
sys_wait (pid_t pid)
{
  return (uint32_t) process_wait ((tid_t) pid);
}

/* Implementation of SYS_CREATE */
static uint32_t
sys_create (const char *file_name, unsigned size)
{
  bool success;

  check_uaddr (file_name);
  success = filesys_create (file_name, size);
  return (uint32_t) success;
}

/* Implementation of SYS_REMOVE */
static uint32_t
sys_remove (const char *file_name)
{
  bool success;

  check_uaddr (file_name);
  success = filesys_remove (file_name);
  return (uint32_t) success;
}

/* Implementation of SYS_OPEN */
static uint32_t
sys_open (const char *file_name)
{
  struct file *f;
  struct thread *cur;
  struct fhandle *fh;

  check_uaddr (file_name);
  lock_acquire (&filesys_lock);
  f = filesys_open (file_name);
  lock_release (&filesys_lock);
  if (f == NULL)
    return SYSCALL_ERROR;
  cur = thread_current ();
  fh = malloc (sizeof (struct fhandle));
  fh->fd = cur->fd++;
  fh->file = f;
  list_push_back (&cur->files, &fh->elem);
  return (uint32_t) fh->fd;
}

/* Implementation of SYS_FILESIZE */
static uint32_t
sys_filesize (int fd)
{
  struct file *f;

  f = get_file (fd);
  if (f == NULL)
    return SYSCALL_ERROR;
  return file_length (f);
}

/* Implementation of SYS_READ */
static uint32_t
sys_read (int fd, void *buffer, unsigned size)
{
  struct file *f;
  unsigned i;
  size_t read;

  /* Check that the buffer is valid. */
  check_uaddr (buffer);
  check_uaddr (buffer + size);

  /* If the file is STDIN read it directly. */
  if(fd == STDIN_FILENO)
    {
      for (i = 0; i != size; i++)
        *((uint8_t *) (buffer + i)) = input_getc ();
      read = size;
    }

  /* If the file is STDOUT return an error. */
  else if (fd == STDOUT_FILENO)
    read = SYSCALL_ERROR;

  /* Else read it in from a file. */
  else
    read = buffer_io (fd, buffer, size, false);

  return read;
}


/* Implementation of SYS_WRITE */
static uint32_t
sys_write (int fd, const void *buffer, unsigned size)
{
  struct file *f;
  size_t written;

  /* Make sure that the buffer is valid. */
  check_uaddr (buffer);
  check_uaddr (buffer + size);

  /* If the file descriptor is STDOUT write it all at once. */
  if (fd == STDOUT_FILENO)
    {
      putbuf (buffer, size);
      written = size;
    }

  /* If the file descriptor is STDIN return an error. */
  else if (fd == STDIN_FILENO)
    written = SYSCALL_ERROR;

  /* Else write it to the file. */
  else
    written = buffer_io (fd, buffer, size, true);

  return written;
}

/* Implementation of SYS_SEEK */
static void
sys_seek (int fd, unsigned pos)
{
  struct file *f;

  f = get_file (fd);
  if (f == NULL)
    return;
  file_seek (f, pos);
}


/* Implementation of SYS_TELL */
static uint32_t
sys_tell (int fd) 
{
  struct file *f;
  f = get_file (fd);
  if(f == NULL)
    return SYSCALL_ERROR;
  return file_tell (f);
}

/* Implementation of SYS_CLOSE */
static void
sys_close (int fd)
{
  struct thread *cur;
  struct list_elem *e, *ne;
  struct fhandle *fh;

  cur = thread_current ();
  e = list_begin (&cur->files);
  while (e != list_end (&cur->files))
    {
      ne = list_next (e);
      fh = list_entry (e, struct fhandle, elem);
      if(fh->fd == fd)
        {
          file_close (fh->file);
          list_remove (&fh->elem);
          free(fh);
          break;
        }
      e = ne;
    }
}

mapid_t
sys_mmap (int fd, void *addr)
{
  struct thread *cur = thread_current ();
  struct file *f;
  struct page *pg;
  struct file_page *fp;

  /* Check that the arguments are valid. */
  if (fd == STDIN_FILENO || fd == STDOUT_FILENO
      || !is_user_vaddr (addr) || addr == NULL
      || (uintptr_t) addr % PGSIZE != 0)
    return SYSCALL_ERROR;

  /* Get the file to map. */
  f = get_file (fd);
  if (f == NULL || file_length (f) == 0)
    return SYSCALL_ERROR;
  f = file_reopen (f);
  if (f == NULL)
    return SYSCALL_ERROR;

  /* Add the file to the page table. */
  size_t offset = 0;
  size_t size, seg_size, size_left;
  size = size_left = file_length (f);
  while (size_left > 0)
    {
      seg_size = (size_left < PGSIZE) ? size_left : PGSIZE;
      pg = pagetable_get_page (cur->pagetable, addr + offset);
      if (pg != NULL)
        break;
      pg = malloc (sizeof (struct page));
      if (pg == NULL)
        break;
      fp = malloc (sizeof (struct file_page));
      if (fp == NULL)
        break;
      pg->flags = PAGE_MMAP;
      pg->flags |= PAGE_WRITE_BIT;
      pg->data = fp;
      fp->file = f;
      fp->size = seg_size;
      fp->offset = offset;
      pagetable_set_page (&cur->pagetable, pg, addr + offset);
      size_left -= (size_left < PGSIZE) ? size_left : PGSIZE;
      offset += PGSIZE;
    }
  if (!(offset >= size))
    {
      pagetable_clear (&cur->pagetable, addr, offset / PGSIZE);
      return SYSCALL_ERROR;
    }
	
  /* Add the mapping to the thread. */
  struct map *map = malloc (sizeof (struct map));
  if (map == NULL)
    {
      pagetable_clear (&cur->pagetable, addr, DIV_ROUND_UP (size, PGSIZE));
      return SYSCALL_ERROR;
    }
  map->id = cur->mapid++;
  map->file = f;
  map->base = addr;
  map->size = size;
  list_push_back (&cur->maps, &map->elem);
  return map->id;
}

void
sys_munmap (mapid_t mapping)
{
  struct thread *cur = thread_current ();
  struct map *map;
  struct list_elem *e;

  for (e = list_begin (&cur->maps);
       e != list_end (&cur->maps);
       e = list_next (e))
    {
      map = list_entry (e, struct map, elem);
      if (map->id == mapping)
        {
          list_remove (e);
          flush_map (map);
          pagetable_clear (&cur->pagetable, map->base,
                           DIV_ROUND_UP (map->size, PGSIZE));
          free (map);
          return;
        }
    }
}

/* Implementation of SYS_CHDIR */
static bool
sys_chdir (const char *path)
{
  struct thread *cur = thread_current ();
  struct dir *old_dir = cur->dir;
  struct dir *new_dir = dir_open_path (path);
  if (new_dir == NULL)
    return false;
  cur->dir = new_dir;
  dir_close (old_dir);
  return true;
}

/* Implementation of SYS_MKDIR */
static bool
sys_mkdir (const char *path)
{
  bool success = false;
  block_sector_t sector = 0;

  /* Split the path into dirname and filename. */
  size_t size = strlen (path) + 1;
  char *dirname = calloc (size, sizeof (char));
  char *filename = calloc (size, sizeof (char));
  dir_path_split (path, dirname, filename);

  /* Try opening the directory to create new one in. */
  struct dir *dir = dir_open_path (dirname);
  if (dir == NULL)
    goto done;

  /* Find a free block to use. */
  success = free_map_allocate (1, &sector);
  if (!success)
    goto done;

  /* Try creating the directory. */
  struct inode *inode = dir_get_inode (dir);
  block_sector_t parent = inode_get_inumber (inode);
  success = dir_create (sector, parent, 16);
  if (!success)
    goto done;

  /* Try adding the directory to its parent. */
  success = dir_add (dir, filename, sector);

done:
  /* Free resources and return success. */
  if (!success && sector != 0)
    free_map_release (sector, 1);
  if (dir != NULL)
    dir_close (dir);
  free (dirname);
  free (filename);
  return success;
}

/* Implementation of SYS_READDIR */
static bool
sys_readdir (int fd, char *name)
{
  struct file *f = get_file (fd);
  if (f == NULL || !inode_is_dir (file_get_inode (f)))
    return false;
  struct dir *dir = (struct dir *) f;
  return dir_readdir (dir, name);
}

/* Implementation of SYS_ISDIR */
static bool
sys_isdir (int fd)
{
  struct file *f = get_file(fd);
  if (f == NULL)
    return false;
  return inode_is_dir (file_get_inode (f));
}

/* Implementation of SYS_INUMBER */
int sys_inumber (int fd)
{
  struct file *f = get_file (fd);
  if (fd == NULL)
    return SYSCALL_ERROR;
  return inode_get_inumber (file_get_inode (f));
}

/* Given a file descriptor get a file. */
struct file *
get_file (int fd)
{
  struct thread *cur;
  struct fhandle *fh;
  struct list_elem *e;

  cur = thread_current();
  for (e = list_begin (&cur->files);
      e != list_end (&cur->files);
      e = list_next (e))
    {
      fh = list_entry (e, struct fhandle, elem);
      if (fh->fd == fd)
        return fh->file;
    }
  return NULL;
}

/* Check whether a user address is valid. */
static void *
check_uaddr (void *uaddr)
{
  if (uaddr == NULL || !is_user_vaddr (uaddr))
    sys_exit (SYSCALL_ERROR);
  return uaddr;
}

/* Definition of an IO function type. */
typedef size_t (*io_fn) (struct file *, void *, size_t);

/* Perform IO on a buffer that must be pinned in memory. */
size_t
buffer_io (int fd, void *buffer, size_t size, bool write)
{
  struct file *f;
  io_fn io = write ? file_write : file_read;
  int i, iters;
  size_t done = 0, to_do, pg_rest;

  /* Acquire file and check if valid. */
  f = get_file (fd);
  if (f == NULL || write && inode_is_dir (file_get_inode (f)))
    return SYSCALL_ERROR;

  /* Perform iterative IO. */
  iters = 1 + (pg_no (pg_round_down (buffer + size))
          - pg_no (pg_round_down (buffer)));
  for (i = 0; i < iters; i++)
    {
      pg_rest = (uintptr_t) pg_round_up (buffer + 1) - (uintptr_t) buffer;
      to_do = (pg_rest > size) ? size : pg_rest;
      frame_pin (pg_round_down (buffer));
      done += io (f, buffer, to_do);
      frame_unpin (pg_round_down (buffer));
      buffer += to_do;
      size -= to_do;
    }
  return done;
}
