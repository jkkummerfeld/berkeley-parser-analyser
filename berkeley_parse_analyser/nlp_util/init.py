#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

'''A collection of useful functions at startup.  There are definitely more
powerful, and flexible, alternatives out there, but this was what I needed at
the time.'''

import sys
import time

def header(args, out=sys.stdout):
    head_text = "# Time of run:\n# "
    head_text += time.ctime(time.time())
    head_text += "\n# Command:\n# "
    head_text += ' '.join(args)
    head_text += "\n#"
    if isinstance(out, list):
        for outfile in out:
            print(head_text, file=outfile)
    else:
        print("Need to fix isinstance file", file=sys.stderr)
    #if isinstance(out, file):
        print(head_text, file=out)
        #print("Invalid list of output files passed to header", file=sys.stderr)
        #sys.exit(1)

def argcheck(argv, minargs, maxargs, desc, arg_desc, further_desc=''):
    if minargs <= len(argv) <= maxargs:
        return
    print("{}\n  {} {}".format(desc, argv[0], arg_desc), file=sys.stderr)
    if len(further_desc) > 0:
        print("\n{}".format(further_desc), file=sys.stderr)
    print("Expected {} to {} args, got:\n{}".format(minargs - 1, maxargs - 1, ' '.join(argv)), file=sys.stderr)
    sys.exit(1)

if __name__ == "__main__":
    print("Running doctest")
    import doctest
    doctest.testmod()
