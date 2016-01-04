##########################################
# Heemin Seog & Eugene Tang
# COS 401 - Sonnet Generation
#
# A wrapper class for the markov models which
# provides options to generate purely from markov model,
# use seed-line, and/or use seed-word
##########################################

import gensim
import random
from nltk.corpus import stopwords

RHYME_PAIRS = [(0,2), (1,3), (4,6), (5,7), (8,10), (9,11), (12,13)]

class Sonnet:
	def __init__(self, markov, sents, seed):
		self.model = gensim.models.Word2Vec(sents, min_count=1)
		self.markov = markov
		self.seed = seed
		self.stop = stopwords.words('english')

	def similarity(self, word, sent):
		vec1 = [word]
		vec2 = [w for w in sent.split(' ') if w not in self.stop]
		return self.model.n_similarity(vec1,vec2)

	def semantics_for_rhyme_set(self, n, rhyme_list, deviance=0.3, seed_rhyme=False):
		endings = {}
		if len(rhyme_list) > 10:
			if seed_rhyme:
				r_list = [(r,self.similarity(self.seed, r)) for r in rhyme_list]
				sum_r_scores = sum([v for s,v in r_list])
				r_list = [(s,v/sum_r_scores) for s,v in r_list]
				r_use = []
				for i in xrange(10):
					random.random()
					for s,v in r_list:
						if rand > 0:
							rand -= v
						else:
							break
					r_use.append(s)
				rhyme_list = r_use
			else:
				rhyme_list = random.sample(rhyme_list,10)
		for rhyme in rhyme_list:
			sents = self.markov.generate_lines_for_rhyme(rhyme, n)
			sents = [(s,self.similarity(self.seed, s)) for s in sents]
			sents.sort(key=lambda x: x[1])
			most_similar = sents[-1][1]
			sents = [(s,v) for s,v in sents if (v+deviance) >= most_similar]
			sum_scores = sum([v for s,v in sents])
			sents = [(s,v/sum_scores) for s,v in sents]
			endings[rhyme] = sents

		select = []
		for k,v in endings.iteritems():
			rand = random.random()
			for (s,val) in v:
				if rand > 0:
					rand -= val
				else:
					break
			select.append((s,val))
		select.sort(key=lambda x: x[1], reverse=True)
		select = [k for k,v in select]

		return (select[0],select[1])

	def semantics_by_word_similarity(self, n, seed_rhyme=False):
		sentences = []
		for x in xrange(7):
			r = random.choice(self.markov.rhymed)
			rhymes = list(self.markov.get_rhymes(r))
			rhymes.append(r)
			sentences.append(self.semantics_for_rhyme_set(n,rhymes,seed_rhyme))
		return sentences

	def order(self, sentences):
		sonnet = [None for x in xrange(14)]
		for ((s1,s2),(v1,v2)) in zip(sentences, RHYME_PAIRS):
			#print s1, s2, v1, v2
			sonnet[v1] = s1
			sonnet[v2] = s2
		return sonnet

	def gen_sonnet(self, n=1, plain=True, seed_rhyme=False):
		if not plain:
			sentences = self.semantics_by_word_similarity(n, seed_rhyme)
			poem = ''
			for s in self.order(sentences):
				poem += s + '\n'
			return poem
		else:
			return self.markov.gen_sonnet()