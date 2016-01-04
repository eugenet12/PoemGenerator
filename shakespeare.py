import sys
import itertools
import nltk
import string
import nltk
import operator
import random
from collections import Counter
from markov import Markov
from sonnet import Sonnet
from hmm import HMM

NUM_FILES = 154

# Files that contain too many errors to fix by hand
SKIP = [3, 5, 7, 8, 10, 11, 12, 17, 19, 20, 26, 28, 29, 30, 31, 33,
		40, 42, 43, 45, 46, 51, 52, 55, 56, 58, 59, 66, 74, 75, 78,
		80, 81, 82, 84, 86, 87, 88, 90, 91, 93, 94, 99, 100, 108,
		111, 112, 113, 114, 115, 116, 118, 119, 120, 121, 124, 125,
		126, 127, 129, 132, 133, 135, 139, 141, 142, 144, 145, 152]

# punctuation to remove
PUNC = ":;,.?!()"

# structure of poems
RHYME_PAIRS = [(0,2), (1,3), (4,6), (5,7), (8,10), (9,11), (12,13)]

vocabulary = []
word_counts = Counter()
d = {}               # word to pronunciation
d_word_stress = {}   # word to stress
d_stress_word = {}   # stress to word
d_rhymes = {}        # rhyme groups
unigrams = Counter()
bigrams = Counter()
pos_unigrams = Counter()
pos_bigrams = Counter()
pos_trigrams = Counter()
pos_word = {}
sentences = []

################################################################
# General utils
################################################################

# Get tokens from a line of Shakespeare
def get_tokens(line):
	r_tokens = line.rstrip().split()
	tokens = []
	for token in r_tokens:
		token = ''.join(c for c in token if c not in PUNC)
		if '-' in token:
			tokens += token.split('-')
		else:
			tokens.append(token)
	tokens = [token.lower() for token in tokens]
	return tokens

# Read dictionary of pronunciations
def read_dictionary():
	global d
	with open('pronunciation.txt', 'r') as f:
		for line in f:
			tmp = line.rstrip().split('\t')
			if tmp[0][-1] == ')':
				tmp[0] = tmp[0][:-3]
			if not tmp[0].lower() in d:
				d[tmp[0].lower()] = []
			d[tmp[0].lower()].append(tmp[1].split())


################################################################
# Syllable Finding
################################################################
# Does it have a vowel
def has_vowel(syl):
	for l in syl.lower():
		if l in ('a', 'e', 'i', 'o', 'u'):
			return True
	return False

def list_num_syl(word):
	return [len([True for t in s if has_vowel(t)]) for s in d[word]]

# Get number of syllables
def get_list_num_syl(word):
	if word in d:
		return list_num_syl(word)
	else:
		#print "WORD_NOT_FOUND"
		return [0]

# map tokens of stress/syllables
def create_stress_map(tokens,syls):
	global d_word_stress
	global d_stress_word
	syl_count = 0
	for word,syl in zip(tokens,syls):
		stress = ''
		for i in xrange(syl):
			if syl_count % 2 == 0:
				stress += '-'
			else:
				stress += '+'
			syl_count += 1
		if word in d_word_stress:
			d_word_stress[word].add(stress)
		else:
			# avoid keyerrors
			if not word in d_word_stress:
				d_word_stress[word] = set()
			if not stress in d_stress_word:
				d_stress_word[stress] = set()

			d_word_stress[word].add(stress)
			d_stress_word[stress].add(word)

def add_rhymes(last_words):
	global d_rhymes

	for i1, i2 in RHYME_PAIRS:
		w1 = last_words[i1]
		w2 = last_words[i2]

		# check that word ends in positive stress
		if list(d_word_stress[w1])[0][-1] == "-":
			continue 

		if not w1 in d_rhymes:
			d_rhymes[w1] = set()
		if not w2 in d_rhymes:
			d_rhymes[w2] = set()

		d_rhymes[w1].add(w2)
		d_rhymes[w2].add(w1)

def update_rhymes():
	global d_rhymes

	for key in d_rhymes:
		tmp = d_rhymes[key]
		for word in d_rhymes[key]:
			tmp.union(d_rhymes[word])
		tmp.discard(key)
		d_rhymes[key] = tmp

count = 0
kill = []
def create_map_bestfit():
	global count

	# error file
	ferror = open('incorrect.txt','w')

	# for each file
	for i in xrange(1, NUM_FILES+1):
		if i in SKIP:
			continue
		#print i
		with open("Shakespeare_parsed/%03d" % i) as f:

			# number of lines that fit
			num_agree = 0

			# last words of each line
			last_words = []

			for line in f:
				tokens = get_tokens(line)
				if len(tokens) == 0:
					continue

				last_words.append(tokens[-1])

				# get syllable counts
				syls = [get_list_num_syl(t) for t in tokens]
				syls = itertools.product(*syls)
				syls = [list(s) for s in syls]
				syls_fit = [s for s in syls if sum(s) == 10]

				# if no matchings of syllables fit
				if len(syls_fit) == 0:

					# write error
					ferror.write('%d: %s\n' % (i,' '.join(tokens)))
					err = [[str(t) for t in j] for j in syls]
					for e,s in zip(err,syls):
						ferror.write('%d: %s\n' % (sum(s),' '.join(e)))

					count += 1
					create_stress_map(tokens, syls[0])
				else:
					create_stress_map(tokens, syls_fit[0])
					num_agree += 1

			add_rhymes(last_words)

			if num_agree < 12:
				kill.append(i)
				print "ARTICLE%d" % i
		if i == 200:
			break
	#print kill
	update_rhymes()
	ferror.close()

################################################################
# Stats and co.
################################################################
def find_stats(print_stats):
	global vocabulary
	global c
	for i in xrange(1, NUM_FILES+1):
		with open("Shakespeare_parsed/%03d" % i) as f:
			for line in f:
				tokens = get_tokens(line)
				if len(tokens) == 0:
					continue
				for token in tokens:
					word_counts[token] += 1
	vocabulary = word_counts.keys()
	num_words = sum(word_counts.values())
	top10 = word_counts.most_common()[:10]
	if print_stats:
		print "STATS:"
		print "Number of Words: %d" % num_words
		print "Number of Unique Words: %d" % len(vocabulary)
		print "Top 10 Words:"
		for word, count in top10:
			print "%5s, %2d" % (word, count)

def rhyme_stats():
	print "Number of Rhymed Words: %d" % len(d_rhymes)
	tot_rhymes = 0
	for k,v in d_rhymes.iteritems():
		tot_rhymes += len(v)
	print "Average number of Rhymes: %f" % (tot_rhymes/float(len(d_rhymes)))

def print_words():
	for word in vocabulary:
		print word

def get_rhymes(word):
	return d_rhymes[word]

def get_counts():
	global unigrams
	global bigrams
	global sentences

	for i in xrange(1, NUM_FILES+1):
		if i in SKIP:
			continue
		with open("Shakespeare_parsed/%03d" % i) as f:
			for line in f:
				tokens = get_tokens(line)
				tokens = [t.lower() for t in tokens]
				tags = nltk.pos_tag(tokens)
				if len(tokens) == 0:
					continue
				sentences.append(tokens)
				prev_word = ""
				for token in tokens:
					unigrams[token] += 1
					if not prev_word == "":
						bigrams[(prev_word,token)] += 1
					prev_word = token

	top10_uni = unigrams.most_common()[:10]
	top10_bi = bigrams.most_common()[:10]

def get_pos_counts():
	global pos_unigrams
	global pos_bigrams
	global pos_trigrams
	global pos_word

	for i in xrange(1, NUM_FILES+1):
		if i in SKIP:
			continue
		with open("Shakespeare_parsed/%03d" % i) as f:
			for line in f:
				tokens = get_tokens(line)
				tokens = [t.lower() for t in tokens]
				tags = nltk.pos_tag(tokens)
				if len(tokens) == 0:
					continue
				prev_tag1 = ""
				prev_tag2 = ""
				for word,tag in tags:
					if not tag in pos_word:
						pos_word[tag] = Counter()
					pos_word[tag][word] += 1
					pos_unigrams[tag] += 1
					if not prev_tag1 == "":
						pos_bigrams[(prev_tag1,tag)] += 1
					if not prev_tag2 == "":
						pos_trigrams[(prev_tag2,prev_tag1,tag)] += 1
					prev_tag2 = prev_tag1
					prev_tag1 = tag

	top10_pos_uni = pos_unigrams.most_common()[:10]
	top10_pos_bi = pos_bigrams.most_common()[:10]
	top10_pos_tri = pos_trigrams.most_common()[:10]
	top10_pos_word = pos_word[top10_pos_uni[0][0]].most_common()[:10]
	# PRINT STATISTICS OF THE CORPUS IF DESIRED
	'''
	print "STATS:"
	print "Top 10 POS:"
	for pos, count in top10_pos_uni:
		print "%5s, %2d" % (pos, count)
	print "Top 10 POS Bigrams:"
	for pos_pair, count in top10_pos_bi:
		p1, p2 = pos_pair
		print "%5s %5s, %2d" % (p1, p2, count)
	print "Top 10 POS Trigrams:"
	for pos_tri, count in top10_pos_tri:
		p1, p2, p3 = pos_tri
		print "%5s %5s %5s, %2d" % (p1, p2, p3, count)
	print "Top 10 words for top POS:"
	for word, count in top10_pos_word:
		print "%5s, %2d" % (word, count)
	'''

def get_poems_to_test(outfile, corpus_name, header, p1, p2, p3, p4, p5, p6):
    with open(outfile,'w') as f:
        f.write("%s\n" % corpus_name)
        f.write("%s\n\n" % header)
        f.write("Regular Markov Model\n")
        f.write("-------------------------------------\n")
        f.write("%s\n\n" % p1)
        f.write("Markov Model w/ inter-line similarity\n")
        f.write("-------------------------------------\n")
        f.write("%s\n\n" % p2)
        f.write("Markov Model w/ inter-line & rhyme similarity\n")
        f.write("-------------------------------------\n")
        f.write("%s\n\n" % p3)
        f.write("Regular HMM\n")
        f.write("-------------------------------------\n")
        f.write("%s\n\n" % p4)
        f.write("HMM w/ inter-line similarity\n")
        f.write("-------------------------------------\n")
        f.write("%s\n\n" % p5)
        f.write("HMM w/ inter-line & rhyme similarity\n")
        f.write("-------------------------------------\n")
        f.write("%s\n\n" % p6)

if len(sys.argv) == 1:
	print "Please provide a seed word."
	sys.exit(0)


find_stats(False)
read_dictionary()
create_map_bestfit()

get_counts()
vocabulary = unigrams.keys()
num_words = sum(unigrams.values())
top10 = unigrams.most_common()[:10]
#print "STATS:"
#print "Number of Words: %d" % num_words
#print "Number of Unique Words: %d" % len(vocabulary)
#print "Top 10 Words:"
#for word, count in top10:
#    print "%5s, %2d" % (word, count)

get_pos_counts()
markov_model = Markov(unigrams, bigrams, d_word_stress, d_rhymes.keys(), get_rhymes)
sonnet = Sonnet(markov_model, sentences, sys.argv[1])
p1 = sonnet.gen_sonnet(10)
p2 = sonnet.gen_sonnet(10, False)
p3 = sonnet.gen_sonnet(10, True)

hmm = HMM(unigrams, pos_unigrams, pos_bigrams, pos_trigrams, pos_word, d_word_stress, d_rhymes.keys(), get_rhymes)
sonnet = Sonnet(hmm, sentences, sys.argv[1])
p4 = sonnet.gen_sonnet(10)
p5 = sonnet.gen_sonnet(10, False)
p6 = sonnet.gen_sonnet(10, True)

get_poems_to_test("shakespeare-test-poems.txt","Shakespeare", "topic: "+sys.argv[1],p1,p2,p3,p4,p5,p6)

