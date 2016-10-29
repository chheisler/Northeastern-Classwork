#!/usr/bin/python
import re
import sys
import copy

if sys.argv[1] == '-h':
    print 'usage:', sys.argv[0], 'regex files...'

class DefaultDict (dict):
    """Dictionary with a default value for unknown keys."""
    def __init__(self, default):
        self.default = default
    def __getitem__(self, key):
        if key in self: return self.get(key)
        return self.setdefault(key, copy.deepcopy(self.default))
    def sorted(self, rev=True):
        counts = [ (c,w) for w,c in self.items() ]
        counts.sort(reverse=rev)
        return counts

r = re.compile(sys.argv[1]);
counts = DefaultDict(0)

if len(sys.argv) < 3:
    sys.argv += '-'

for filename in sys.argv[2:]:
    if filename == '-':
	file = sys.stdin
    else:
	file = open(filename,'r')
    for line in file.xreadlines():
	match = r.search(line)
	if match:
	    print filename, "\t", line,
	    if match.group(1):
		counts[match.group(1)] += 1

print counts.sorted()[:50]
