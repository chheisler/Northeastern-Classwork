#!/usr/bin/env python

import fileinput

state = 0
for line in fileinput.input():
    for c in line.strip('\n'):
        print state, state + 1, (c if (c != ' ') else '<space>')
        state += 1

print state
