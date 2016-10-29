#include "filesys/directory.h"
#include <stdio.h>
#include <string.h>
#include <list.h>
#include "filesys/filesys.h"
#include "filesys/inode.h"
#include "threads/malloc.h"
#include "threads/thread.h"

/* A directory. */
struct dir 
  {
    struct inode *inode;                /* Backing store. */
    off_t pos;                          /* Current position. */
  };

/* A single directory entry. */
struct dir_entry 
  {
    block_sector_t inode_sector;        /* Sector number of header. */
    char name[NAME_MAX + 1];            /* Null terminated file name. */
    bool in_use;                        /* In use or free? */
  };

/* Delimiters and special tokens for paths */
#define PATH_DELIM "/"
#define ROOT_TOKEN ""
#define PWD_TOKEN "."
#define PARENT_TOKEN ".."

/* Creates a directory with space for ENTRY_CNT entries in the
   given SECTOR.  Returns true if successful, false on failure. */
bool
dir_create (block_sector_t sector, block_sector_t parent, size_t entry_cnt)
{
  bool success;
  size_t size = entry_cnt * sizeof (struct dir_entry);
  struct inode *inode = NULL;
  struct dir *dir;

  success = inode_create (sector, true, size);
  if (success)
    {
      inode = inode_open (sector);
      dir = dir_open (inode);
      if (dir == NULL)
        success = false;
      else
        success = dir_add (dir, PWD_TOKEN, sector)
                  && dir_add (dir, PARENT_TOKEN, parent);
    }
  if (inode != NULL)
    inode_close (inode);
  if (dir != NULL)
    dir_close (dir);
  return success;
}

/* Opens and returns the directory for the given INODE, of which
   it takes ownership.  Returns a null pointer on failure. */
struct dir *
dir_open (struct inode *inode) 
{
  struct dir *dir = calloc (1, sizeof *dir);
  if (inode != NULL && dir != NULL)
    {
      dir->inode = inode;
      dir->pos = 0;
      return dir;
    }
  else
    {
      inode_close (inode);
      free (dir);
      return NULL; 
    }
}

/* Opens the root directory and returns a directory for it.
   Return true if successful, false on failure. */
struct dir *
dir_open_root (void)
{
  return dir_open (inode_open (ROOT_DIR_SECTOR));
}

static bool lookup (const struct dir *, const char *,
                    struct dir_entry *, off_t *);

/* Open a directory given a relative path. */
struct dir *
dir_open_path (const char *path)
{
  struct dir_entry e;
  struct dir *dir, *next_dir;
  struct inode *inode;

  /* Get the directory to start from. */
  if (strlen (path) > 0 && path[0] == PATH_DELIM[0])
    dir = dir_open_root ();
  else
    dir = dir_reopen (thread_current ()->dir);

  /* Copy the path into a new string. */
  size_t size = strlen (path) + 1;
  char *path_copy = malloc (size);
  if (path_copy == NULL)
    return NULL;
  strlcpy (path_copy, path, size);

  /* Parse path into tokens and follow. */
  char *token, *save;
  bool first = false;
  for (token = strtok_r (path_copy, PATH_DELIM, &save);
       token != NULL;
       token = strtok_r (NULL, PATH_DELIM, &save))
    {
      /* Check for root directory token */
      if (strcmp (token, ROOT_TOKEN) == 0)
        {
          if (first)
            dir = dir_open_root ();
        }

      /* Else try to lookup token in directory. */
      else
        {
          if (lookup (dir, token, &e, NULL))
            {
              inode = inode_open (e.inode_sector);
              if (inode_is_dir (inode))
                {
                  next_dir = dir_open (inode);
                  dir_close (dir);
                  dir = next_dir;
                }
              else
                goto error;
            }
          else
            goto error;
        }
      first = false;
    }
  return dir;

/* If we couldn't parse the path clean up and return NULL. */
error:
  dir_close (dir);
  return NULL;
}

/* Opens and returns a new directory for the same inode as DIR.
   Returns a null pointer on failure. */
struct dir *
dir_reopen (struct dir *dir) 
{
  return dir_open (inode_reopen (dir->inode));
}

/* Destroys DIR and frees associated resources. */
void
dir_close (struct dir *dir) 
{
  if (dir != NULL)
    {
      inode_close (dir->inode);
      free (dir);
    }
}

/* Returns the inode encapsulated by DIR. */
struct inode *
dir_get_inode (struct dir *dir) 
{
  return dir->inode;
}

/* Searches DIR for a file with the given NAME.
   If successful, returns true, sets *EP to the directory entry
   if EP is non-null, and sets *OFSP to the byte offset of the
   directory entry if OFSP is non-null.
   otherwise, returns false and ignores EP and OFSP. */
static bool
lookup (const struct dir *dir, const char *name,
        struct dir_entry *ep, off_t *ofsp) 
{
  struct dir_entry e;
  size_t ofs;
  
  ASSERT (dir != NULL);
  ASSERT (name != NULL);

  for (ofs = 0; inode_read_at (dir->inode, &e, sizeof e, ofs) == sizeof e;
       ofs += sizeof e) 
    if (e.in_use && !strcmp (name, e.name)) 
      {
        if (ep != NULL)
          *ep = e;
        if (ofsp != NULL)
          *ofsp = ofs;
        return true;
      }

  return false;
}

/* Searches DIR for a file with the given NAME
   and returns true if one exists, false otherwise.
   On success, sets *INODE to an inode for the file, otherwise to
   a null pointer.  The caller must close *INODE. */
bool
dir_lookup (const struct dir *dir, const char *name,
            struct inode **inode) 
{
  struct dir_entry e;

  ASSERT (dir != NULL);
  ASSERT (name != NULL);

  inode_lock (dir->inode);
  if (lookup (dir, name, &e, NULL))
    *inode = inode_open (e.inode_sector);
  else
    *inode = NULL;
  inode_unlock (dir->inode);

  return *inode != NULL;
}

/* Adds a file named NAME to DIR, which must not already contain a
   file by that name.  The file's inode is in sector
   INODE_SECTOR.
   Returns true if successful, false on failure.
   Fails if NAME is invalid (i.e. too long) or a disk or memory
   error occurs. */
bool
dir_add (struct dir *dir, const char *name, block_sector_t inode_sector)
{
  struct dir_entry e;
  off_t ofs;
  bool success = false;

  ASSERT (dir != NULL);
  ASSERT (name != NULL);

  /* Check NAME for validity. */
  if (*name == '\0' || strlen (name) > NAME_MAX)
    return false;

  inode_lock (dir->inode);

  /* Check that NAME is not in use. */
  if (lookup (dir, name, NULL, NULL))
    goto done;

  /* Set OFS to offset of free slot.
     If there are no free slots, then it will be set to the
     current end-of-file.
     
     inode_read_at() will only return a short read at end of file.
     Otherwise, we'd need to verify that we didn't get a short
     read due to something intermittent such as low memory. */
  for (ofs = 0; inode_read_at (dir->inode, &e, sizeof e, ofs) == sizeof e;
       ofs += sizeof e) 
    if (!e.in_use)
      break;

  /* Write slot. */
  e.in_use = true;
  strlcpy (e.name, name, sizeof e.name);
  e.inode_sector = inode_sector;
  success = inode_write_at (dir->inode, &e, sizeof e, ofs) == sizeof e;

done:
  inode_unlock (dir->inode);
  return success;
}

static bool dir_empty (struct inode *);

/* Removes any entry for NAME in DIR.
   Returns true if successful, false on failure,
   which occurs only if there is no file with the given NAME. */
bool
dir_remove (struct dir *dir, const char *name) 
{
  struct dir_entry e;
  struct inode *inode = NULL;
  bool success = false;
  off_t ofs;

  ASSERT (dir != NULL);
  ASSERT (name != NULL);

  inode_lock (dir->inode);

  /* Find directory entry. */
  bool found = lookup (dir, name, &e, &ofs);
  if (!found)
    goto done;

  /* Open inode. */
  inode = inode_open (e.inode_sector);
  if (inode == NULL)
    goto done;

  /* Do not remove the directory if open or not empty. */ 
  if (inode_is_dir (inode) && (inode_get_inumber (inode) == ROOT_DIR_SECTOR
      || inode_get_open_cnt (inode) > 1 || !dir_empty (inode)))
    goto done;

  /* Erase directory entry. */
  e.in_use = false;
  if (inode_write_at (dir->inode, &e, sizeof e, ofs) != sizeof e) 
    goto done;

  /* Remove inode. */
  inode_remove (inode);
  success = true;

done:
  inode_close (inode);
  inode_unlock (dir->inode);
  return success;
}

/* Reads the next directory entry in DIR and stores the name in
   NAME.  Returns true if successful, false if the directory
   contains no more entries. */
bool
dir_readdir (struct dir *dir, char name[NAME_MAX + 1])
{
  struct dir_entry e;

  inode_lock (dir->inode);
  while (inode_read_at (dir->inode, &e, sizeof e, dir->pos) == sizeof e) 
    {
      dir->pos += sizeof e;
      if (e.in_use)
        {
          if (strcmp (e.name, PWD_TOKEN) == 0
              || strcmp (e.name, PARENT_TOKEN) == 0)
            continue;
          strlcpy (name, e.name, NAME_MAX + 1);
          inode_unlock (dir->inode);
          return true;
        } 
    }
  inode_unlock (dir->inode);
  return false;
}

/* Given a file name returns splits it into a relative path to directory and
   the file name in the directory, storing them in dirname and filename. */
void
dir_path_split (const char *name, char *dirname, char *filename)
{ 
  size_t size = strlen (name) + 1;
  char *last = strrchr (name, PATH_DELIM[0]);
  if (last == NULL)
      strlcpy (filename, name, size);
  else
    {
      strlcpy (dirname, name, last - name + 2);
      if (last == name + size - 2)
        strlcpy (filename, PWD_TOKEN, strlen (PWD_TOKEN) + 1);
      else
        strlcpy (filename, last + 1, name + size - last);
    }
}

/* Check whether a directory is empty. */
static bool
dir_empty (struct inode *inode) 
{
  struct dir_entry e;
  size_t ofs;
  
  ASSERT (inode != NULL);

  inode_lock (inode);
  for (ofs = 0; inode_read_at (inode, &e, sizeof e, ofs) == sizeof e;
       ofs += sizeof e)
    if (e.in_use && strcmp (e.name, PWD_TOKEN) != 0
        && strcmp (e.name, PARENT_TOKEN) != 0)
      {
        inode_unlock (inode);
        return false;
      }
  inode_unlock (inode);
  return true;
}
