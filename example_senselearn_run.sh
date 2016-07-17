# Created by: Andrew Bennett
# Last updated: July, 2016
#
# Examples demonstrating usage of sense distribution learning script

#!\bin\bash

data_dir=example_senselearn_data
gold_dists_fname=gold_dists.txt
out_dir=example_out

# create gold-standard distributions from annotations
python make_gold_dists_file.py \
    --annotations_dir gold_annotations \
    --save_path $data_dir/$gold_dists_fname

# run example experiments: In all cases,
# manually edit these options if the location of any files/directories
# are different to those listed here

# run HCA-WSI on example lemmas
# HCA configured to run using 10 topics, 10 Gibbs sampling iterations,
# and with burstiness turned on according to hca_wsi_options.txt
echo "#########################################################################"
echo "RUNNING EXAMPLE HCA-WSI EXPERIMENT"
echo "#########################################################################"
echo ""
python run_tm_wsi_sensedist_learning.py \
    --results_dir $out_dir/hca_example_out \
    --mode all \
    --corpus_dir $data_dir/usages \
    --tm_dir topicmodelling \
    --tools_dir nlp_tools \
    --wsi_args_file $data_dir/hca_wsi_options.txt \
    --lemmas_file $data_dir/lemmas.txt \
    --experiment default \
    --tm hca \
    --wn_version wn3.0 \
    --gold_dist_file $data_dir/$gold_dists_fname

# run HDP-WSI on example lemmas
# HDP configured to run using 10 Gibbs sampling iterations according to
# hdp_wsi_options.txt
echo "#########################################################################"
echo "RUNNING EXAMPLE HDP-WSI EXPERIMENT"
echo "#########################################################################"
echo ""
python run_tm_wsi_sensedist_learning.py \
    --results_dir $out_dir/hdp_example_out \
    --mode all \
    --corpus_dir $data_dir/usages \
    --tm_dir topicmodelling \
    --tools_dir nlp_tools \
    --wsi_args_file $data_dir/hdp_wsi_options.txt \
    --lemmas_file $data_dir/lemmas.txt \
    --experiment default \
    --tm hdp \
    --wn_version wn3.0 \
    --gold_dist_file $data_dir/$gold_dists_fname

# run HCA-WSI bootstrapping experiment on example lemmas (5 runs per lemma)
# HCA configured to run using 10 topics, 10 Gibbs sampling iterations,
# and with burstiness turned on according to hca_wsi_options.txt
echo "#########################################################################"
echo "RUNNING EXAMPLE BOOTSTRAPPING HCA-WSI EXPERIMENT"
echo "#########################################################################"
echo ""
python run_tm_wsi_sensedist_learning.py \
    --results_dir $out_dir/hca_bootstrapping_example_out \
    --mode all \
    --corpus_dir $data_dir/usages \
    --tm_dir topicmodelling \
    --tools_dir nlp_tools \
    --wsi_args_file $data_dir/hca_wsi_options.txt \
    --lemmas_file $data_dir/lemmas.txt \
    --experiment bootstrapping \
    --bootstrap_size 5 \
    --tm hca \
    --wn_version wn3.0 \
    --gold_dist_file $data_dir/$gold_dists_fname
