#include "filesys/filesys.h"
#include <debug.h>
#include <stdio.h>
#include <string.h>
#include "filesys/file.h"
#include "filesys/free-map.h"
#include "filesys/inode.h"
#include "filesys/directory.h"
#include "threads/thread.h"

/* Partition that contains the file system. */
struct block *fs_device;

static void do_format (void);

/* Initializes the file system module.
   If FORMAT is true, reformats the file system. */
void
filesys_init (bool format) 
{
  cache_init ();

  fs_device = block_get_role (BLOCK_FILESYS);
  if (fs_device == NULL)
    PANIC ("No file system device found, can't initialize file system.");

  inode_init ();
  free_map_init ();

  if (format) 
    do_format ();

  lock_init (&filesys_lock);
 
  free_map_open ();

  thread_current ()->dir = dir_open_root ();
}

/* Shuts down the file system module, writing any unwritten data
   to disk. */
void
filesys_done (void) 
{
  dir_close (thread_current ()->dir);
  free_map_close ();
  cache_flush ();
}

/* Creates a file named NAME with the given INITIAL_SIZE.
   Returns true if successful, false otherwise.
   Fails if a file named NAME already exists,
   or if internal memory allocation fails. */
bool
filesys_create (const char *name, off_t initial_size) 
{
  block_sector_t inode_sector = 0;

  /* Split the name into a dirname and a filename. */
  size_t size = strlen (name) + 1;
  char *dirname = calloc (size, sizeof (char));
  char *filename = calloc (size, sizeof (char));
  dir_path_split (name, dirname, filename);

  /* Try creating the file. */
  struct dir *dir = dir_open_path (dirname);
  bool success = (dir != NULL
                  && free_map_allocate (1, &inode_sector)
                  && inode_create (inode_sector, false, initial_size)
                  && dir_add (dir, filename, inode_sector));
  if (!success && inode_sector != 0) 
    free_map_release (inode_sector, 1);
  dir_close (dir);

  /* Free resources and return success. */
  free (dirname);
  free (filename);
  return success;
}

/* Opens the file with the given NAME.
   Returns the new file if successful or a null pointer
   otherwise.
   Fails if no file named NAME exists,
   or if an internal memory allocation fails. */
struct file *
filesys_open (const char *name)
{
  /* Split the name into dirname and filename. */
  size_t size = strlen (name) + 1;
  char *dirname = calloc (size, sizeof (char));
  char *filename = calloc (size, sizeof (char));
  dir_path_split (name, dirname, filename);

  /* Look up the file in the directory. */
  struct dir *dir = dir_open_path (dirname);
  struct inode *inode = NULL;
  if (dir != NULL)
    dir_lookup (dir, filename, &inode);
  dir_close (dir);

  /* Free resources and return file. */
  free (dirname);
  free (filename);
  return file_open (inode);
}

/* Deletes the file named NAME.
   Returns true if successful, false on failure.
   Fails if no file named NAME exists,
   or if an internal memory allocation fails. */
bool
filesys_remove (const char *name) 
{
  /* Split hte name into dirname and filename. */
  size_t size = strlen (name) + 1;
  char *dirname = calloc (size, sizeof (char));
  char *filename = calloc (size, sizeof (char));
  dir_path_split (name, dirname, filename);

  /* Try removing the file. */
  struct dir *dir = dir_open_path (dirname);
  bool success = dir != NULL && dir_remove (dir, filename);
  dir_close (dir); 

  /* Free resources and return success. */
  free (dirname);
  free (filename);
  return success;
}

/* Formats the file system. */
static void
do_format (void)
{
  printf ("Formatting file system...");
  free_map_create ();
  if (!dir_create (ROOT_DIR_SECTOR, ROOT_DIR_SECTOR, 16))
    PANIC ("root directory creation failed");
  free_map_close ();
  printf ("done.\n");
}
