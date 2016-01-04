from nltk.corpus import brown
from nltk.corpus import cmudict
from collections import Counter
from itertools import islice
import re
import string
import sys
import nltk

from markov import Markov
from sonnet import Sonnet
from hmm import HMM

punc = string.punctuation
repunc = r'^\W*$'
d = cmudict.dict()

d_word_stress = {}
d_stress_word = {}
d_rhymes = {}
unigrams = Counter()
bigrams = Counter()
pos_unigrams = Counter()
pos_bigrams = Counter()
pos_trigrams = Counter()
pos_word = {}

BROWN_DIR = "brown_pos"
SONNET_DIR = "sonnet_pos"

##########################################################################
###################### UTILS #############################################
##########################################################################

def take(n, iterable):
    "Return first n items of the iterable as a list"
    return list(islice(iterable, n))

def has_vowel(syl):
    for l in syl.lower():
        if l in ('a', 'e', 'i', 'o', 'u'):
            return True
    return False

def remove_tokens(words):
    new_words = []
    for word in words:
        if not re.match(repunc,word):
            new_words.append(word)
    return new_words

def remove_bad_sents(sents):
    n_sents = []
    for s in sents:
        n_s = remove_tokens(s)
        valid = 0
        for token in n_s:
            token = token.lower()
            if token in d:
                valid += 1
        if valid == len(n_s):
            n_sents.append(n_s)
    return n_sents

def extract_number(syl):
    num = [c for c in syl if c.isdigit()]
    if len(num) > 0:
        return num[0]
    else:
        #print "no stress symbol"
        return 0

def remove_number(syl):
    rest = [c for c in syl if not c.isdigit()]
    return ''.join(rest)

def get_rhyme(word):
    options = d[word]
    n_options = []
    for ps in options:
        n_ps = []
        for i in xrange(len(ps)-1,-1,-1):
            if has_vowel(ps[i]):
                toadd = remove_number(ps[i])
                n_ps.append(toadd)
                break
            else:
                n_ps.append(ps[i])
        n_ps.reverse()
        n_options.append(''.join(n_ps))
    return set(n_options)

def get_stress_and_rhyme(word):
    if word in d:
        options = d[word]
        stresses = [''.join(['+' if int(extract_number(p)) > 0 else '-' for p in s if has_vowel(p)]) for s in options]
        rhymes = get_rhyme(word)
        return (stresses,rhymes)
    else:
        print "Error"
        return (None,None)

def process_sentences(sentences):
    global d_word_stress
    global d_stress_word
    global d_rhymes
    global unigrams
    global bigrams
    global pos_unigrams
    global pos_bigrams
    global pos_trigrams
    global pos_word

    i = 0
    for s in sentences:
        prev_word = ""
        for word in s:
            word = word.lower()
            (stresses,rhymes) = get_stress_and_rhyme(word)
            if (stresses,rhymes) == (None,None):
                #print "No stress/rhyme", word
                continue
            for stress in stresses:
                if not word in d_word_stress:
                    d_word_stress[word] = set()
                if not stress in d_stress_word:
                    d_stress_word[stress] = set()

                d_word_stress[word].add(stress)
                d_stress_word[stress].add(word)

            for rhyme in rhymes:
                if not rhyme in d_rhymes:
                    d_rhymes[rhyme] = set()
                d_rhymes[rhyme].add(word)

            unigrams[word] += 1
            if not prev_word == "":
                bigrams[(prev_word,word)] += 1
            prev_word = word

        """tags = nltk.pos_tag(s)
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
            prev_tag1 = tag"""
        if i % 1000 == 0:
            print "*",
            sys.stdout.flush()
        i += 1
    with open(DIR + "/pos_uni.csv", "r") as f:
        for line in f:
            tokens = line.rstrip().split(',')
            tokens = [t.strip() for t in tokens]
            pos_unigrams[tokens[0]] = int(tokens[1])
    #print pos_unigrams
    with open(DIR + "/pos_bi.csv", "r") as f:
        for line in f:
            tokens = line.rstrip().split(',')
            tokens = [t.strip() for t in tokens]
            pos_bigrams[(tokens[0],tokens[1])] = int(tokens[2])
    with open(DIR + "/pos_tri.csv", "r") as f:
        for line in f:
            tokens = line.rstrip().split(',')
            tokens = [t.strip() for t in tokens]
            pos_trigrams[(tokens[0],tokens[1],tokens[2])] = int(tokens[3])
    with open(DIR + "/pos_word.csv") as f:
        for line in f:
            tokens = line.rstrip().split(',')
            tokens = [t.strip() for t in tokens]
            pos_word[tokens[0]] = Counter()
            for i in xrange((len(tokens)-1)/2):
                pos_word[tokens[0]][tokens[2*i+1]] = int(tokens[2*(i+1)])

    # Used the first time around to pipe into a file. Read from file
    # afterwards
    """top10_pos_uni = pos_unigrams.most_common()[:10]
    top10_pos_bi = pos_bigrams.most_common()[:10]
    top10_pos_tri = pos_trigrams.most_common()[:10]
    top10_pos_word = pos_word[top10_pos_uni[0][0]].most_common()[:10]
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
    with open("s_pos_uni.csv", "w") as f:
        for pos, count in pos_unigrams.items():
            f.write("%s,%d\n" % (pos,count))
    with open("s_pos_bi.csv", "w") as f:
        for pos_pair, count in pos_bigrams.items():
            p1, p2 = pos_pair
            f.write("%s,%s,%d\n" % (p1, p2, count))
    with open("s_pos_tri.csv", "w") as f:
        for pos_tri, count in pos_trigrams.items():
            p1, p2, p3 = pos_tri
            f.write("%s,%s,%s,%d\n" % (p1, p2, p3, count))
    with open("s_pos_word.csv", "w") as f:
        for pos, counts in pos_word.iteritems():
            f.write(pos)
            for word, count in counts.items():
                f.write(",%s,%d" % (word, count))"""

def get_valid_brown_corpus():
    global DIR
    DIR = BROWN_DIR
    genre = ['adventure', 'belles_lettres', 'editorial', 'fiction', 'government', 'hobbies', 'humor', 'learned', 'lore', 'mystery', 'news', 'religion', 'reviews', 'romance', 'science_fiction']
    sentences = brown.sents(categories=genre)
    sents = remove_bad_sents(sentences)
    sents = [[w.lower() for w in s] for s in sents]
    return sents

def get_valid_sentences_from_file(filename):
    global DIR
    DIR = SONNET_DIR
    sentences = []
    with open(filename,'r') as f:
        for line in f:
            s = line.strip().split()
            sentences.append(s)
    return remove_bad_sents(sentences)

# make sure stress is alternating
# make sure the word has a stress (not "hmm")
# make sure it ends in a positive stress
def check_stress(word):
    stress = list(d_word_stress[word])[0]
    if len(stress) == 0:
        return False
    if stress[-1] != "+":
        return False
    prev_stress = ""
    for i in stress:
        if not prev_stress == "":
            if i == prev_stress:
                return False
        prev_stress = i
    return True

def get_rhymed():
    rhymed = set()
    for k,v in d_rhymes.iteritems():
        filter_v = [w for w in v if check_stress(w)]
        if len(filter_v) <= 1:
            continue
        for w in filter_v:
            rhymed.add(w)
    return rhymed

def get_rhyme_words(word):
    endings = get_rhyme(word)
    words = set()
    #print word
    for ending in endings:
        words = words.union(d_rhymes[ending])
    words.remove(word)
    words = set([w for w in words if check_stress(w)])
    return words

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

def find_stats(sent_list):
    print_stats = True
    word_list = [w for s in sent_list for w in s]
    word_counts = Counter(word_list)
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

if __name__ == '__main__':
    '''
    brown = get_valid_brown_corpus()
    sonnet = get_valid_sentences_from_file('poem_lines.txt')
    print "BROWN"
    find_stats(brown)
    print ""
    print "SONNET"
    find_stats(sonnet)
    '''
    if len(sys.argv) == 1:
        print "Please provide a whether you want to run on brown or sonnets"
        print "python process_corpus [brown/sonnets]"
        sys.exit(0)
    if len(sys.argv) == 2:
        print "Please provide a seed word"
        sys.exit(0)

    if sys.argv[1] == "brown":
        sents = get_valid_brown_corpus()
        process_sentences(sents)
    elif sys.argv[1] == "sonnets":
        sents = get_valid_sentences_from_file('poem_lines.txt')
        process_sentences(sents)
    else:
        print "Please provide a whether you want to run on brown or sonnets"
        print "python process_corpus [brown/sonnets]"
        sys.exit(0)

    rhymed = get_rhymed()
    markov = Markov(unigrams, bigrams, d_word_stress, list(rhymed), get_rhyme_words)
    sonnet = Sonnet(markov, sents, sys.argv[2])
    p1 = sonnet.gen_sonnet(10)
    p2 = sonnet.gen_sonnet(10, False)
    p3 = sonnet.gen_sonnet(10, True)

    hmm = HMM(unigrams, pos_unigrams, pos_bigrams, pos_trigrams, pos_word, d_word_stress, list(rhymed), get_rhyme_words)
    sonnet = Sonnet(hmm, sents, sys.argv[2])
    p4 = sonnet.gen_sonnet(10)
    p5 = sonnet.gen_sonnet(10, False)
    p6 = sonnet.gen_sonnet(10, True)

    if sys.argv[1] == "brown":
        get_poems_to_test("brown-test-poems.txt","Brown Corpus", "topic: "+sys.argv[2],p1,p2,p3,p4,p5,p6)
    else:
        get_poems_to_test("sonnet-test-poems.txt","Sonnet Corpus", "topic: "+sys.argv[2],p1,p2,p3,p4,p5,p6)

    '''
    sents = get_valid_brown_corpus()
    process_sentences(sents)
    rhymed = get_rhymed()
    markov = Markov(unigrams, bigrams, d_word_stress, list(rhymed), get_rhyme_words)
    sonnet = Sonnet(markov, sents, 'horses')
    print sonnet.gen_sonnet(10)
    '''
