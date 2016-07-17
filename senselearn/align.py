"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides class for aligning topic modelling output to sense inventory
given sense glosses
"""

from senselearn.probability import Distribution, js_divergence


class TopicSenseAligner:
    """
    Class providing methods for performing topic--sense alignment
    """
    def __init__(self):
        self.all_gloss_dists = {}

    def add_lemma_gloss_dists(self, lemma, dic_sense_dist):
        """
        adds sense distributions over words based on sense glosses for given
        lemma

        :param lemma: lemma to add gloss distributions for
        :param dic_sense_dist: dict mapping sense id to distribution over words
            corresponding to sense gloss (represented by dict)
        :return: None
        """
        self.all_gloss_dists[lemma] = dic_sense_dist

    def do_alignment(self, topic_model, lemma):
        """
        performs topic-sense alignment, and returns sense distribution

        :param topic_model: dict containing topic modelling output
        :param lemma: lemma we are performing alignment for
        :return: sense distribution (represented by a Distribution)
        """
        # make topic-word distributions
        topic_word_dists = {}
        for t, word_counts in topic_model["topic_word_counts"].iteritems():
            topic_word_dists[t] = Distribution()
            topic_word_dists[t].update(word_counts)
            topic_word_dists[t].normalise_mutable()

        # make doc-topic distributions
        doc_topic_distributions = {}
        for d, topic_counts in topic_model["doc_topic_counts"].iteritems():
            doc_topic_distributions[d] = Distribution()
            doc_topic_distributions[d].update(topic_counts)
            doc_topic_distributions[d].normalise_mutable()

        # get dict mapping sense to distribution over words
        gloss_dists = self.all_gloss_dists[lemma]

        # produce overall distribution over topics (hard-assignment)
        topic_dist = self._produce_topic_dist_hard(doc_topic_distributions)

        # finally, do prevalence-score based alignment
        return self._prevalence_score_alignment(topic_dist, topic_word_dists,
                                                gloss_dists)

    @staticmethod
    def _produce_topic_dist_hard(doc_dists):
        """
        produces distribution over topics based on document distributions over
        topics, based on hard assignment (one topic per document)

        :param doc_dists: dict containing doc distributions over topics
        :return: distribution over topics (represented by Distribution)
        """
        # get un-normalised distribution over topics
        result = Distribution()
        for doc_distribution in doc_dists.values():
            # hard assignment
            mode_topic = doc_distribution.mode(min_tie_break=True)
            result[mode_topic] += 1.0
        result.normalise_mutable()
        return result

    @staticmethod
    def _prevalence_score_alignment(topic_dist, topic_word_dists, gloss_dists):
        """
        performs the topic-sense alignment, and returns distribution over senses

        :param topic_dist: distribution over topics (based on hard assignment)
        :param topic_word_dists: dict mapping topic id to topic distribution
            over words
        :param gloss_dists: dict mapping sense id to gloss distribution over
            words
        :return: distribution over senses (represented by a Distribution)
        """
        # iterate over every combination of sense/topic to calculate
        # un-normalised distribution
        ws_dist = Distribution()
        for topic, topic_dist_over_words in topic_word_dists.iteritems():
            topic_prob = topic_dist[topic]
            for sense, sense_dist_over_words in gloss_dists.iteritems():
                # obtain js-divergence between distributions
                jsd = js_divergence(sense_dist_over_words,
                                    topic_dist_over_words)
                ws_dist[sense] += (1 - jsd) * topic_prob

        if sum(ws_dist.values()) < 0.00001:
            try:
                first_sense = min(ws_dist.keys())
                ws_dist[first_sense] = 1.0
            except:
                return Distribution()
        return ws_dist.normalise_immutable()
