"""
Created by: Andrew Bennett
Last updated: July, 2016

Main script for running sense distribution learning experiments
"""

import gzip
import json
import random
import csv
import subprocess
import sys
import argparse
import os
import gc
import shutil
from multiprocessing import Lock, Queue, Process

from nltk.corpus import wordnet as wn

from senselearn.corpus import DefaultCorpus
from senselearn.wsi.hdp_runner import HDPRunner
from senselearn.align import TopicSenseAligner
from senselearn.wordnet_gloss import get_wordnet_gloss_dists
from senselearn.errors import WSIRepeat, ExperimentFail
from senselearn.wsi.hca_runner import HCARunner
from senselearn.wsi_operator import WSIOptions, WSIOperator
from senselearn.probability import js_divergence

MIN_BOOTSTRAPPING_SIZE = 500


def parse_wsi_options_file(options_file_path):
    """
    Parse file containing options for running HDP or HCA

    :param options_file_path: path to file containing HDP/HCA options
    :return: dictionary containing options
    """
    default_options = {}
    fp = open(options_file_path)
    for line in fp.readlines():
        line_parts = line.split()
        key = line_parts[0]
        if len(line_parts) > 1:
            val = " ".join(line_parts[1:])
        else:
            val = None
        default_options[key] = val
    return default_options


def load_gold_dists(gold_dists_file):
    """
    Parses file containing gold-standard sense distributions

    :param gold_dists_file: path to gold-standard sense distributions file
    :return: dictionary mapping lemma to gold-standard distribution (as a dict)
    """
    gold_dists = {}
    fp = open(gold_dists_file, 'r')
    for line in fp.xreadlines():
        parts = line.split()
        if len(parts) <= 1:
            continue
        sense = parts[0]
        freq = float(parts[1])
        lemma = ".".join(sense.split(".")[:-1])
        try:
            gold_dist = gold_dists[lemma]
        except KeyError:
            gold_dist = {}
            gold_dists[lemma] = gold_dist
        gold_dist[sense] = freq
    return gold_dists


def get_semcor_dist(lemma):
    """
    Obtain SemCor-based distribution for given lemma

    :param lemma: lemma to obtain SemCor-based distribution of
                  (e.g. "bank.n.en")
    :return: SemCor-based distribution (as a dict)
    """
    base_lemma = ".".join(lemma.split(".")[:-2])
    pos = lemma.split(".")[-2]
    synsets = wn.synsets(base_lemma, pos=pos)
    semcor_dist = {}
    total_count = 0
    for i, s in enumerate(synsets):
        sense_id = "%s.%02d" % (lemma, i + 1)
        try:
            count = sum(l.count() for l in s.lemmas if l.name == base_lemma)
        except TypeError:
            count = sum(l.count() for l in s.lemmas() if l.name() == base_lemma)
        total_count += count
        semcor_dist[sense_id] = count
    if total_count == 0:
        semcor_dist["%s.01" % lemma] = 1
    return semcor_dist


def get_stopwords(lang, stopwords_dir):
    """
    Obtain set of stopwords for given language

    :param lang: code of language to obtain stopwords for
    :param stopwords_dir: path to directory containing stopwords
    :return: set of stopwords
    """
    stopwords_fname = "stopwords.%s.txt" % lang
    stopwords_path = os.path.join(stopwords_dir, stopwords_fname)
    fp = open(stopwords_path)
    stopwords = {line.strip() for line in fp.xreadlines()}
    fp.close()
    return stopwords


def load_topic_model_json(tm_path):
    """
    Loads json file containing topic modelling output

    :param tm_path: Path to topic modelling json file
    :return: dict containing topic distributions over words, document
        distributions over topics, as well as other data (e.g. aligned
             sense distribution)
    """
    if tm_path.split(".")[-1] == "gz":
        tm_fp = gzip.open(tm_path)
    else:
        tm_fp = open(tm_path)
    tm_json = json.load(tm_fp)
    tm_fp.close()
    return tm_json


def dump_tm_json(tm_output, save_path):
    """
    Dump topic model structure into json file, and compress using gzip

    :param tm_output: dict containing topic modelling data
    :param save_path: path to save json object
    :return: None
    """
    tm_fp = open(save_path, 'w')
    json.dump(tm_output, tm_fp)
    tm_fp.close()
    gzip_json_cmd = ["gzip", save_path]
    p_gzip = subprocess.Popen(gzip_json_cmd, stdout=subprocess.PIPE)
    p_gzip.stdout.readlines()


def run_tm_wsi(lemma, tm_dir, tm, results_dir, corpus_dir, stopwords,
               write_lock, bootstrapping, model_num, aligner, wsi_options,
               keep_wsi_data):
    """
    Runs TM-WSI (HDP-WSI or HCA-WSI) on single lemma
    :param lemma: lemma to run TM-WSI on
    :param tm_dir: base directory containing topic modelling programs
    :param tm: topic modelling algorithm to use (either "hdp" or "hca")
    :param results_dir: base directory for storing results
    :param corpus_dir: directory containing lemma usages files
    :param stopwords: set of stopwords for lemma
    :param write_lock: lock to serialise writing of output
    :param bootstrapping: whether we are running bootstrapping experiment or
        not (boolean)
    :param model_num: index of model being run (from enumerating all models)
    :param aligner: aligner object for aligning topic modelling output to sense
        inventory (or None if alignment not being performed)
    :param wsi_options: options to supply to HDP or HCA
    :param keep_wsi_data: whether to keep intermediate WSI output (if False,
        intermediate output will be deleted)
    :return: None
    """
    write_lock.acquire()
    if model_num is None:
        print "processing lemma %s" % lemma
    else:
        print "processing lemma %s (model num %d)" % (lemma, model_num)
    sys.stdout.flush()
    write_lock.release()

    # run WSI on lemma
    corpus = DefaultCorpus(lemma, corpus_dir, stopwords)
    corpus.scan_lemma_usages(lemma)
    corpus.prepare_vocab()
    if tm == "hca":
        wsi_runner = HCARunner(corpus)
    elif tm == "hdp":
        wsi_runner = HDPRunner(corpus)
    else:
        raise ExperimentFail("invalid tm algorithm %s" % tm)
    if bootstrapping:
        upper = corpus.get_num_usages_by_lemma(lemma)
        lower = min(MIN_BOOTSTRAPPING_SIZE, upper)
        num_usages_dict = {lemma: random.randint(lower, upper)}
    else:
        num_usages_dict = None
    if model_num is None:
        model_name = lemma
    else:
        model_name = lemma + "_%06d" % model_num

    operator = WSIOperator(corpus, wsi_runner)
    operator.set_default_wsi_options(wsi_options)

    scratch_dir = os.path.join(results_dir, "scratch")
    output_dir = os.path.join(scratch_dir,
                              model_name + ".outdir")
    input_path = os.path.join(scratch_dir,
                              model_name + ".input.ldac")
    wsi_options = WSIOptions(output_dir=output_dir,
                             input_path=input_path,
                             output_prefix="wsi_output")
    if tm == "hca":
        wsi_options["exe_path"] = os.path.join(tm_dir, "HCA-0.61", "hca", "hca")
    else:
        wsi_options["exe_path"] = os.path.join(tm_dir, "hdp", "hdp")

    # run wsi once, and append results to generated data
    # keep trying until it succeeds (no WSIRepeat exception)
    tm = None
    while True:
        try:
            if bootstrapping:
                num_usages = num_usages_dict[lemma]
            else:
                num_usages = corpus.get_num_usages_by_lemma(lemma)
            write_lock.acquire()
            print("starting wsi for model %s --- %s  "
                  "(%d uses sampled)" % (model_name, lemma, num_usages))
            sys.stdout.flush()
            write_lock.release()
            tm = operator.run_wsi(wsi_options, all_num_usages=num_usages_dict)
            tm["lemma"] = lemma
            break
        except WSIRepeat as e:
            write_lock.acquire()
            sys.stderr.write("WSI repeat for lemma %s, due to "
                             "reason '%s'\n"
                             % (lemma, e.message))
            sys.stdout.flush()
            write_lock.release()
            # delete output_dir and input_path, before trying again
            os.remove(input_path)
            shutil.rmtree(output_dir)

    # do alignment to get sense dist if relevant
    if aligner:
        sense_dist = aligner.do_alignment(tm, lemma)
        tm["sense_dist"] = sense_dist

    # save json file
    tm_path = os.path.join(results_dir, "tm_output", model_name + ".tm.json")
    dump_tm_json(tm, tm_path)

    # clear corpus object and possibly other files and end
    if not keep_wsi_data:
        os.remove(input_path)
        shutil.rmtree(output_dir)
    del corpus
    gc.collect()
    write_lock.acquire()
    print "finished model %s" % model_name
    sys.stdout.flush()
    write_lock.release()


def run_process_worker(job_queue, results_dir, corpus_dir, wn_version,
                       tools_dir, tm, tm_dir, wsi_options, do_bootstrapping,
                       do_alignment, keep_wsi_data, write_lock):
    """
    Function for single sense distribution learning experiment worker

    :param job_queue: Queue of jobs to run
    :param results_dir: base directory for storing results
    :param corpus_dir: directory containing lemma usages files
    :param wn_version: version of WordNet to be used (name of WordNet
        executable)
    :param tools_dir: base directory containing NLP tools
    :param tm: topic modelling algorithm to use (either "hdp" or "hca")
    :param tm_dir: base directory containing topic modelling programs
    :param wsi_options: options to supply to HDP or HCA
    :param do_bootstrapping: whether are running bootstrapping experiment or
        not (boolean)
    :param do_alignment: whether to perform alignment or not (boolean)
    :param keep_wsi_data: whether to keep intermediate WSI output (if False,
        intermediate output will be deleted)
    :param write_lock: lock to serialise writing of output
    :return: None
    """
    all_stopwords = {}
    if do_alignment:
        aligner = TopicSenseAligner()
    else:
        aligner = None
    lemmas_done = set()
    # continuously obtain jobs, until all jobs done
    for lemma, model_num in iter(job_queue.get, "STOP"):
        lang = lemma.split(".")[-1]
        try:
            stopwords = all_stopwords[lang]
        except KeyError:
            stopwords = get_stopwords(lang, tools_dir)
            all_stopwords[lang] = stopwords
        # process the lemma
        try:
            # make aligner if necessary
            if do_alignment and lemma not in lemmas_done:
                gloss_dists = get_wordnet_gloss_dists(lemma, wn_version,
                                                      stopwords, tools_dir)
                aligner.add_lemma_gloss_dists(lemma, gloss_dists)
                lemmas_done.add(lemma)
            run_tm_wsi(lemma, tm_dir, tm, results_dir, corpus_dir, stopwords,
                       write_lock, do_bootstrapping, model_num, aligner,
                       wsi_options, keep_wsi_data)
        except ExperimentFail as e:
            # report error to error log
            write_lock.acquire()
            sys.stderr.write("Failure with lemma %s of type '%s' with message "
                             "'%s' occurred!\n\n" % (lemma, type(e).__name__,
                                                     e.message))
            write_lock.release()


def evaluate_results(tm_output_dir, save_path, gold_dists_file):
    """
    Evaluate results from sense distribution learning experiment (by producing
    csv file containing evaluation metrics)

    :param tm_output_dir: directory containing topic modeling json outputs from
        sense distribution learning experiment
    :param save_path: path to save evaluation results to
    :param gold_dists_file: path to file containing gold-standard sense
        distributions
    :return: None
    """
    gold_dists = load_gold_dists(gold_dists_file)
    all_results = []
    results_keys = ["lemma", "num_usages", "jsd", "semcor_jsd",
                    "final_perplexity", "time"]
    for fname in os.listdir(tm_output_dir):
        tm_path = os.path.join(tm_output_dir, fname)
        tm = load_topic_model_json(tm_path)
        lemma = tm["lemma"]
        results = {
            "lemma": lemma,
            "num_usages": len(tm["doc_topic_counts"]),
            "final_perplexity": tm["perplexity_array"][-1],
            "time": tm["time"],
        }
        if "sense_dist" in tm:
            sense_dist = tm["sense_dist"]
            semcor_dist = get_semcor_dist(lemma)
            try:
                gold_dist = gold_dists[lemma]
            except KeyError:
                sys.stderr.write("No gold standard distribution for "
                                 "lemma %s\n\n" % lemma)
                continue
            results["jsd"] = js_divergence(sense_dist, gold_dist)
            results["semcor_jsd"] = js_divergence(semcor_dist, gold_dist)
        else:
            results["jsd"] = ""
            results["semcor_jsd"] = ""
        all_results.append(results)

    all_results.sort(key=lambda r: [r[k] for k in results_keys])
    fp = open(save_path, 'w')
    writer = csv.DictWriter(fp, results_keys)
    writer.writeheader()
    writer.writerows(all_results)
    fp.close()


def main():
    """
    Main function for running script

    :return: None
    """
    desc = ("Script for running sense distribution learning experiments (see "
            "README for more detail on arguments)")
    parser = argparse.ArgumentParser(description=desc)
    parser.add_argument("--results_dir", required=True,
                        help="name of directory for storing outputs")
    parser.add_argument("--mode", choices=["train", "evaluate", "all"],
                        required=True,
                        help="which part of experiment to run - either just "
                             "train topic models, just evaluate results, "
                             "or both")
    parser.add_argument("--corpus_dir",
                        help="directory containing corpus files (required "
                             "for training only)")
    parser.add_argument("--tm_dir",
                        help="directory containing topicmodelling programs "
                             "(required for training only)")
    parser.add_argument("--tools_dir",
                        help="directory containing NLP tools (required "
                             "for training only)")
    parser.add_argument("--wsi_args_file",
                        help="path to file containing WSI options (required "
                             "for training only)")
    parser.add_argument("--lemmas_file",
                        help="file containing lemmas to process (required "
                             "for training only)")
    parser.add_argument("--experiment", choices=["default", "bootstrapping"],
                        help="which experiment kind to run - either default "
                             "experiment, or bootstrapping experiment "
                             "(required for training only)")
    parser.add_argument("--tm", choices=["hdp", "hca"],
                        help="topic modelling algorithm to use "
                             "(required for training only)")
    parser.add_argument("--wn_version",
                        help="version of WordNet to use for alignment (name "
                             "of executable - required for training only, and "
                             "only if performing alignment)")
    parser.add_argument("--gold_dist_file", default=None,
                        help="file containing gold-standard distributions "
                             "(required for evaluation only)")
    parser.add_argument("--bootstrap_size", type=int, default=10,
                        help="number of models per lemma "
                             "(only relevant for bootstrapping training)")
    parser.add_argument("--skip_alignment", action="store_true",
                        help="skip topic-sense alignment of HDP/WSI results "
                             "(only relevant for training)")
    parser.add_argument("--keep_wsi_data", action="store_true",
                        help="don't delete temporary WSI data generated "
                             "(only relevant for training)")
    parser.add_argument("--nprocs", type=int, default=1,
                        help="number of processes to run at once (only "
                             "relevant for training)")
    args = parser.parse_args()

    # create required directories
    results_dir = args.results_dir
    scratch_dir = os.path.join(results_dir, "scratch")
    tm_output_dir = os.path.join(results_dir, "tm_output")
    for d in (results_dir, scratch_dir, tm_output_dir):
        if not os.path.exists(d):
            os.makedirs(d)

    # extract other required arguments
    mode = args.mode
    corpus_dir = args.corpus_dir
    tools_dir = args.tools_dir
    tm_dir = args.tm_dir
    wn_version = args.wn_version
    wsi_args_path = args.wsi_args_file
    lemmas_path = args.lemmas_file
    experiment = args.experiment
    tm = args.tm
    skip_alignment = bool(args.skip_alignment)
    keep_wsi_data = bool(args.keep_wsi_data)
    nprocs = args.nprocs

    if mode != "evaluate":
        print "doing training..."
        if corpus_dir is None:
            sys.stderr.write("No corpus directory provided for training!\n\n")
            sys.exit(1)
        elif tm_dir is None:
            sys.stderr.write("No topic modelling programs "
                             "directory provided for training!\n\n")
            sys.exit(1)
        elif tools_dir is None:
            sys.stderr.write("No NLP tools directory provided for "
                             "training!\n\n")
            sys.exit(1)
        elif tm is None:
            sys.stderr.write("No topic modelling algorithm provided "
                             "for training!\n\n")
            sys.exit(1)
        elif lemmas_path is None:
            sys.stderr.write("No lemmas file provided for training!\n\n")
            sys.exit(1)
        elif wsi_args_path is None:
            sys.stderr.write("No WSI args file provided for training!\n\n")
            sys.exit(1)
        elif experiment is None:
            sys.stderr.write("No experiment provided for training!\n\n")
            sys.exit(1)

        wsi_options = parse_wsi_options_file(wsi_args_path)
        do_alignment = not skip_alignment
        if do_alignment and not wn_version:
            sys.stderr.write("No wordnet version provided! "
                             "(required for alignment)\n\n")
            sys.exit(1)

        # create jobs to run
        job_queue = Queue()
        fp_lemmas = open(lemmas_path)
        lemmas = [line.strip() for line in fp_lemmas.xreadlines()]
        fp_lemmas.close()
        if experiment == "default":
            for lem in lemmas:
                job_queue.put((lem, None))
        else:
            model_num = 0
            bootstrap_size = args.bootstrap_size
            for _ in xrange(bootstrap_size):
                for lem in lemmas:
                    job_queue.put((lem, model_num))
                    model_num += 1
        for _ in xrange(nprocs):
            job_queue.put("STOP")

        # run procs to perform wsi
        write_lock = Lock()
        do_bootstrapping = (experiment == "bootstrapping")
        procs = []
        for _ in xrange(nprocs):
            p = Process(target=run_process_worker,
                        args=(job_queue, results_dir, corpus_dir, wn_version,
                              tools_dir, tm, tm_dir, wsi_options,
                              do_bootstrapping, do_alignment,
                              keep_wsi_data, write_lock))
            p.start()
            procs.append(p)
        for p in procs:
            p.join()
        print "WSI processing done!"
        print ""

    # run evaluation if required
    if mode != "train":
        print "doing evaluation..."
        if args.gold_dist_file is None:
            sys.stderr.write("No gold distributions file provided "
                             "for evaluation!\n\n")
            sys.exit(1)

        gold_dist_file = args.gold_dist_file
        save_path = os.path.join(results_dir, "evaluation_results.csv")
        evaluate_results(tm_output_dir, save_path, gold_dist_file)

        print "evaluation done!"
        print ""


# MAIN
if __name__ == "__main__":
    main()
