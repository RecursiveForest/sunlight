#!/usr/bin/env python

import os
import sys
from re import split, match
from fnmatch import fnmatch
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from optparse import OptionParser

usage_text = "%prog [-a] FILE/DIR"
info_text = "laziness"
files = []
atags = []
vtags = []

my_tags = [
	'album',
	'artist',
	'catalognumber',
	'comment',
	'country',
	'date',
	'discnumber',
	'genre',
	'label',
	'title',
	'tracknumber'
]

def set_opt(o, opt, v, p):
	a = getattr(p.values, o.dest)
	if isinstance(a, list):
		a.append(v)
	else:
		a = [v]
	setattr(p.values, o.dest, a)

parser = OptionParser(usage=usage_text, version="0.1", epilog="laziness")
#parser.add_option('-a', '--add', dest='a', help='add')
parser.add_option('-c', '--copy', nargs=2, action='callback', callback=set_opt, dest='c', type='string', help='copy TAG SRC')
parser.add_option('-a', '--add', nargs=2, action='callback', callback=set_opt, dest='a', type='string', help='add TAG VAL')
parser.add_option('-t', '--tag', nargs=1, action='callback', callback=set_opt, dest='t', type='string', help='tag TAG')
parser.add_option('-d', '--delete', nargs=1, action='callback', callback=set_opt, dest='d', type='string', help='delete TAG')
parser.add_option('-n', '--names', action='store_true', dest='n', help='names?')
parser.add_option('-v', '--verbose', action='store_true', dest='v', help='verbose')
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
	f.sort()

def open_vorbis(f):
	if fnmatch(f.lower(), '*.flac'):
		return FLAC(f)
	if fnmatch(f.lower(), '*.ogg'):
		return OggVorbis(f)

def ptags(files, tags):
	for fil in files:
		print(fil)
		f = open_vorbis(fil)
		tags = tags if tags else f.tags.keys()
		for t in tags:
			print("\t%s: %s" % (t, f.tags[t][0]))
		print()

def pptags(files, tags):
	# assumes open_vorbis is cheap
	print()
	com_tags = {}
	maxtaglen = 0
	for track in files:
		f = open_vorbis(track)
		tags = tags if tags else f.tags.keys()
		for t in tags:
			if t in com_tags:
				if com_tags[t] != f.tags[t][0]:
					com_tags[t] = None
			else:
				com_tags[t] = f.tags[t][0]
	for t in com_tags.keys():
		if com_tags[t]:
			if len(t) > maxtaglen: maxtaglen = len(t)
	for t in com_tags.keys():
		if com_tags[t]:
			print("%s%s%s" % (t, ' ' * (maxtaglen - len(t) + 1), com_tags[t]))
	print()
	maxtaglen = 0
	for track in files:
		print(os.path.basename(track))
		f = open_vorbis(track)
		tags = tags if tags else f.tags.keys()
		for t in tags:
			if len(t) > maxtaglen: maxtaglen = len(t)
		for t in tags:
			if not com_tags[t]:
				print("\t%s%s%s" % (t, ' ' * (maxtaglen - len(t) + 1), f.tags[t][0]))
				#print("\t%s: %s" % (t, f.tags[t][0]))
		#print()

def add_tag(files, tag, val):
	for fil in files:
		f = open_vorbis(fil)
		f[tag] = val
		f.save()

def delete_tag(files, tag):
	for fil in files:
		f = open_vorbis(fil)
		for t in tag:
			f.__delitem__(t)
		f.save()

def ext(f):
	return split("\.", f)[-1]

def proper_names(files):
	for fil in files:
		f = open_vorbis(fil)
		if opt.v: print("%s - %s.%s" % (f['tracknumber'][0], f['title'][0], ext(fil)))
		os.rename(fil, "./%s - %s.%s" % (f['tracknumber'][0], f['title'][0], ext(fil)))

def is_tag(t):
	return t in my_tags or any([match(t, x) for x in my_tags])

if os.path.isdir(par[0]) or os.path.isfile(par[0]):
	print("%s is a file or dir." % par[0])
	add_files(files, par)
elif is_tag(par[0]):
	for x in my_tags:
		if match(par[0], x):
			opt.a = [(x, par[1])]
	add_files(files, par[2:])
else:
	print("%s is neither a valid path or a recognised tag, exiting." % par[0])
	exit()
if not files:
	print("No files present, exiting.")
	exit()
if opt.t:
	ptags(files, opt.t)
if opt.a:
	for g, v in opt.a:
		print("setting %s = %s" % (g, v))
		add_tag(files, g, v)
		if opt.v: ptags(files, None)
if opt.d:
	print("deleting tag %s" % (opt.d))
	delete_tag(files, opt.d)
if opt.n:
	print("setting proper filenames.")
	proper_names(files)
if not opt.t and not opt.a and not opt.n:
	print("not not")
	pptags(files, None)
