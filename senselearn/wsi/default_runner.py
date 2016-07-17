"""
Created by: Andrew Bennett
Last updated: July, 2016

Superclass for running TM-WSI (either HDP-WSI or HCA-WSI)
"""

class WSIRunner:
    def __init__(self, corpus):
        """
        :param corpus: DefaultCorpus object to run WSI over
        """
        self.corpus = corpus

    def run_wsi(self, supplied_wsi_options, all_num_usages=None):
        """
        Run TM-WSI using supplied corpus

        :param supplied_wsi_options: WSIOptions object containing options for
            running HCA or HDP
        :param all_num_usages: dict containing number of usages to use for each
            lemma (if None, use all usages of all lemmas in corpus)
        :return: dict containing topic modelling output, along with other
            metadata
        """
        raise NotImplementedError()
