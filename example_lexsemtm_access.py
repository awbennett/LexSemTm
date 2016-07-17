"""
Created by: Andrew Bennett
Last updated: July, 2016

Script demonstrating use of lexsemtm interface
"""

from lexsemtm import get_reader

# Obtain reader object to obtain data from LexSemTM
# Assumes that LexSemTM data and index files are stored in lexsemtm_data
reader = get_reader("lexsemtm_data")

# Obtain sense distribution for the noun "tree"
# Note that the format of lemma names are WORD.POS.LANG, and that at present
# the only available language and LexSemTM version are "en" and "s"
# respectively
sense_dist = reader.get_sense_dist("tree.n.en", lang="en", which_version="s")
print "sense distribution of noun 'tree':"
for s, p in sorted(sense_dist.iteritems()):
    print s, p
print ""

# Obtain topic model for the adjective "red"
# Note that:
# 1. tm["doc_topic_counts"] is a dict mapping lemma usage ID to dict of
#    topic counts
# 2. tm["topic_word_counts"] is a dict mapping topic ID to a dict
#    of word counts
tm = reader.get_topic_model("red.a.en", lang="en", which_version="s")
print "fields in topic model of adjective 'red':"
for key in sorted(tm.iterkeys()):
    print key
print ""

# Obtain the LexSemTM frequency of the adverb "silently"
freq = reader.get_lemma_freq("silently.r.en", lang="en", which_version="s")
print "frequency of adverb 'silently': %d" % freq
print ""

# Obtain list of all lemmas in LexSemTM, and print first 10
lemma_names = reader.get_lemma_names(lang="en", which_version="s")
print "total number of lemmas in LexSemTM: %d" % len(lemma_names)
print "first 10 lemmas:"
for lemma in lemma_names[:10]:
    print lemma
print ""
