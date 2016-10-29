#!/usr/bin/env python

import fileinput

state = 0
for line in fileinput.input():
    for tok in line.split():
        print state, state + 1, tok
        state += 1

print state
