#ifndef USERPROG_PROCESS_H
#define USERPROG_PROCESS_H

/* Data type for a map ID. */
typedef int mapid_t;
#define MAPID_ERROR ((mapid_t) -1)

#include "threads/thread.h"
#include "threads/synch.h"
#include "threads/vaddr.h"
#include "filesys/file.h"
#include <stdbool.h>
#include <list.h>

/* Definition of PID type. */
typedef int pid_t;
#define PID_ERROR ((pid_t) -1)

/* Function definitions. */
tid_t process_execute (const char *args);
int process_wait (tid_t);
void process_exit (void);
void process_activate (void);
struct process *process_child (pid_t pid);

/* Definitions of sizes in argument page for args and argv. */
#define ARGS_SIZE PGSIZE / 2
#define ARGV_SIZE (PGSIZE - ARGS_SIZE - sizeof (unsigned)) / sizeof (char *)

/* A structure for holding process arguments, argv and argc in a page of
   contiguous memory. */
struct args_page
  {
    char args[ARGS_SIZE];  /* String args. */
    char *argv[ARGV_SIZE]; /* Pointers to args */
    unsigned argc;         /* Number of args. */
  };

/* Enumeration of process states. */;
enum process_status
  {
    PROCESS_FAIL,
    PROCESS_RUN,
    PROCESS_DEAD,
    PROCESS_ORPHAN
  };

/* Data structure representing a user process. */
struct process
  {
    pid_t pid;                  /* The PID of the process. */
    enum process_status status; /* Current state of the process. */
    struct list_elem elem;      /* The process's list elem. */
    struct semaphore sema;      /* To synch exec and wait with parent. */
    struct lock status_mod;     /* Lock to modify process state. */
    int exit;                   /* Exit code of this process. */
  };

/* Data structure for an open file handle. */
struct fhandle
  {
    int fd;                 /* File descriptor for file. */
    struct file *file;      /* Pointer to open file. */
    struct list_elem elem; /* Element for list file lists. */
  };

/* Data structure for a memory mapped file. */
struct map
  {
    mapid_t id;            /* The ID of the mapping. */
    struct file *file;     /* The file on disk. */
    void *base;            /* The file in memory. */
    size_t size;           /* The size of the file. */ 
    struct list_elem elem; /* Element for map list. */
  };

/* Flush a memory mapped file to disk. */
void flush_map (struct map *map);

/* Delimiter for tokenizing arguments. */
#define ARG_DELIM " "

/* The size of a word. */
#define WORD_SIZE 4

/* Error definitions. */
#define BAD_EXIT -1
#define BAD_WAIT -1
#define BAD_ARGS -1

#endif /* userprog/process.h */
