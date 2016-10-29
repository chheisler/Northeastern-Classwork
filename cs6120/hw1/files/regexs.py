#!/usr/bin/python
import re
import sys

#print 'regex', sys.argv[1]
#print 'files', sys.argv[2:]

r = re.compile(sys.argv[1]);

for filename in sys.argv[2:]:
    file = open(filename,'r')
    for line in file.xreadlines():
        m  = r.search(line)
	if m:
            # 	    print filename, "\t", m.group(0), "\t", line,
	    print filename, "\t", line,
