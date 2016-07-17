"""
Created by: Andrew Bennett
Last updated: July, 2016

Class for running HCA-WSI
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

WSI_INPUT_PATH_KEY = "data"
WSI_OUTPUT_DIR_KEY = "directory"

EXE_PATH = "exe_path"
HCA_OPTION_DEFAULTS = {
    EXE_PATH: "topicmodelling/HCA-0.61/hca/hca",
    "C": "300",
    "K": "10",
    "N200000,20000": None,
}

SKIP_OPTIONS = (INPUT_PATH, OUTPUT_DIR, OUTPUT_PREFIX, EXE_PATH,
                WSI_INPUT_PATH_KEY, WSI_OUTPUT_DIR_KEY)

DEFAULT = "default"

# output suffixes
TOPIC_WORD_SUFFIX = ".nwt"
DOC_TOPIC_SUFFIX = ".ndt"

# number of lines to skip in each file type
TOPICS_LINE_SKIP_NUM = 3
DOC_LINE_SKIP_NUMBER = 3

# patterns for parsing likelihood file
LIKELIHOOD_LINE_PATTERN = re.compile("log_2\(perp\)=.*")

# cycles per line in likelihood file
LIKELIHOOD_CHANGE_RATE = 5


class HCARunner(WSIRunner):
    """
    Class providing methods for running HCA-WSI
    """
    def __init__(self, corpus):
        """
        :param corpus: underlying DefaultCorpus object to run HCA-WSI over
        """
        WSIRunner.__init__(self, corpus)

    def run_wsi(self, supplied_options, all_num_usages=None):
        """
        Run HCA-WSI using supplied corpus

        :param supplied_options: WSIOptions object containing options for
            running HCA
        :param all_num_usages: dict containing number of usages to use for each
            lemma (if None, use all usages of all lemmas in corpus)
        :return: dict containing topic modelling output, along with other
            metadata
        """
        # check that required options are given (set to default values if not)
        wsi_options = copy(supplied_options)
        for option, default_value in HCA_OPTION_DEFAULTS.iteritems():
            if option not in wsi_options:
                wsi_options[option] = default_value

        # get components required
        wsi_exe_path = wsi_options[EXE_PATH]
        wsi_input_path = wsi_options[INPUT_PATH]
        wsi_output_dir = wsi_options[OUTPUT_DIR]
        wsi_output_prefix = wsi_options[OUTPUT_PREFIX]

        # add correct option keys for input path and output dir, for
        # running hca
        wsi_options[WSI_INPUT_PATH_KEY] = wsi_input_path
        wsi_options[WSI_OUTPUT_DIR_KEY] = wsi_output_dir

        # get paths for stdout and stderr, and ensure paths are empty
        wsi_stdout_path = os.path.join(wsi_output_dir,
                                       wsi_output_prefix + STDOUT_SUFFIX)
        wsi_stderr_path = os.path.join(wsi_output_dir,
                                       wsi_output_prefix + STDERR_SUFFIX)
        wsi_output_stem = os.path.join(wsi_output_dir,
                                       wsi_output_prefix)
        if os.path.exists(wsi_stdout_path):
            raise ExperimentFail("Existing file at stdout path %s"
                                 % wsi_stdout_path)
        elif os.path.exists(wsi_stderr_path):
            raise ExperimentFail("Existing file at stderr path %s"
                                 % wsi_stderr_path)

        # create input for HCA
        if all_num_usages:
            usage_subset = self._subsample_lemma_usages(all_num_usages)
        else:
            usage_subset = None
        empty, non_empty = self._create_hca_input(wsi_input_path, usage_subset)

        # build up argument list to execute
        hca_option_list = [wsi_exe_path, "-e"]
        for option_name, option_val in wsi_options.iteritems():
            # need to skip over some options
            if option_name not in SKIP_OPTIONS:
                hca_option_list.append("-" + option_name)
                if option_val:
                    hca_option_list.append(option_val)
        # add input stem and output stem options
        hca_option_list.append(".".join(wsi_input_path.split(".")[:-1]))
        hca_option_list.append(wsi_output_stem)

        # run hca, and save stdout in out_file
        # (this very complex setup is to obtain accurate running time)
        out_file = open(wsi_stdout_path, 'w')

        wsi_setup_str = "out_file = open('%s', 'w')\n" % wsi_stdout_path
        wsi_setup_str += "err_file = open('%s', 'w')\n" % wsi_stderr_path
        wsi_setup_str += "import subprocess"

        wsi_call_str = ("subprocess.call(%s, stdout=out_file, "
                        "stderr=err_file, shell=False)\n" %
                        str(hca_option_list))
        wsi_call_str += "err_file.close()\n"
        wsi_call_str += "out_file.close()"

        # run hca once, timing the process
        time_taken = timeit(stmt=wsi_call_str, setup=wsi_setup_str, number=1)
        out_file.close()

        return self._parse_hca_results(wsi_output_stem, wsi_stderr_path,
                                      non_empty, time_taken)

    @staticmethod
    def _parse_perplexity_file(perplexity_path):
        """
        Parses file containing perplexity values over HCA iterations

        :param perplexity_path: path to perplexity file
        :return: list containing perplexity values
            (length = number of iterations)
        """
        fp = open(perplexity_path, 'r')
        likelihood_array = []
        for line in fp.xreadlines():
            line = line.strip()
            # start of new cycles set
            if LIKELIHOOD_LINE_PATTERN.match(line):
                likelihood = float(line.split("=")[1].split(",")[0])
                for _ in range(LIKELIHOOD_CHANGE_RATE):
                    likelihood_array.append(likelihood)
        return likelihood_array

    def _subsample_lemma_usages(self, all_num_usages):
        """
        Sample set of lemma usages to run HCA on

        :param all_num_usages: dict mapping lemma to the number of usages to
            sample for that lemma
        :return: set of document ID's (with respect to underlying corpus)
            representing lemma usages to run HCA on
        """
        sampled_doc_ids = set()
        for lemma, num_usages in all_num_usages.iteritems():
            # for each lemma, sample a random set of usages of that lemma
            doc_ids = self.corpus.get_doc_ids_by_lemma(lemma)
            num_subsample = min(len(doc_ids), num_usages)
            for doc_id in random.sample(doc_ids, num_subsample):
                sampled_doc_ids.add(doc_id)
        return sampled_doc_ids

    def _create_hca_input(self, hca_input_path, doc_subset):
        """
        Creates input file running HCA

        :param hca_input_path: path to save HCA input to
        :param doc_subset: set of document ID's from underlying corpus to use
            (if None, run HCA over all documents)
        :return: tuple containing ID's of documents that are empty and non-empty
            respectively (empty documents are not provided to HCA)
        """
        empty_list = []
        non_empty_list = []
        fp = open(hca_input_path, 'w')

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

    def _parse_hca_results(self, wsi_output_stem, hca_stderr_path,
                           non_empty, time_taken):
        """
        Parses results from HCA to create dictionary containing outputs

        :param wsi_output_stem: prefix of HCA output paths
        :param hca_stderr_path: path to stderr file from HCA (contains
            perplexity values)
        :param non_empty: list of non-empty document ID's HCA was run on
        :param time_taken: time taken to run HCA (stored as metadata)
        :return: dict containing HCA output and appropriate metadata
        """
        # obtain topic distributions
        topic_words_path = wsi_output_stem + TOPIC_WORD_SUFFIX
        if not os.path.exists(topic_words_path):
            raise WSIRepeat("HCA fail (no topics-word file created)")
        topic_word_counts = self._get_topic_word_counts(topic_words_path)

        # obtain document distributions
        docs_topic_path = wsi_output_stem + DOC_TOPIC_SUFFIX
        if not os.path.exists(docs_topic_path):
            raise WSIRepeat("HCA fail (no docs-topic file created)")
        doc_topic_counts = self._get_doc_topic_counts(docs_topic_path, non_empty)

        return {
            "time": time_taken,
            "perplexity_array": self._parse_perplexity_file(hca_stderr_path),
            "topic_word_counts": topic_word_counts,
            "doc_topic_counts": doc_topic_counts,
        }

    def _get_topic_word_counts(self, topic_word_assignment_path):
        """
        Parses file containing topic-word counts

        :param topic_word_assignment_path: path to topic-word counts file
        :return: dict mapping topic-ID to dict containing word counts
        """

        def get_topic_str(t_):
            return "t_%02d" % t_

        fp = open(topic_word_assignment_path, 'r')
        lines = fp.xreadlines()
        topic_word_counts = defaultdict(dict)
        for _ in range(TOPICS_LINE_SKIP_NUM):
            lines.next()

        # read in all topic-word frequency data
        for line in lines:
            word_id, topic, count = map(int, line.strip().split())
            word = self.corpus.id_to_word(word_id)
            topic_id = get_topic_str(topic)
            topic_word_counts[topic_id][word] = count
        fp.close()
        return topic_word_counts

    @staticmethod
    def _get_doc_topic_counts(doc_word_assignment_path, non_empty_list):
        """
        Parses file containing doc-topic counts

        :param doc_word_assignment_path: path to file containing
            doc-topic counts
        :param non_empty_list: list of non-empty document ID's HCA was run on
        :return: dict mapping doc-ID to dict containing topic counts
        """

        def get_doc_str(d_):
            return "d_%06d" % d_

        def get_topic_str(t_):
            return "t_%02d" % t_

        fp = open(doc_word_assignment_path, 'r')
        lines = fp.xreadlines()
        doc_topic_counts = defaultdict(dict)
        for _ in range(DOC_LINE_SKIP_NUMBER):
            lines.next()

        # obtain doc distributions for all non-empty documents
        for line in lines:
            d, topic, count = map(int, line.strip().split())
            doc_id = get_doc_str(non_empty_list[d])
            topic_id = get_topic_str(topic)
            doc_topic_counts[doc_id][topic_id] = count
        fp.close()
        return doc_topic_counts
