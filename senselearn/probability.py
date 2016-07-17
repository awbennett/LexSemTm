"""
Created by: Andrew Bennett
Last updated: July, 2016

Provides classes and functions implementing probability-related calculations
"""

from collections import defaultdict
from math import log


def js_divergence(dist1, dist2):
    """
    Calculates JS-divergence between 2 distributions

    :param dist1: first distribution (of type dict or Distribution)
    :param dist2: second distribution (of type dict or Distribution)
    :return: JS divergence
    """
    d1 = Distribution.make_normalised_dist(dist1)
    d2 = Distribution.make_normalised_dist(dist2)
    dist_avg = (d1 + d2) / 2
    return 0.5 * (kl_divergence(d1, dist_avg)
                  + kl_divergence(d2, dist_avg))


def kl_divergence(dist1, dist2):
    """
    Calculates KL-divergence between 2 distributions

    :param dist1: first distribution (of type dict or Distribution)
    :param dist2: second distribution (of type dict or Distribution)
    :return: KL divergence
    """
    d1 = Distribution.make_normalised_dist(dist1)
    d2 = Distribution.make_normalised_dist(dist2)
    kld = 0
    for k, v1 in d1.iteritems():
        # skip elements with value zero (they do not contribute)
        if v1 > 0.0:
            v2 = d2[k]
            kld += v1 * log((v1 / v2), 2)
    return kld


def average_distributions(distribution_list):
    """
    averages all distributions in a given list

    :param distribution_list: list of distributions,
        each is of type Distribution
    :return: average distribution (of type Distribution)
    """
    sum_dists = Distribution()
    for distribution in distribution_list:
        assert isinstance(distribution, Distribution)
        sum_dists += distribution.normalise_immutable()
    sum_dists.normalise_mutable()
    return sum_dists


class Distribution(defaultdict):
    """
    Class representing a probability distribution
    """
    def __init__(self):
        defaultdict.__init__(self, float)
        self.is_normalised = False

    def __setitem__(self, key, value):
        """
        called when the value of some item in dictionary is set
        make sure dict is now un-normalised after this happens
        """
        defaultdict.__setitem__(self, key, value)
        self.is_normalised = False

    def __add__(self, other):
        """
        :param other: other distribution to be added to this one
        """
        result = Distribution()
        for key, prob in self.iteritems():
            result[key] += prob
        for key, prob in other.iteritems():
            result[key] += prob
        return result

    def __mul__(self, other):
        """
        :param other: scalar to multiple distribution by
        """
        result = Distribution()
        for key, prob in self.iteritems():
            result[key] = prob * other
        return result

    def __div__(self, other):
        """
        :param other: scalar to divide distribution by
        """
        result = Distribution()
        denominator = float(other)
        for key, prob in self.iteritems():
            result[key] = prob / denominator
        return result

    def __str__(self):
        print_str = ""
        if not self.keys():
            return print_str
        max_key_len = max(len(str(k)) for k in self.iterkeys())
        for k, prob in sorted(self.iteritems()):
            if max_key_len > 0:
                print_str += ("%" + str(max_key_len) + "s: ") % k
            else:
                print_str += "%s: " % k
            print_str += str(prob) + "\n"
        return print_str.rstrip()

    def normalise_immutable(self):
        """
        normalises distribution, so that probs add up to one
        returns new distribution with normalised values

        immutable version (returns a new Distribution, does not alter
        input one)

        :return: normalised distribution
        """
        if self.is_normalised:
            # if already normalised, just make simple copy of self
            new_dist = Distribution()
            for key, prob in self.iteritems():
                new_dist[key] = prob
        else:
            values_sum = float(sum(self.values()))
            new_dist = self / values_sum

        new_dist.is_normalised = True
        return new_dist

    def normalise_mutable(self):
        """
        normalises distribution, so that probs add up to one
        returns new distribution with normalised values

        mutable version (returns nothing, edits self in-place)

        :return: None
        """
        if self.is_normalised:
            # if already normalised, do nothing
            return
        else:
            values_sum = float(sum(self.values()))
            for key, prob in self.iteritems():
                self[key] = prob / values_sum
            self.is_normalised = True

    def mode(self, min_tie_break=False):
        """
        obtains the mode of this distribution

        :param min_tie_break: whether or not to tie-break by choosing minimum
            key (if False instead chooses arbitrary key)
        :return: the mode (key with greatest probability)
        """
        if min_tie_break:
            return max(sorted(self.keys()), key=self.get)
        else:
            return max(self.keys(), key=self.get)

    def get_entropy(self):
        """
        obtains entropy of distribution (normalising first if necessary)

        :return: entropy of distribution
        """
        if not self.is_normalised:
            self.normalise_mutable()
        return -sum(p * log(p, 2) for p in self.itervalues() if p > 0.0)

    def exponential_rescale(self, k):
        """
        exponential rescaling of current distribution
        does not edit self, instead returns new distribution

        :param k: exponential rescaling parameter
        :return: rescaled Distribution
        """
        prob_sum = float(sum(self.values()))
        new_dist = Distribution()
        for key, prob in self.iteritems():
            if prob > 0.0:
                new_dist[key] = (prob / prob_sum) ** k
            else:
                new_dist[key] = 0.0
        new_dist.normalise_mutable()
        return new_dist

    @staticmethod
    def make_normalised_dist(d):
        """
        create normalised Distribution from input which can be either a
        Distribution or a dictionary

        :param d: dict or Distribution to create normalised Distribution from
        :return: normalised Distribution
        """
        if isinstance(d, Distribution):
            return d.normalise_immutable()
        else:
            new_d = Distribution()
            new_d.update(d)
            new_d.normalise_mutable()
            return new_d