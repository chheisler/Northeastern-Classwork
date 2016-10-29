from random import randint
from subprocess import call
from sys import argv

# global constants
NUMSYMS = 'numbers.syms'
NUMFST = 'numbers.fst'

# pick a random digit or read from comand line arguments
if len(argv) > 1:
    digits = argv[1]
else:
    digits = str(randint(0,999999999) % 10 ** randint(1,9))
    print digits
raw_name = digits + '.txt'
fst_name = digits + '.fst'

# create raw FST specification
raw = open(raw_name, 'w')
for i, c in enumerate(digits):
    raw.write("{0} {1} {2} {2}\n".format(i, i+1, c))
raw.write("%d\n" % len(digits))
raw.close()

# compile specification into FST
cmd = 'fstcompile --isymbols={0} --osymbols={0} < {1} > {2}'
call(cmd.format(NUMSYMS, raw_name, fst_name), shell=True)

# compose compiled FST with numbers.fst and print
cmd = 'fstcompose {0} {1} | fstproject --project_output |fstrmepsilon' \
      '| fstprint --isymbols={2} --osymbols={2}' 
call(cmd.format(fst_name, NUMFST, NUMSYMS), shell=True)

# clean up files
cmd = 'find -regex ".*/[0-9]+\.\(txt\|fst\)" | xargs -d"\n" rm'
call(cmd, shell=True)
