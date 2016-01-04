##########################################
# Heemin Seog & Eugene Tang
# COS 401 - Sonnet Generation
#
# Implements a pure first-order markov model
# on the words
##########################################

from collections import Counter
import nltk
import random

RHYME_PAIRS = [(0,2), (1,3), (4,6), (5,7), (8,10), (9,11), (12,13)]

class Markov:
	def __init__(self, unigrams, bigrams, d_word_stress, rhymed, get_rhymes):
		random.seed()
		self.unigrams = unigrams
		self.bigrams = bigrams
		self.d_word_stress = d_word_stress
		self.rhymed = rhymed
		self.get_rhymes = get_rhymes

	# normalize an array
	def normalize(self, ar):
		tot = 0
		for _,_,v in ar:
			tot += v
		return [(k,s,v/tot) for k,s,v in ar]

	# make sure stress is alternating
	def check_stress(self, stress):
		prev_stress = ""
		for i in stress:
			if not prev_stress == "":
				if i == prev_stress:
					return False
			prev_stress = i
		return True

	# filter words by meter and number of syllables
	def filter(self, stress, syl_num, rhyme = None):
		filtered_words = []
		if not rhyme is None:
			vocab = self.get_rhymes(rhyme)
		else:
			vocab = self.unigrams
		for word in vocab:
			for s in self.d_word_stress[word]:
				if len(s) == 0:
					continue
				if not self.check_stress(s):
					continue
				if s[-1] == stress and len(s) <= syl_num: # check stress and length
					filtered_words.append((word,s))
					break
		return filtered_words

	# pick random word given probabilities
	def pick_word(self, probs):
		probs = self.normalize(probs)
		random.shuffle(probs)
		tot = random.random()
		for k,s,v in probs:
			tot -= v
			if tot <= 0:
				return k,s
		return "SHOULD NOT HAPPEN", "SHOULD NOT HAPPEN"

	# find random words to start lines
	def random_start_words(self):
		start_words = ["" for i in xrange(2 * len(RHYME_PAIRS))]
		for i1, i2 in RHYME_PAIRS:
			word1 = random.choice(self.rhymed)
			word2 = random.choice(list(self.get_rhymes(word1)))
			syl1 = list(self.d_word_stress[word1])[0]
			syl2 = list(self.d_word_stress[word2])[0]
			start_words[i1] = (word1, syl1)
			start_words[i2] = (word2, syl2)
		return start_words

	# find random word by stress and number of syllables
	def random_word(self, stress, syl_num):
		words = self.filter(stress, syl_num)
		return random.choice(words)

	# get probability of w1 preceding w2
	def get_prob(self, w_1, w_2):
		num = float(self.bigrams[(w_1, w_2)])/len(self.bigrams)
		den = float(self.unigrams[w_2])/len(self.unigrams)
		return num/den

	# find most likely word to follow word
	def find_most_likely(self, word, syl_num, sentence):
		if syl_num == 0:
			return sentence
		if syl_num % 2 == 0:
			stress = '+'
		else:
			stress = '-'
		word_probs = []
		for w,s in self.filter(stress, syl_num):
			if not self.get_prob(w, word) == 0:
				word_probs.append((w, s, self.get_prob(w, word)))
		if len(word_probs) == 0:
			n_word, n_stress = self.random_word(stress, syl_num)
			return self.find_most_likely(n_word, syl_num-len(n_stress), n_word + " " + sentence)
		n_word, n_stress = self.pick_word(word_probs)
		return self.find_most_likely(n_word, syl_num-len(n_stress), n_word + " " + sentence)

	def generate_line_for_rhyme(self, end_word):
		stress = list(self.d_word_stress[end_word])[0]
		s = self.find_most_likely(end_word, 9-len(stress)+1, end_word)
		return s

	def generate_lines_for_rhyme(self, end_word, n):
		sents = []
		for i in xrange(n):
			s = self.generate_line_for_rhyme(end_word)
			sents.append(s)
		return sents

	# generate sonnet
	def gen_sonnet(self):
		start_words = self.random_start_words()
		#print start_words
		s = ''
		for word, stress in start_words:
			s += self.find_most_likely(word, 9-len(stress)+1, word) + '\n'
		return s
