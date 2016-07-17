"""
Converts morpha-format lemmatized text file into a pretty text file with all the pos tags removed.  
Assumes that each document is separated by boundary symbol (default = "\n"), and the output is 1 
line for each document.

Usage:          CleanMorpha.py
Stdin:          morpha_formatted_text
Stdout:         pretty_text
Other Input:    N/A
Other Output:   N/A
Author:         Jey Han Lau
Date:           Nov 10
"""

import sys

if len(sys.argv) != 1 and len(sys.argv) != 2:
    print "Usage CleanMorpha.py [boundary_symbol] < morpha_formatted_text > pretty_text"
    raise SystemExit

if len(sys.argv) == 2:
    pageboundary = sys.argv[1].strip("\"")
else:
    pageboundary = ""

for line in sys.stdin:
    tail = line.rfind("_")
    if pageboundary != "" and tail != -1 and line.strip()[:tail] == pageboundary:
        sys.stdout.write("\n")

    else:
        tokens = line.strip().split()
        string = ""
        for i, token in enumerate(tokens):
            tail = token.rfind("_")

            if tail != -1:
                #a few special cases:
                #-convert brackets
                #-ignore --cnumb--
                output_token = token[:tail].lower().replace("-lrb-", "(")
                output_token = output_token.replace("-rrb-", ")")
                output_token = output_token.replace("--cnumb--", "")
                output_token = output_token.replace("--cnumbs--", "")
                output_token = output_token.replace("--onumb--", "")
                output_token = output_token.replace("--noun--", "")
                if len(output_token) > 0:
                    sys.stdout.write(output_token)
                    if (i != (len(tokens)-1)):
                        sys.stdout.write(" ")

        if pageboundary == "":
            sys.stdout.write("\n")

