"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides functions for obtaining WordNet gloss distributions
"""

import os
import subprocess
import re

from senselearn.errors import ExperimentFail
from senselearn.probability import Distribution

POS_MAP = {
    "n": "noun",
    "v": "verb",
    "a": "adj",
    "r": "adv",
}


def is_int(s):
    """
    decide whether string represents integer or not

    :param s: input string
    :return: boolean result
    """
    try:
        int(s)
        return True
    except ValueError:
        return False


def get_wordnet_gloss_dists(lemma, wn_version, stopwords, tools_dir):
    """
    Obtain gloss distributions for given lemma (general function for all
    languages)

    :param lemma: lemma to obtain gloss distributions for
    :param wn_version: version of WordNet to use (should be name of WordNet
        executable)
    :param stopwords: set of stopwords
    :param tools_dir: directory containing NLP tools
    :return: dist mapping sense ID to gloss distribution over words
        (each represented by a Distribution)
    """
    lang = lemma.split(".")[-1]
    if lang == "en":
        return get_en_gloss_dists(lemma, wn_version, stopwords, tools_dir)
    else:
        raise ExperimentFail("language %s not implemented" % lang)


def get_en_gloss_dists(lemma, wn_version, stopwords, tools_dir):
    """
    Obtain English sense gloss distributions based on Princeton Wordnet

    :param lemma: lemma to obtain gloss distributions for
    :param wn_version: version of WordNet to use (should be name of WordNet
        executable)
    :param stopwords: set of stopwords
    :param tools_dir: directory containing NLP tools
    :return: dist mapping sense ID to gloss distribution over words
        (each represented by a Distribution)
    """
    pos = lemma.split(".")[-2]
    lemma_base = ".".join(lemma.split(".")[:-2])

    wn = os.path.join(tools_dir, "wn_bin", wn_version)
    if not os.path.exists(wn):
        raise ExperimentFail("wordnet path empty (%s)" % wn)
    open_nlp = os.path.join(tools_dir, "opennlp-tools-1.5.0", "bin", "opennlp")
    morpha = os.path.join(tools_dir, "morpha", "morpha")
    tokenizer_model = os.path.join(tools_dir, "opennlp-tools-1.5.0",
                                   "models", "en-token.bin")
    pos_tag_model = os.path.join(tools_dir, "opennlp-tools-1.5.0",
                                 "models", "en-pos-maxent.bin")
    morpha_verb_stems = os.path.join(tools_dir, "morpha", "verbstem.list")
    morpha_post_correct = os.path.join(tools_dir, "morpha",
                                       "morph-post-correct.prl")

    command = """%s "%s" -over""" % (wn, lemma_base)
    command += " | %s TokenizerME %s 2> /dev/null" % (open_nlp, tokenizer_model)
    command += " | %s POSTagger %s 2> /dev/null" % (open_nlp, pos_tag_model)
    command += " | %s -tf %s" % (morpha, morpha_verb_stems)
    command += " | %s" % morpha_post_correct
    p = subprocess.Popen(command, stdout=subprocess.PIPE,
                         shell=True, executable='/bin/bash')

    # process gloss input to produce distribution
    sense_gloss_dists = {}
    start_pattern = re.compile("^the %s .* have [0-9]+ sens.*" % POS_MAP[pos])
    start_parsing = False
    num_skip = 0
    wn_out = p.stdout.read().strip()
    if not wn_out:
        raise ExperimentFail("Error in running wordnet!")
    for line in wn_out.split("\n"):
        data = ["_".join(item.split("_")[:-1]) for item in line.split()]
        if start_pattern.match(" ".join(data)):
            start_parsing = True
            num_skip = 1

        elif start_parsing and num_skip > 0:
            num_skip -= 1

        elif start_parsing and line.strip() == "":
            start_parsing = False

        elif start_parsing:
            sense_id = 0
            gloss_dist = Distribution()
            for i, word_pos in enumerate(line.split()):
                break_id = word_pos.rfind("_")
                word = word_pos[:break_id].lower()
                if i == 0:
                    sense_id = int(word.strip("."))
                else:
                    word = word.strip("\"").strip("'").strip(")").strip("(")
                    if (word == lemma_base) or \
                       (len(word) < 3) or \
                       (word in stopwords) or \
                       (i < 4 and is_int(word)):
                        continue
                    else:
                        gloss_dist[word] += 1

            sense_name = "%s.%02d" % (lemma, sense_id)
            sense_gloss_dists[sense_name] = gloss_dist

    return sense_gloss_dists
