# -*- coding: utf-8 -*-
##########################################
# Heemin Seog & Eugene Tang
# COS 401 - Sonnet Generation
#
# Used to clean the html files containing
# the poems from sonnets.org.
##########################################

from os import walk
import re
import string

# manually select which strings to remove from the text
remove = ['--','\?','!','"',',','@','#','$','%','\^','\&',
		 '\*','\(','\)','\[','\]',':',';','/','\\\\','`','~'
		 'nbsp','<dt>','</dt>','\.','<i>','</i>','<dl>',
		 '<p>','<.*?>', '[0-9]*']

def read_sonnets(in_dir, outfile):
	regex = r'<dt>'
	outfile = open(outfile, 'w')
	for (dirpath,dirnames,filenames) in walk(in_dir):
		filenames = sorted(filenames)
		for name in filenames:
			path = dirpath + '/' + name
			with open(path, 'r') as f:
				for line in f:
					if re.search(regex, line):
						s = re.sub('<dt>','',line)
						s = re.sub('-', ' ', s)
						s = re.sub(u'—', ' ', s)
						s = re.sub('nbsp', '', s)
						for p in remove:
							s = re.sub(p,'',s)
						if s.strip() == '':
							continue
						outfile.write('%s\n' % s.lower().strip())
	outfile.close()

read_sonnets('Sonnets', 'poem_lines.txt')