#!/usr/bin/env python

import os
import sys
from fnmatch import fnmatch
from mutagen.flac import FLAC
from optparse import OptionParser

usage_text = "%prog [-a] FILE/DIR"
info_text = "laziness"
files = []
atags = []
vtags = []

def add_opt(option, opt, value, parser, *args, **kw):
	if isinstance(parser.values.a, list):
		parser.values.a.append(value)
	else:
		parser.values.a = [value]
	atags.append(value)
def tag_opt(option, opt, value, parser, *args, **kw):
	if isinstance(parser.values.t, list):
		parser.values.t.append(value)
	else:
		parser.values.t = [value]

parser = OptionParser(usage=usage_text, version="0.1", epilog="laziness")
#parser.add_option('-a', '--add', dest='a', help='add')
parser.add_option('-a', '--add', nargs=2, action='callback', callback=add_opt, dest='a', type='string', help='add')
parser.add_option('-t', '--tag', nargs=1, action='callback', callback=tag_opt, dest='t', type='string', help='add')
opt, par = parser.parse_args()

def add_files(f, paths):
	for p in paths:
		if os.path.isdir(p):
			for dp, dirs, files in os.walk(p, topdown=False):
				for n in files:
					if fnmatch(n.lower(), '*.flac'):
						f.append(os.path.join(dp, n))
					if fnmatch(n.lower(), '*.ogg'):
						f.append(os.path.join(dp, n))
		elif os.path.isfile(p):
			f.append(p)
		elif os.path.exists(p):
			sys.exit("File/dir %s does not exist. Get your act together." % p)
		else:
			sys.exit("%s isn't a file or a dir, what the fuck?" % p)

def ptags(files, tags):
	for fil in files:
		print(fil)
		f = FLAC(fil)
		tags = tags if tags else f.tags.keys()
		for t in tags:
			print("\t%s: %s" % (t, f.tags[t][0]))
		print()


def add_tag(files, tag, val):
	for fil in files:
		f = FLAC(fil)
		f[tag] = val
		f.save()

add_files(files, par)
#print("files:")
#print(files)
#print()
if opt.t:
	ptags(files, opt.t)
for g, v in atags:
	print("setting %s = %s" % (g, v))
	add_tag(files, g, v)
	ptags(files, None)
if not opt.t or opt.a:
	ptags(files, None)
#for f in files:
#	print(f)
#	ptags([f], None)

#f['title'] = 'Eternal Enemies'
#f.save()
#print(f.tags)
