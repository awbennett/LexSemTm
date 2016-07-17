"""
Created by: Andrew Bennett
Last updated: July, 2016

Script for creating gold-standard sense distributions file based on directory
containing lemma usages with gold-standard sense annotations
"""

import argparse
from collections import Counter
import csv
import os


def main():
    """
    Main function for running script

    :return: None
    """
    desc = "Create gold standard distributions file from sense annotations"
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--annotations_dir", required=True,
                        help="directory containing sense annotations")
    parser.add_argument("--save_path", required=True,
                        help="path to save gold standard distributions")
    args = parser.parse_args()

    # load gold standard distributions
    annotations_dir = args.annotations_dir
    gold_dists = {}
    for fname in os.listdir(annotations_dir):
        path = os.path.join(annotations_dir, fname)
        fp = open(path, 'r')
        reader = csv.DictReader(fp)
        sense_counts = Counter([row["sense_id"] for row in reader])
        lemma = ".".join(fname.split(".")[:-1])
        gold_dists[lemma] = {sense: count for sense, count
                             in sense_counts.iteritems()}
        fp.close()

    # save to output file
    save_fp = open(args.save_path, 'w')
    for lemma, gold_dist in sorted(gold_dists.iteritems()):
        for sense_id, freq in sorted(gold_dist.iteritems()):
            save_fp.write("%s %d\n" % (sense_id, freq))
        save_fp.write("\n")
    save_fp.close()


if __name__ == "__main__":
    main()
