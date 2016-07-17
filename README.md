This repository provides for accessing the LexSemTM dataset, and running
experiments using HCA-WSI and HDP-WSI. If you make use this code or the
LexSemTM dataset in your work, please cite:

- Andrew Bennett, Timothy Baldwin, Jey Han Lau, Diana McCarthy, and
  Francis Bond (to appear). LexSemTM: A Semantic Dataset Based on All-words
  Unsupervised Sense Distribution Learning. In Proceedings of the 54th Annual
  Meeting of the Association for Computational Linguistics (ACL 2016),
  Berlin, Germany.

# Directory Structure

- **example_lexsemtm_access.py:** Example Python script demonstrating use of the
  LexSemTM reader provided by "lexsemtm.py".
- **example_senselearn_data:** Contains example input data for running
  sense distribution learning experiments.
- **example_senselearn_run.sh:** Example shell script demonstrating use of
  script for sense distribution learning experiments.
- **gold_annotations:** Contains gold-standard WordNet 3.0 sense
  annotations for the 50 lemma dataset from Bennett et al. (to appear).
- **lexsemtm.py:** Python program for accessing data in LexSemTM.
- **lexsemtm_data:** Empty directory for storing LexSemTM data.
- **make_gold_dists_file.py:** Script for parsing gold-standard
  sense annotations.
- **nlp_tools:** Contains miscellaneous NLP tools required by experiments.
- **run_tm_wsi_sensedist_learning.py:** Python program for running sense
  distribution learning experiments.
- **senselearn:** Python library used by sense distribution learning script.
- **topicmodelling:** Contains code for HDP and HCA topic modelling algorithms.

# LexSemTM

## Download Instructions

Download the LexSemTM data and index files, and store in a
common directory (recommended: "lexsemtm_data"). The following files
need to be downloaded:

1. Tar archive containing sense distribution and topic model data:
https://storage.googleapis.com/lexsemtm/en.s.data.tar
2. Index file containing all lemmas and corresponding metadata:
https://storage.googleapis.com/lexsemtm/en.s.lemmas.tab
3. Index file containing all vocabulary and corresponding metadata:
https://storage.googleapis.com/lexsemtm/en.vocab.tab

## Interface

The LexSemTMReader class in "lexsemtm.py" provides an interface for accessing
the data in LexSemTM, including both the lemma sense distributions, and
the lemma topic models (topic distributions over words, and document
distributions over topics). The "example_lexsemtm_access.py" script provides
some example code demonstrating the use of the LexSemTMReader class.

# Sense Distribution Learning

## Prerequisites

### Install WordNet

Princeton WordNet is available for download at https://wordnet.princeton.edu,
and is required to create sense distributions from the topic modelling output
of HDP or HCA.

Install all version(s) of WordNet to be experimented with, and link or copy
the binaries to the "nlp_tools/wn_bin" directory. Follow the instructions
there to download and install all required version(s) of WordNet.

In order to be able to run the example usage script
example_senselearn_run.sh, WordNet 3.0, should be installed,
and an executable with name "wn3.0" should be stored in "nlp_tools/wn_bin"
(either the WordNet executable itself, or a link to it).

### Compile Morpha

Morpha is required in order to align topic modelling output to WordNet.
The compiled morpha binary needs to be located at "nlp_tools/morpha/morpha",
and should be executable. If the provided binary (compiled on Linux) does not
work, follow the instructions in "nlp_tools/morpha/README" to re-compile.

### Configure OpenNLP

OpenNLP is also required in order to align topic modelling output to WordNet.
Depending on your version of Java, OpenNLP may or may not require any
manual configuration. See "nlp_tools/opennlp-tools-1.5.0/README" for more
detail.

### Compile HDP and/or HCA

In order to be able to run sense distribution learning experiments with HDP
or HCA, the respective topic modelling programs need to be compiled.
The respective binaries need to be located at
"topicmodelling/hdp/hdp" or "topicmodelling/HCA-0.61/hca/hca" respectively,
and should be executable.
If the provided binaries (compiled on Linux) do not work, follow the
instructions at "topicmodelling/hdp/README" or
"topicmodelling/HCA-0.61/README" respectively to re-compile.

### Install NLTK

In order to be able to run the evaluate part of the sense distribution learning
script, the Natural Language Toolkit (NLTK) must be installed.
Follow the instructions at
http://www.nltk.org/install.html
if necessary.

## Running Experiments

After configuring the prerequisites described above, the Python script
"run_tm_sensedist_learning.py" can be used to run sense distribution learning
experiments using HDP-WSI and HCA-WSI. It allows standard sense distribution
learning and bootstrapping experiments to be run, as described in
Bennett et al. (to appear).

The directory "example_senselearn_data" contains some example inputs for this
program, and the "example_senselearn_run.sh" script demonstrates how to
run sense distribution learning experiments on the example inputs.

### Script Arguments

Required arguments for sense distribution learning script:

- **results_dir:** Path to base directory for storing all sense distribution
  learning outputs (will be created if it does not exist).
- **mode:** What mode of experiment to run. Should be either "train" to create
  all topic models and sense distributions, "evaluate" to perform evaluation
  of results, or "all" to do both.

Arguments required for training (if running in mode "training" or "all"):

- **corpus_dir:** Path to directory containing lemma usage files.
  Each usage file should be named LEMMA.txt, where LEMMA is the name
  of the lemma.
- **tm_dir:** Path to directory containing topic modelling programs
  ("topicmodelling" directory).
- **tools_dir:** Path to directory containing NLP tools
  ("nlp_tools" directory).
- **wsi_args_file:** Path to file containing command line arguments to be
  provided to HDP or HCA. Should consist of one argument per line, either
  consisting of two tokens separated by whitespace (e.g. the line "K 20"
  adds the option "--K 20") or a single token (e.g. the line "Sad=0.5"
  adds the option "--Sad=0.5").
- **lemmas_file:** File containing lemmas to run sense distribution learning on.
  Should consist of one lemma per line.
- **experiment:** Which kind of experiment to run. Should be either "default"
  to train one sense distribution on all usages of each lemma, or
  "bootstrapping" to train multiple sense distributions on random subsets
  of each lemma's usages.
- **tm:** Which topic modelling algorithm to use (either "hdp" or "hca").
- **wn_version:** Which version of WordNet to use for topic-sense alignment.
  This should be the name of a WordNet executable stored in
  "NLP_TOOLS/wn_bin", where NLP_TOOLS is the path to the nlp_tools directory.
  This option is only required if alignment is not being skipped.

Arguments required for evaluation (if running in mode "evaluate" or "all"):

- **gold_dist_file:** File containing gold-standard distributions.
  Should consist of one line per sense, providing the un-normalised
  frequency of that sense (to be normalised on a per-lemma basis).
  Sense format is LEMMA.NUM, where LEMMA is the name of the corresponding
  lemma, and NUM is the sense number of the lemma. Can be created
  using "make_gold_dists_file.py".

Optional arguments:

- **bootstrap_size:** Number of sense distributions to train per lemma if
  performing bootstrapping experiment (default: 10). Only relevant for
  bootstrapping training.
- **skip_alignment:** If argument is provided, don't perform
  topic-sense alignment of topic modelling results (instead, only create
  topic modelling output). Only relevant for training.
- **keep_wsi_data:** If option is provided, don't delete intermediate
  files created by HDP-WSI or HCA-WSI. Only relevant for training.
- **nprocs:** Number of processes to run in parallel for performing sense
  distribution learning experiment (default: 1). Only relevant for training.

In general, the assumed format of lemma names is WORD.POS.LANG (e.g.
"tree.n.en"), where WORD
is the word type, POS is the part of speech ("n" for noun, "v" for verb,
"a" for adjective, and "r" for adverb), and LANG is the language (currently
only "en" is supported).

### Script Outputs

After running the sense distribution learning script, the following results
are stored in the results directory:

- **tm_output:** This is a directory containing all outputs from HDP-WSI or
  HCA-WSI. Each output is stored in a separate JSON file, containing
  topic-word counts (un-normalised topic distributions over words) and
  document-topic counts (un-normalised document distributions over topics)
  from topic modelling, as well as other relevant metadata (including
  information on time to train model and perplexity values). This output is
  created by the training part of the script.
- **evaluation_results.csv:** This file contains a summary of evaluation
  results, including the Jensen-Shannon Divergence (JSD) of the resultant sense
  distribution with respect to the provided gold-standard distribution
  for each model, and the JSD of the corresponding SemCor-based distribution
  with respect to the gold-standard distribution (as described in Bennett et
  al., 2016). This output is created by the evaluation part of the script.


# Gold-Standard Dataset

The gold-standard sense annotated sentences for the 50 lemmas used to
evaluate LexSemTM in Bennett et al. (to appear)
 are located in directory "gold_annotations".
These can be converted to a set of gold-standard distributions for
evaluating sense distribution learning using "make_gold_dists_file.py"
(example usage can be seen in "example_senselearn_run.sh").

The full sets of usages for these lemmas used to train the corresponding
LexSemTM sense distributions are available at
https://storage.googleapis.com/lexsemtm/gold_usages.tar.gz for download.

# Licensing
* MIT license - http://opensource.org/licenses/MIT
