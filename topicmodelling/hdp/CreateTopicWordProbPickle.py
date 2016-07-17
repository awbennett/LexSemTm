"""
Create Topic-Word Probabilities pickle file

Usage:          CreateTopicWordProbPickle.py <[test-]mode-topics.dat> <vocabs.txt> <output_pickle>
Stdin:          N/A
Stdout:         N/A
Other Input:    [test-]mode-topics.dat, vocabs.txt
Other Output:   topics.all.pickle
Author:         Jey Han Lau
Date:           June 12
"""

import sys
import pickle
import operator

#parameters
debug = False

if len(sys.argv) != 4:
    print "Usage: CreateTopicWordProbPickle.py <[test-]mode-topics.dat> <vocabs.txt> " + \
        "<output_pickle>"
    raise SystemExit

#input
tw_file = open(sys.argv[1])
vocab_file = open(sys.argv[2])
output_pickle = open(sys.argv[3], "w")

#global variables
vocabs = []
topic_wordprob = {}

#process the vocab file
for line in vocab_file:
    vocabs.append(line.strip())


topic_id = 1
for line in tw_file:
    wordprob = {}

    #collect frequency for each vocab
    freqs = map(int, line.split()[1:])
    total_freq = sum(freqs)

    for (i, freq) in enumerate(freqs):
        if freq > 0:
            wordprob[vocabs[i]] = float(freq)/total_freq 

    #add to the topic_wordprob dictionary
    topic_wordprob[topic_id] = wordprob 

    topic_id += 1

if debug:
    for (topic_id, wordprob) in sorted(topic_wordprob.items()):
        print topic_id, ":",
        for (word, prob) in sorted(wordprob.items(), key=operator.itemgetter(1), reverse=True)[:10]:
            print word + "/" + ("%.3f" % prob),
        print

pickle.dump(topic_wordprob, output_pickle)
