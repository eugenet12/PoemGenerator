from collections import Counter
import nltk
import random

RHYME_PAIRS = [(0,2), (1,3), (4,6), (5,7), (8,10), (9,11), (12,13)]

# HIDDEN MARKOV MODEL
class HMM:
	def __init__(self, vocab, pos_uni, pos_bi, pos_tri, pos_word, d_word_stress, rhymed, get_rhymes):
		random.seed()
		self.vocab = vocab
		self.d_word_stress = d_word_stress
		self.rhymed = rhymed
		self.get_rhymes = get_rhymes
		self.pos_uni = pos_uni
		self.pos_bi = pos_bi
		self.pos_tri = pos_tri
		self.pos_word = pos_word

	# normalize an array
	def normalize_word(self, ar):
		tot = 0
		for _,_,v in ar:
			tot += v
		return [(k,s,v/tot) for k,s,v in ar]

	def normalize_pos(self, ar):
		tot = 0
		for _,v in ar:
			tot += v
		return [(k,v/tot) for k,v in ar]

	# make sure stress is alternating
	def check_stress(self, stress):
		prev_stress = ""
		for i in stress:
			if not prev_stress == "":
				if i == prev_stress:
					return False
			prev_stress = i
		return True

	# filter words by pos, meter and number of syllables
	def filter(self, stress, syl_num, pos = None, rhyme = None):
		filtered_words = []
		if not rhyme is None:
			vocab = self.get_rhymes(rhyme)
		elif not pos is None:
			vocab = self.pos_word[pos].keys()
		else:
			vocab = self.vocab

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
		probs = self.normalize_word(probs)
		random.shuffle(probs)
		tot = random.random()
		for k,s,v in probs:
			tot -= v
			if tot <= 0:
				return k,s
		return "SHOULD NOT HAPPEN", "SHOULD NOT HAPPEN"

	# pick random pos given probabilities
	def pick_pos(self, probs):
		probs = self.normalize_pos(probs)
		random.shuffle(probs)
		tot = random.random()
		for k,v in probs:
			tot -= v
			if tot <= 0:
				return k
		return "SHOULD NOT HAPPEN"

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

	# get probability of p1 preceding p2 and p3
	def get_pos_prob(self, p_1, p_2, p_3):
		if p_3 == None or self.pos_bi[(p_2, p_3)] == 0:
			num = float(self.pos_bi[(p_1,p_2)])/len(self.pos_bi)
			den = float(self.pos_uni[p_2])/len(self.pos_uni)
		else:
			num = float(self.pos_tri[(p_1, p_2, p_3)])/len(self.pos_tri)
			den = float(self.pos_bi[(p_2, p_3)])/len(self.pos_bi)
		return num/den

	# get probability of word w given pos
	def get_word_prob(self, word, pos):
		num = float(self.pos_word[pos][word])/len(self.pos_word[pos])
		den = float(self.pos_uni[pos])/len(self.pos_uni)
		return num/den

	# find most likely word to follow word
	def find_most_likely(self, pos1, pos2, word, syl_num, sentence):
		if syl_num == 0:
			return sentence
		if syl_num % 2 == 0:
			stress = '+'
		else:
			stress = '-'

		# get next pos
		pos_probs = []
		for pos in self.pos_uni:
			pos_prob = self.get_pos_prob(pos, pos1, pos2)
			if not pos_prob == 0:
				pos_probs.append((pos, pos_prob))
		if len(pos_probs) == 0:
			#print "NO POS FOUND!"
			pos = random.choice(self.pos_uni.keys())
		else:
			pos = self.pick_pos(pos_probs)

		word_probs = []
		for w,s in self.filter(stress, syl_num, pos):
			if not self.get_word_prob(w, pos) == 0:
				word_probs.append((w, s, self.get_word_prob(w, pos)))
		if len(word_probs) == 0:
			#print "NO WORD FOUND!"
			n_word, n_stress = self.random_word(stress, syl_num)
			return self.find_most_likely(pos, pos1, n_word, syl_num-len(n_stress), n_word + " " + sentence)
		n_word, n_stress = self.pick_word(word_probs)
		return self.find_most_likely(pos, pos1, n_word, syl_num-len(n_stress), n_word + " " + sentence)

	def generate_lines_for_rhyme(self, rhyme_word, n):
		rhymes = list(self.get_rhymes(rhyme_word))
		rhymes.append(rhyme_word)
		#print "rhymes", rhymes
		sents = []
		for i in xrange(n):
			word = random.choice(rhymes)
			pos = nltk.pos_tag([word])[0][1]
			stress = list(self.d_word_stress[word])[0]
			s = self.find_most_likely(pos, None, word, 9-len(stress)+1, word)
			sents.append(s)
		return sents

	def order(self, sentences):
		sonnet = [None for x in xrange(14)]
		for ((s1,s2),(v1,v2)) in zip(sentences, RHYME_PAIRS):
			sonnet[v1] = s1
			sonnet[v2] = s2
		return sonnet

	# generate sonnet
	def gen_sonnet(self):
		start_words = self.random_start_words()
		#print start_words
		s = ""
		for word, stress in start_words:
			pos = nltk.pos_tag([word])[0][1]
			s += self.find_most_likely(pos, None, word, 9-len(stress)+1, word) + '\n'
		return s

