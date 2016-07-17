#!/bin/bash
#quick command to print top 10 topic words

./print.topics.R ../topicmodel_output/mode-topics.dat ../topicmodel_output/vocabs.txt \
    ../topicmodel_output/topics.txt.tmp 10
python ConvertTopicDisplayFormat.py < ../topicmodel_output/topics.txt.tmp > \
    ../topicmodel_output/topics.txt
cat ../topicmodel_output/topics.txt
rm ../topicmodel_output/topics.txt.tmp
