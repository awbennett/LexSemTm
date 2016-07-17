"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides class for creating corpus based on lemma usages file, which can
be used to help create WSI output, and map vocab ID's to strings
"""

import os
from copy import copy

MIN_WORD_LEN = 3
VOCAB_FREQ_THRESHOLD = 10
CONTEXT_WINDOW_SIZE = 3


class DefaultCorpus:
    """
    Class to represent a corpus of word usages
    """
    def __init__(self, lemmas, usages_dir, stopwords):
        """
        :param lemmas: list of lemmas whose usages make up corpus
        :param usages_dir: directory containing lemma usage files
        :param stopwords: set of stopwords
        """
        self.word_counts = {}

        # bow representations of documents, based on raw word strings
        self.doc_bows = []
        self.num_docs = 0

        # mappings from lemmas to docs, and vice versa
        self.lemma_docs = {}
        self.doc_lemmas = []

        # vocab bow representation of documents, where words are represented
        # by their ID in vocabulary, along with mapping from word-id to word
        # string, and vice versa
        self.vocab_bows = []
        self.vocab_size = 0
        self.vocab_list = []
        self.vocab_dict = {}
        self.vocab_up_to_date = False

        # minimum frequency of word in corpus for
        # it to be counted in vocabulary
        self.min_vocab_freq = VOCAB_FREQ_THRESHOLD + 1

        # list of all available lemmas in corpus (not necessarily all scanned
        # into this object)
        self.all_lemmas = lemmas

        self.stopwords = set()
        for w in stopwords:
            self.stopwords.add(w)
        self.corpus_dir = usages_dir

    def scan_lemma_usages(self, lemma):
        """
        parse usages file for given lemma, and populate this corpus

        :param lemma: lemma to obtain usages for
        :return: None
        """
        target_word = lemma.split(".")[0]
        usages_path = os.path.join(self.corpus_dir, lemma + ".txt")
        usages_fp = open(usages_path, 'r')

        for doc_num, line in enumerate(usages_fp.xreadlines()):
            line_array = []
            target_word_loc = int(line.split()[0])
            target_word_i = None
            tokens = line.split()[1:]
            # scan through tokens in line
            for i in range(len(tokens)):
                if i == target_word_loc:
                    target_word_i = len(line_array)
                t = tokens[i]
                # follow identical procedure as used by Lau et al.
                if (len(t) >= MIN_WORD_LEN) and (t not in self.stopwords):
                    if (i > 0) and (tokens[i-1] == "#") and t != target_word:
                        t = tokens[i - 1] + t
                    line_array.append(t)
                    self._add_word(lemma, doc_num, t)

            # add positional word tokens
            for i in range(1, CONTEXT_WINDOW_SIZE + 1):
                if (target_word_i - i) >= 0:
                    # left context word
                    t = line_array[target_word_i - i]
                    if t.count("#") != 2:
                        self._add_word(lemma, doc_num, "%s_#%d" % (t, -i))
                if (target_word_i + i) < len(line_array):
                    # right context word
                    t = line_array[target_word_i + i]
                    if t.count("#") != 2:
                        self._add_word(lemma, doc_num, "%s_#%d" % (t, i))

        usages_fp.close()

    def get_available_lemmas(self):
        """
        obtain all available lemmas in corpus

        :return: list of lemmas
        """
        return copy(self.all_lemmas)

    def get_num_usages(self):
        """
        obtain the total number of usages (documents) stored in this corpus

        :return: total number of usages over all lemmas
        """
        return self.num_docs

    def get_num_usages_by_lemma(self, lemma):
        """
        obtain the number of word usages for a given lemma

        :param lemma: lemma to obtain number of usages for
        :return: number of usages
        """
        return len(self.lemma_docs[lemma])

    def get_doc_ids_by_lemma(self, lemma):
        """
        obtain list of all doc ID's which are usages of given lemma

        :param lemma: lemma to obtain usages ID's of
        :return: list of usage ID's
        """
        return copy(self.lemma_docs[lemma])

    def doc_id_to_lemma(self, doc_id):
        """
        maps a doc_id to the lemma it is a usage of

        :param doc_id: usage ID in this corpus
        :return: corresponding lemma (or None if usage ID is invalid)
        """
        try:
            return self.doc_lemmas[doc_id]
        except IndexError:
            return None

    def word_to_id(self, word):
        """
        map word string to ID

        :param word: string of word to map
        :return: ID of word (or None if word is outside vocabulary)
        """
        try:
            return self.vocab_dict[word]
        except KeyError:
            return None

    def id_to_word(self, word_id):
        """
        maps word ID to word string

        :param word_id: ID of word to map
        :return: word string
        """
        if (word_id >= 0) and (word_id < self.vocab_size):
            return self.vocab_list[word_id]
        else:
            return None

    def prepare_vocab(self):
        """
        Create required indexes for vocabulary

        :return: None
        """
        # re-set vocab fields to empty in-case they have been changed
        self.vocab_list = []
        self.vocab_size = 0
        self.vocab_dict = {}
        vocab_id = 0

        # scan through global count dictionary to enumerate vocabulary
        # Note: first vocab item is at index 0 in array, but has id 1
        for word, freq in self.word_counts.iteritems():
            # only include vocabulary above frequency threshold
            if freq < self.min_vocab_freq:
                continue
            self.vocab_list.append(word)
            self.vocab_size += 1
            self.vocab_dict[word] = vocab_id
            vocab_id += 1

        # build vocab BOWs
        self.vocab_bows = [None] * self.num_docs
        for doc, bow in enumerate(self.doc_bows):
            self.vocab_bows[doc] = {}
            vocab_bow = self.vocab_bows[doc]
            for word, count in bow.iteritems():
                word_id = self.word_to_id(word)
                if word_id is not None:
                    vocab_bow[word_id] = count
        # now up to date
        self.vocab_up_to_date = True

    def _add_word(self, lemma, lemma_usage_num, word):
        """
        adds word to corpus for given usage of given lemma

        :param lemma: corresponding lemma
        :param lemma_usage_num: corresponding usage number of lemma
        :param word: word to add
        :return: None
        """
        self.vocab_up_to_date = False

        # obtain list of doc_ids for this lemma
        try:
            lemma_docs = self.lemma_docs[lemma]
        except KeyError:
            self.lemma_docs[lemma] = []
            lemma_docs = self.lemma_docs[lemma]

        # obtain bow for this document, creating new one if needed
        if lemma_usage_num >= len(lemma_docs):
            # means new bag of words needed, update all relevant fields
            doc_num = self.num_docs
            lemma_docs.append(doc_num)
            self.doc_lemmas.append(lemma)
            self.num_docs += 1
            bow = {}
            self.doc_bows.append(bow)
        else:
            doc_num = lemma_docs[lemma_usage_num]
            bow = self.doc_bows[doc_num]

        # add word to bow
        try:
            bow[word] += 1
        except KeyError:
            bow[word] = 1

        # update global word counts
        try:
            self.word_counts[word] += 1
        except KeyError:
            self.word_counts[word] = 1

    def __iter__(self):
        """
        iterator for corpus; iterates over vocab BOW
        for documents in order (vocab BOW is a dict from token id
        to token frequency)
        """
        # prepare vocab if necessary
        # protect from race condition
        if not self.vocab_up_to_date:
            self.prepare_vocab()
        return UsageCorpusIterator(self.vocab_bows)


class UsageCorpusIterator:
    """
    Iterator class; used to iterate over the documents in
    a corpus instance
    """
    def __init__(self, vocab_bows):
        self.vocab_bows = vocab_bows
        self.i = 0

    def next(self):
        try:
            doc = self.i
            self.i += 1
            return self.vocab_bows[doc]
        except IndexError:
            raise StopIteration
