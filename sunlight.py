#!/usr/bin/env python

import os
import sys
from re import split, match
from fnmatch import fnmatch
from mutagen.flac import FLAC
from mutagen.oggvorbis import OggVorbis
from optparse import OptionParser
import argparse
from tempfile import mkstemp

VERSION = '0.1'
usage_text = "%(prog)s [-catdnivz] [OPTS] [FILE/DIR]"
description="sunlight is a tagging swiss army knife for audio files"
info_text = """
`sunlight' will print tags for all files in cwd recursively

passing a file or path will perform operations on those files

`sunlight -i' will edit tags in $EDITOR, one file at a time

`sunlight -i -t title' will edit a single tag in $EDITOR, all
files at once

you can omit -a when passing two arguments (regardless of FILE/DIR)
if the tags are recognised:

`sunlight comment "Downloaded illegally"' will set the comment
`sunlight tracknumber' will display the tracknumber

editing my_tags will change which tags are "recognised" for the
above shorthand

`sunlight -n' will set the filenames akin to "01 - Title.flac"
"""
files = []
tracks = []

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

#class EncoderArg(argparse.Action):
#	def __init__(self, option_strings, dest, nargs=None, **kwargs):
#		super(EncoderArg, self).__init__(option_strings, dest, nargs, **kwargs)
#	def __call__(self, parser, namespace, values, option_string=None):
#		if isinstance(p.values, list):

#def set_opt(o, opt, v, p):
#	a = getattr(p.values, o.dest)
#	if isinstance(a, list):
#		a.append(v)
#	else:
#		a = [v]
#	setattr(p.values, o.dest, a)

def setup_parser():
	p = argparse.ArgumentParser(usage=usage_text, description=description, epilog=info_text)
	p.add_argument('--version', action='version', version='%(prog)s ' + VERSION)
	p.add_argument('-c', '--copy',   nargs=2, action='append', dest='c', help='copy TAG SRC')
	p.add_argument('-a', '--add',    nargs=2, action='append', dest='a', help='add TAG VAL')
	p.add_argument('-t', '--tag',    nargs=1, action='append', dest='t', help='tag TAG')
	p.add_argument('-d', '--delete', nargs=1, action='append', dest='d', help='delete TAG')
	p.add_argument('-n', '--names',           action='store_true', dest='n', help='set filesnames from tags')
	p.add_argument('-i', '--interactive',     action='store_true', dest='i', help='edit tags with $EDITOR, combines with -t')
	p.add_argument('-f', '--fuck',            action='store_true', dest='f', help='please find a better name for this argument')
	p.add_argument('-z', '--zeropad',         action='store_true', dest='z', help='zeropad tracknumbers')
	p.add_argument('-v', '--verbose',         action='store_true', dest='v', help='verbose')
	p.add_argument('files', nargs='*', help='files to edit')
	return p

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
			sys.exit("File/dir %s does not exist." % p)
		else:
			sys.exit("%s isn't a file or a dir" % p)
	f.sort()

def add_tag(files, tag, val):
	for f in files:
		f[tag] = val
		f.save()

def delete_tag(files, tag):
	for f in files:
		for t in tag:
			if t in f.tags: f.__delitem__(t)
		f.save()

def ext(f):
	return split("\.", f)[-1]

def interactive(track, tags, out, parse):
	tmp = mkstemp(prefix='sunlight-')[1]
	fd = open(tmp, 'w')
	out(fd, track, tags)
	fd.close()
	rv = os.system("$EDITOR " + tmp)
	if rv:
		print("err: $EDITOR returned nonzero value: " + str(rv))
		os.remove(tmp)
		exit(rv)
	fd = open(tmp, 'r')
	parse(list(fd), track, tags)
	fd.close()
	os.remove(tmp)

def is_tag(t):
	return t in my_tags or any([match(t, x) for x in my_tags])

def open_vorbis(f):
	if fnmatch(f.lower(), '*.flac'):
		return FLAC(f)
	if fnmatch(f.lower(), '*.ogg'):
		return OggVorbis(f)

def ptags(tracks, tags):
	for f in tracks:
		tags = tags if tags else f.tags.keys()
		for t in tags:
			print("\t%s: %s" % (t, f.tags[t][0]))
		print()

def pptags(tracks, tags, o=sys.stdout):
	com_tags = {}
	maxtaglen = 0
	for f in tracks:
		ts = tags if tags else f.tags.keys()
		for t in ts:
			if t in com_tags:
				if t not in f.tags or com_tags[t] != f.tags[t][0]:
					com_tags[t] = None
			else:
				com_tags[t] = f.tags[t][0]
		for t in com_tags:
			if t not in f.tags:
				com_tags[t] = None
	for t in com_tags.keys():
		if com_tags[t]:
			if len(t) > maxtaglen: maxtaglen = len(t)
	for t in sorted(com_tags.keys()):
		if com_tags[t]:
			print("%s%s" % (t.ljust(maxtaglen+1), com_tags[t]), file=o)
	print(file=o)
	maxtaglen = 0
	for f in tracks:
		print(os.path.basename(f.filename), file=o)
		ts = tags if tags else f.tags.keys()
		for t in ts:
			if len(t) > maxtaglen: maxtaglen = len(t)
		for t in sorted(ts):
			if not com_tags[t]:
				print("\t%s%s" % (t.ljust(maxtaglen+1), f.tags[t][0]), file=o)

def proper_names(tracks):
	for f in tracks:
		if opt.v: print("%s/%s - %s.%s" % (os.path.dirname(f.filename),
			        f['tracknumber'][0], f['title'][0], ext(f.filename).lower()))
		os.rename(f.filename, "%s/%s - %s.%s" % (os.path.dirname(f.filename),
			  f['tracknumber'][0], f['title'][0], ext(f.filename).lower()))

def read_tracks(names, l):
	for n in names:
		l.append(open_vorbis(n))

def zeropad(tracks):
	for t in tracks:
		add_tag([t], 'tracknumber', t['tracknumber'][0].zfill(2))

parser = setup_parser()
opt = parser.parse_args()
if opt.t: opt.t = [i[0] for i in opt.t]
if opt.a: opt.a = [i[0] for i in opt.a]
if opt.d: opt.d = [i[0] for i in opt.d]
if opt.c: opt.c = [i[0] for i in opt.c]
if not opt.files:
	opt.files = [os.getcwd()]
if os.path.isdir(opt.files[0]) or os.path.isfile(opt.files[0]):
	add_files(files, opt.files)
# enables 'sunlight title' to show title, 'sunlight title dog' to set title = dog
elif is_tag(opt.files[0]):
	for x in my_tags:
		if match(opt.files[0], x):
			opt.a = [(x, opt.files[1])]
	if len(opt.files) == 2:
		opt.files.append(os.getcwd())
	add_files(files, opt.files[2:])
else:
	print("%s is neither a valid path or a recognised tag" % opt.files[0])
	exit()
if not files:
	print("No files present, exiting.")
	exit()
read_tracks(files, tracks)
if opt.z:
	zeropad(tracks)
	exit()
if opt.i:
	if opt.f:
		def out(fd, tr, tags):
			pptags(tracks, tags, o=fd)
		def parse(ls, tr, tags):
			pass
		interactive(None, None, out, parse)
	elif opt.t != None and len(opt.t) == 1:
		def out(fd, tr, tags):
			for t in tracks:
				if tags[0] in t:
					fd.write("%s\n" % (t[tags[0]][0]))
				else:
					fd.write("\n")
		interactive(None, opt.t, out,
			lambda ls, tr, tags:
				[add_tag([tracks[i]], tags[0], ls[i][:-1])
				for i in range(len(tracks))])
	else:
		def out(fd, track, tags):
			tags = tags if tags else track.tags.keys()
			[fd.write("%s: %s\n" % (t, track[t][0])) for t in tags]
		for t in tracks:
			interactive(t, opt.t, out,
				lambda ls, tr, tags:
					[add_tag([tr],
					*split(": ", l[:-1], maxsplit=1))
					for l in ls])
	exit()
if opt.t:
	pptags(tracks, opt.t)
if opt.a:
	for g, v in opt.a:
		print("setting %s = %s" % (g, v))
		add_tag(tracks, g, v)
		if opt.v: ptags(tracks, None)
if opt.d:
	print("deleting tag %s" % (opt.d))
	delete_tag(tracks, opt.d)
if opt.n:
	print("setting proper filenames.")
	proper_names(tracks)
if not opt.t and not opt.n:
	pptags(tracks, None)
