"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides functions/classes for running WSI (either HDP-WSI or HCA-WSI)
"""

import os
from copy import copy

from senselearn.errors import ExperimentFail


INPUT_PATH = "input_path"
OUTPUT_DIR = "output_dir"
OUTPUT_PREFIX = "output_prefix"
WSI_REQUIRED_OPTIONS = (INPUT_PATH, OUTPUT_DIR, OUTPUT_PREFIX)


class WSIOptions(dict):
    """
    Class for encapsulating options for configuring WSI
    """
    def __init__(self, output_dir=None, input_path=None, output_prefix=None):
        """
        :param output_dir: base directory for saving WSI output
        :param input_path: path to input file for WSI (ldac file)
        :param output_prefix: prefix to use in WSI output files, if needed
        """
        # first line is to shut type checker up...
        assert isinstance(self, dict)
        dict.__init__(self)
        self[OUTPUT_DIR] = output_dir
        self[INPUT_PATH] = input_path
        self[OUTPUT_PREFIX] = output_prefix


class WSIOperator:
    """
    Class providing high level interface for setting up and running
    a generic WSI algorithm (HDP-WSI or HCA-WSI), and evaluating results
    """
    def __init__(self, corpus, wsi_runner):
        """
        :param corpus: DefaultCorpus object to run WSI over
        :param wsi_runner: either a HCARunner or HDPRunner object
        """
        self.corpus = corpus
        self.wsi_runner = wsi_runner
        self.default_options = WSIOptions()

    def set_default_wsi_options(self, wsi_options):
        """
        sets default options for running TM-WSI

        :param wsi_options: WSIOptions object
        :return: None
        """
        self.default_options = WSIOptions()
        for option_name, option_value in wsi_options.iteritems():
            self.default_options[option_name] = option_value

    def run_wsi(self, supplied_wsi_options, all_num_usages=None):
        """
        runs WSI, by making calls to underlying WSIRunner object

        :param supplied_wsi_options: provided WSI options to override default
            options of this class
        :param all_num_usages: dict supplying number of usages to run TM-WSI on
            for each lemma (if None, run on all usages in corpus)
        :return: dict containing topic modelling output from underlying TM-WSI
            algorithm
        """
        # first set un-chosen options to defaults
        wsi_options = copy(supplied_wsi_options)
        for option_key, option_value in self.default_options.iteritems():
            if option_key not in wsi_options:
                wsi_options[option_key] = option_value

        # make sure vital options are set
        if wsi_options[INPUT_PATH] is None:
            raise ExperimentFail("No hdp input path set")
        elif wsi_options[OUTPUT_DIR] is None:
            raise ExperimentFail("No hdp output directory set")
        elif wsi_options[OUTPUT_PREFIX] is None:
            raise ExperimentFail("No output prefix for WSI provided")

        # create input / output directories if needed, and check paths
        # that there is no conflict
        input_path = wsi_options[INPUT_PATH]
        input_dir = os.path.dirname(input_path)
        if os.path.exists(input_path):
            raise ExperimentFail("Existing file at input path %s" % input_path)
        elif not os.path.isdir(input_dir):
            try:
                os.makedirs(input_dir)
            except OSError:
                raise ExperimentFail("Conflict from existing file(s) when "
                                     "creating input directory %s" % input_dir)

        output_dir = wsi_options[OUTPUT_DIR]
        if not os.path.isdir(output_dir):
            try:
                os.makedirs(output_dir)
            except OSError:
                raise ExperimentFail("Conflict from existing file(s) when "
                                     "creating output directory %s"
                                     % output_dir)

        # actually run wsi with given options
        return self.wsi_runner.run_wsi(wsi_options, all_num_usages)
