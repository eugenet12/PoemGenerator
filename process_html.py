##########################################
# Heemin Seog & Eugene Tang
# COS 401 - Sonnet Generation
#
# Used to clean the html files containing
# the shakespearean sonnets.
##########################################

from xml.dom import minidom
from os import walk

def read_sonnets(in_dir):
	for (dirpath,dirnames,filenames) in walk(in_dir):
		filenames = sorted(filenames)
		for name in filenames:
			path = dirpath + '/' + name
			xmldoc = minidom.parse(path)
			body = xmldoc.getElementsByTagName('body')[0]
			row = body.getElementsByTagName('tr')[1]
			text = row.getElementsByTagName('td')[0]
			sonnet = ''
			for node in text.childNodes:
				if node.nodeValue != None:
					sonnet += node.nodeValue.strip() + '\n'
			print sonnet
			with open('Shakespeare_parsed/' + name[:3], 'w') as f:
				f.write(sonnet)


read_sonnets('Shakespeare')
