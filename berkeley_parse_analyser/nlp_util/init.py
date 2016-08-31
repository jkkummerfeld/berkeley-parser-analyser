#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vim: set ts=2 sw=2 noet:

'''A collection of useful functions at startup.  There are definitely more
powerful, and flexible, alternatives out there, but this was what I needed at
the time.'''

import sys, time

def header(args, out=sys.stdout):
	header = "# Time of run:\n# "
	header += time.ctime(time.time())
	header += "\n# Command:\n# "
	header += ' '.join(args)
	header += "\n#"
	if type(out) == type(sys.stdout):
		print >> out, header
	elif type(out) == type([]):
		for outfile in out:
			print >> outfile, header
	else:
		print >> sys.stderr, "Invalid list of output files passed to header"
		sys.exit(1)

def argcheck(argv, minargs, maxargs, desc, arg_desc, further_desc=''):
	if minargs <= len(argv) <= maxargs:
		return
	print >> sys.stderr, "{}\n  {} {}".format(desc, argv[0], arg_desc)
	if len(further_desc) > 0:
		print >> sys.stderr, "\n{}".format(further_desc)
	print >> sys.stderr, "Expected {} to {} args, got:\n{}".format(minargs - 1, maxargs - 1, ' '.join(argv))
	sys.exit(1)

if __name__ == "__main__":
	print "Running doctest"
	import doctest
	doctest.testmod()
