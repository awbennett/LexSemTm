"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides class for accessing LexSemTM
"""

import csv
import json
import os
import subprocess

DEBUG = True

def get_reader(lexsemtm_path):
    """
    Obtain LexSemTMReader object

    :param lexsemtm_path: directory containing LexSemTM data and index files
    :return: LexSemTMReader object
    """
    return LexSemTMReader(lexsemtm_path)


class LexSemTMReader:
    """
    Class for accessing LexSemTM
    """
    def __init__(self, lexsemtm_dir):
        """
        :param lexsemtm_dir: directory containing LexSemTM data and index files
        """
        self.lexsemtm_dir = lexsemtm_dir
        self.all_lemmas = {}
        self.all_lemma_indices = {}
        self.all_lemma_freqs = {}
        self.all_sense_dists = {}
        self.all_topic_models = {}
        self.vocab_lists = {}

    def get_lemma_names(self, lang="en", which_version="s"):
        """
        Obtain list of lemma names in LexSemTM

        :param lang: which language to obtain lemmas from (default: "en")
        :param which_version: which version of LexSemTM to obtain lemmas from
            (default: "s")
        :return: list of lemma names
        """
        key = (lang, which_version)
        if key not in self.all_lemmas:
            self._load_lemma_info_file(lang, which_version)
        return self.all_lemmas[key]

    def get_lemma_freq(self, lemma, lang="en", which_version="s"):
        """
        Obtain number of usages of given lemma used to train LexSemTM topic
        model (i.e. frequency of lemma in LexSemTM)

        :param lemma: lemma to obtain frequency of
        :param lang: which language lemma belongs to (default: "en")
        :param which_version: which version of LexSemTM lemma belongs to
            (default: "s")
        :return: frequency of lemma
        """
        key = (lang, which_version)
        if key not in self.all_lemma_freqs:
            self._load_lemma_info_file(lang, which_version)
        return self.all_lemma_freqs[key][lemma]

    def get_sense_dist(self, lemma, lang="en", which_version="s"):
        """
        Obtain LexSemTM sense distribution for given lemma

        :param lemma: lemma to obtain sense distribution of
        :param lang: which language lemma belongs to (default: "en")
        :param which_version: which version of LexSemTM lemma belongs to
            (default: "s")
        :return: sense distribution (of type dict, mapping sense name
            to probability)
        """
        key = (lang, which_version)
        if key not in self.all_sense_dists:
            self._load_all_sense_dists(lang, which_version)
        return self.all_sense_dists[key][lemma]

    def get_topic_model(self, lemma, lang="en", which_version="s"):
        """
        Obtain LexSemTM topic model for given lemma

        :param lemma: lemma to obtain topic model of
        :param lang: which language lemma belongs to (default: "en")
        :param which_version: which version of LexSemTM lemma belongs to
            (default: "s")
        :return: topic model output, consisting of dict containing
            doc-topic counts and topic-word counts
        """
        # extract topic model raw string from archive
        key = (lang, which_version)
        if key not in self.all_lemma_indices:
            self._load_lemma_info_file(lang, which_version)
        lemma_id = self.all_lemma_indices[key][lemma]
        tm_fname = "%s.%s.%08d.tm.json.gz" % (lang, which_version, lemma_id)
        tar_path = os.path.join(self.lexsemtm_dir, "%s.%s.data.tar" % key)
        extract_cmd_1 = ["tar", "-xOf", tar_path, tm_fname]
        extract_cmd_2 = ["gunzip"]
        p1 = subprocess.Popen(extract_cmd_1, stdout=subprocess.PIPE)
        p2 = subprocess.Popen(extract_cmd_2, stdout=subprocess.PIPE,
                              stdin=p1.stdout)
        tm_json_str = p2.stdout.read()

        # convert json string to usable tm object
        # (doc-topic counts and topic-word counts)
        try:
            tm_json = json.loads(tm_json_str)
        except ValueError:
            return tm_json_str
        if lang not in self.vocab_lists:
            self._load_vocab_file(lang)
        vocab_list = self.vocab_lists[lang]
        doc_topic_counts = {}
        for d, topic_counts in enumerate(tm_json["doc_topic_counts"]):
            doc_topic_counts["d_%06d" % d] = topic_counts
        topic_word_counts = {}
        for t, word_counts in tm_json["topic_word_counts"].iteritems():
            topic_word_counts[t] = {vocab_list[w]: c
                                    for w, c in zip(word_counts["word_ids"],
                                                    word_counts["counts"])}
        return {"doc_topic_counts": doc_topic_counts,
                "topic_word_counts": topic_word_counts}

    def _load_lemma_info_file(self, lang, which_version):
        """
        Load LexSemTM lemma metadata for given language/version combination

        :param lang: language from which to load metadata
        :param which_version: version of LexSemTM from which to load metadata
        :return: None
        """
        key = (lang, which_version)
        lemma_info_fname = "%s.%s.lemmas.tab" % key
        lemma_info_path = os.path.join(self.lexsemtm_dir, lemma_info_fname)
        fp = open(lemma_info_path)
        reader = csv.DictReader(fp, delimiter="\t", quoting=csv.QUOTE_NONE)
        self.all_lemma_indices[key] = {}
        self.all_lemma_freqs[key] = {}
        self.all_lemmas[key] = []
        for row in reader:
            lemma = row["lemma"]
            self.all_lemmas[key].append(lemma)
            self.all_lemma_indices[key][lemma] = int(row["lemma-id"])
            self.all_lemma_freqs[key][lemma] = int(row["num-usages"])
        fp.close()

    def _load_vocab_file(self, lang):
        """
        Load LexSemTM vocabulary index for given language

        :param lang: language from which to load vocabulary index
        :return: None
        """
        vocab_fname = "%s.vocab.tab" % lang
        vocab_path = os.path.join(self.lexsemtm_dir, vocab_fname)
        fp = open(vocab_path)
        reader = csv.DictReader(fp, delimiter="\t", quoting=csv.QUOTE_NONE)
        vocab_map = {}
        for row in reader:
            token_id = int(row["token-id"])
            token = row["token"]
            vocab_map[token_id] = token
        self.vocab_lists[lang] = vocab_map
        fp.close()

    def _load_all_sense_dists(self, lang, which_version):
        """
        Parse LexSemTM data file to obtain all sense distributions for given
        language/version combination

        :param lang: language form which to obtain sense distributions
        :param which_version: version of LexSemTM from which to load sense
            distributions
        :return: None
        """
        key = (lang, which_version)
        if key not in self.all_sense_dists:
            self.all_sense_dists[key] = {}
        sense_dists = self.all_sense_dists[key]
        tar_path = os.path.join(self.lexsemtm_dir, "%s.%s.data.tar" % key)
        sdist_pattern = "%s.%s.*.sdist.tab" % key
        extract_cmd = ["tar", "--wildcards", "-xOf", tar_path, sdist_pattern]
        p = subprocess.Popen(extract_cmd, stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE)
        while True:
            line = p.stdout.readline().strip()
            if not line:
                break
            sense_id, prob = line.split()
            if sense_id == "sense-name":
                continue
            lemma = ".".join(sense_id.split(".")[:-1])
            if lemma not in sense_dists:
                sense_dists[lemma] = {}
            sense_dists[lemma][sense_id] = float(prob)
