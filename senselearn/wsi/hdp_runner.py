"""
Created by: Andrew Bennett
Last updated: July, 2016

Class for running HDP-WSI
"""

from collections import defaultdict
from copy import copy
import os
import random
from timeit import timeit
import re

from senselearn.errors import ExperimentFail, WSIRepeat
from senselearn.wsi_operator import INPUT_PATH, OUTPUT_DIR, OUTPUT_PREFIX
from senselearn.wsi.default_runner import WSIRunner

STDOUT_SUFFIX = ".stdout"
STDERR_SUFFIX = ".stderr"

HDP_INPUT_PATH_KEY = "data"
HDP_OUTPUT_DIR_KEY = "directory"

EXE_PATH = "exe_path"
HDP_OPTION_DEFAULTS = {
    EXE_PATH: "topicmodelling/hdp/hdp",
    "algorithm": "train",
    "max_iter": "300",
    "save_lag": "-1",
    "gamma_b": "0.1",
    "alpha_b": "1.0"
}

SKIP_OPTIONS = (INPUT_PATH, OUTPUT_DIR, OUTPUT_PREFIX, EXE_PATH)

LIKELIHOOD_LINE_PATTERN = re.compile("^iter = .* likelihood = ")
NUM_WORDS_LINE_PATTERN = re.compile("^number of total words")


class HDPRunner(WSIRunner):
    """
    Class providing methods for running HDP-WSI
    """
    def __init__(self, corpus):
        """
        :param corpus: underlying DefaultCorpus object to run HDP-WSI over
        """
        WSIRunner.__init__(self, corpus)

    def run_wsi(self, supplied_hdp_options, all_num_usages=None):
        """
        Run HDP-WSI using supplied corpus

        :param supplied_hdp_options: WSIOptions object containing options for
            running HDP
        :param all_num_usages: dict containing number of usages to use for each
            lemma (if None, use all usages of all lemmas in corpus)
        :return: dict containing topic modelling output, along with other
            metadata
        """
        # check that required options are given (set to default values if not)
        hdp_options = copy(supplied_hdp_options)
        for option, default_value in HDP_OPTION_DEFAULTS.iteritems():
            if option not in hdp_options:
                hdp_options[option] = default_value

        # get components required
        hdp_exe_path = hdp_options[EXE_PATH]
        hdp_input_path = hdp_options[INPUT_PATH]
        hdp_output_dir = hdp_options[OUTPUT_DIR]
        hdp_output_prefix = hdp_options[OUTPUT_PREFIX]

        # add correct option keys for input path and output dir, for
        # running hdp
        hdp_options[HDP_INPUT_PATH_KEY] = hdp_input_path
        hdp_options[HDP_OUTPUT_DIR_KEY] = hdp_output_dir

        # get paths for stdout and stderr, and ensure paths are empty
        hdp_stdout_path = os.path.join(hdp_output_dir,
                                       hdp_output_prefix + STDOUT_SUFFIX)
        hdp_stderr_path = os.path.join(hdp_output_dir,
                                       hdp_output_prefix + STDERR_SUFFIX)
        if os.path.exists(hdp_stdout_path):
            raise ExperimentFail("Existing file at stdout path %s"
                                 % hdp_stdout_path)
        elif os.path.exists(hdp_stderr_path):
            raise ExperimentFail("Existing file at stderr path %s"
                                 % hdp_stderr_path)

        # create input for HDP
        if all_num_usages:
            usage_subset = self._subsample_lemma_usages(all_num_usages)
        else:
            usage_subset = None
        empty, non_empty = self._create_hdp_input(hdp_input_path, usage_subset)

        # build up argument list to execute
        hdp_option_list = [hdp_exe_path]
        for option_name, option_val in hdp_options.iteritems():
            # need to skip over some options
            if option_name not in SKIP_OPTIONS:
                hdp_option_list.append("--" + option_name)
                hdp_option_list.append(option_val)

        # run hdp, and save stdout in out_file
        # (this very complex setup is to obtain accurate running time)
        out_file = open(hdp_stdout_path, 'w')

        hdp_setup_str = "out_file = open('%s', 'w')\n" % hdp_stdout_path
        hdp_setup_str += "err_file = open('%s', 'w')\n" % hdp_stderr_path
        hdp_setup_str += "import subprocess"

        hdp_call_str = ("subprocess.call(%s, stdout=out_file, "
                        "stderr=err_file, shell=False)\n" %
                        str(hdp_option_list))
        hdp_call_str += "err_file.close()\n"
        hdp_call_str += "out_file.close()"

        # run hdp once, timing the process
        time_taken = timeit(stmt=hdp_call_str, setup=hdp_setup_str, number=1)
        out_file.close()

        return self._parse_hdp_wsi_results(hdp_output_dir, hdp_stdout_path,
                                           non_empty, time_taken)

    @staticmethod
    def _parse_likelihoods_file(likelihood_path):
        """
        Parses file containing likelihood values over HDP iterations

        :param likelihood_path: path to likelihoods file
        :return: list containing perplexity values
            (length = number of iterations)
        """
        perplexity_array = []
        fp = open(likelihood_path, 'r')
        # iterate over lines in file, extracting likelihood from all
        # lines matching pattern
        num_words = None
        for line in fp.readlines():
            if NUM_WORDS_LINE_PATTERN.match(line):
                tokens = line.split()
                num_words = int(tokens[-1])
            elif LIKELIHOOD_LINE_PATTERN.match(line):
                tokens = line.strip().split()
                likelihood = float(tokens[-1])
                perplexity = -1 * likelihood / num_words
                perplexity_array.append(perplexity)

        return perplexity_array

    def _subsample_lemma_usages(self, all_num_usages):
        """
        Sample set of lemma usages to run HDP on

        :param all_num_usages: dict mapping lemma to the number of usages to
            sample for that lemma
        :return: set of document ID's (with respect to underlying corpus)
            representing lemma usages to run HDP on
        """
        sampled_doc_ids = set()
        for lemma, num_usages in all_num_usages.iteritems():
            # for each lemma, sample a random set of usages of that lemma
            doc_ids = self.corpus.get_doc_ids_by_lemma(lemma)
            num_subsample = min(len(doc_ids), num_usages)
            for doc_id in random.sample(doc_ids, num_subsample):
                sampled_doc_ids.add(doc_id)
        return sampled_doc_ids

    def _create_hdp_input(self, hdp_input_path, doc_subset):
        """
        Creates input file running HDP

        :param hdp_input_path: path to save HDP input to
        :param doc_subset: set of document ID's from underlying corpus to use
            (if None, run HDP over all documents)
        :return: tuple containing ID's of documents that are empty and non-empty
            respectively (empty documents are not provided to HDP)
        """
        fp = open(hdp_input_path, 'w')
        empty_list = []
        non_empty_list = []

        for doc, bow in enumerate(self.corpus):
            if (doc_subset is not None) and (doc not in doc_subset):
                # skip if document is not in subset we are considering
                continue
            # skip empty documents
            num_unique_words = len(bow.keys())
            if num_unique_words == 0:
                empty_list.append(doc)
                continue
            # create string for current doc
            input_line = str(num_unique_words)
            for word, freq in bow.iteritems():
                input_line += " " + str(word) + ":" + str(freq)
            fp.write(input_line + "\n")
            non_empty_list.append(doc)

        fp.close()
        return empty_list, non_empty_list

    def _parse_hdp_wsi_results(self, hdp_output_dir, hdp_stdout_path,
                               non_empty, time_taken):
        """
        Parses results from HDP to create dictionary containing outputs

        :param hdp_output_dir: directory of HDP outputs
        :param hdp_stdout_path: path to stdout file from HDP (contains
            likelihoods)
        :param non_empty: list of non-empty document ID's HDP was run on
        :param time_taken: time taken to run HDP (stored as metadata)
        :return: dict containing HDP output and appropriate metadata
        """
        # obtain topic distributions
        topic_word_path = os.path.join(hdp_output_dir,
                                       "mode-topics.dat")
        if not os.path.exists(topic_word_path):
            raise WSIRepeat("HDP fail (no topics-word file created)")
        topic_word_counts = self._get_topic_word_counts(topic_word_path)

        # obtain document distributions
        doc_topics_path = os.path.join(hdp_output_dir,
                                       "mode-word-assignments.dat")
        if not os.path.exists(doc_topics_path):
            raise WSIRepeat("HDP fail (no docs-topic file created)")
        doc_topic_counts = self.get_doc_topic_counts(doc_topics_path, non_empty)

        return {
            "time": time_taken,
            "perplexity_array": self._parse_likelihoods_file(hdp_stdout_path),
            "topic_word_counts": topic_word_counts,
            "doc_topic_counts": doc_topic_counts,
        }

    def _get_topic_word_counts(self, topics_path):
        """
        Parses file containing topic-word counts

        :param topics_path: path to topic-word counts file
        :return: dict mapping topic-ID to dict containing word counts
        """

        def get_topic_str(t_):
            return "t_%02d" % t_

        topic_word_counts = defaultdict(dict)
        fp = open(topics_path, 'r')
        for topic_num, line in enumerate(fp.readlines()):
            topic_id = get_topic_str(topic_num)
            counts = map(int, line.strip().split())
            for word_id, count in enumerate(counts):
                if count > 0:
                    word = self.corpus.id_to_word(word_id)
                    topic_word_counts[topic_id][word] = count
        fp.close()
        return topic_word_counts

    @staticmethod
    def get_doc_topic_counts(word_assignments_path, non_empty_list):
        """
        Parses file containing doc-topic counts

        :param word_assignments_path: path to file containing doc-topic counts
        :param non_empty_list: list of non-empty document ID's HDP was run on
        :return: dict mapping doc-ID to dict containing topic counts
        """

        def get_doc_str(d_):
            return "d_%06d" % d_

        def get_topic_str(t_):
            return "t_%02d" % t_

        fp = open(word_assignments_path, 'r')
        doc_topic_counts = defaultdict(dict)
        for i, line in enumerate(fp.readlines()):
            # skip the first line
            if i == 0:
                continue
            # get doc-id for line
            tokens = line.strip().split()
            d = int(tokens[0])
            doc_id = get_doc_str(non_empty_list[d])
            topic = int(tokens[2])
            topic_id = get_topic_str(topic)
            # update count for this doc_id / topic combination
            try:
                doc_topic_counts[doc_id][topic_id] += 1
            except KeyError:
                doc_topic_counts[doc_id][topic_id] = 1
        fp.close()
        return doc_topic_counts
