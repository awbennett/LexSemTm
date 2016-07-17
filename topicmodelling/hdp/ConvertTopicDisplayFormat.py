"""
Quick and simple python program that converts the ugly and dumb vertical display of topics
to horizontal display (1 topic per line).

Usage:          ConvertTopicDisplayFormat.py
Stdin:          topics.txt
Stdout:         mod_topics.txt
Other Input:    N/A
Other Output:   N/A
Author:         Jey Han Lau
Date:           Sep 11
"""

import sys

topics=[] #[[topic1], [topic2], ...]
line_id = 0
for line in sys.stdin:
    data = line.strip().split()

    if line_id == 0:
        for i in range(0, len(data)):
            topics.append([])
    else:
        for i in range(0, len(data)):
            topic_words = topics.pop(i)
            topic_words.append(data[i])
            topics.insert(i, topic_words)

    line_id += 1

for topic in topics:
    print " ".join(topic)
