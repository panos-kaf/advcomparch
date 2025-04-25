#!/usr/bin/env python3

import sys
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

## For nbit predictors
predictors_to_plot = [ "  Nbit-16K-" ]

x_Axis = []
mpki_Axis = []

with open(sys.argv[1]) as fp:
    for line in fp:
        tokens = line.split()
        if line.startswith("Total Instructions:"):
            total_ins = int(tokens[2])
        else:
            for pred_prefix in predictors_to_plot:
                if line.startswith(pred_prefix):
                    predictor_string = tokens[0].split(':')[0]
                    correct_predictions = int(tokens[1])
                    incorrect_predictions = int(tokens[2])
                    x_Axis.append(predictor_string)
                    mpki_Axis.append(incorrect_predictions / (total_ins / 1000.0))

fig, ax1 = plt.subplots()
ax1.grid(True)

xAx = np.arange(len(x_Axis))
ax1.xaxis.set_ticks(np.arange(0, len(x_Axis), 1))
ax1.set_xticklabels(x_Axis, rotation=45)
ax1.set_xlim(-0.5, len(x_Axis) - 0.5)
ax1.set_ylim(min(mpki_Axis) - 0.05, max(mpki_Axis) + 0.05)
ax1.set_ylabel("$MPKI$")
line1 = ax1.plot(mpki_Axis, label="mpki", color="red", marker='x')

# raw_input → input in Python 3
plt.title("MPKI")
filename = input("Please provide a filename for the produced file (e.g. output.png): ")
plt.savefig(filename, bbox_inches="tight")

