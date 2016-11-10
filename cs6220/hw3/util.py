import numpy as np
from math import log

# axes of data array
DATA_AXIS = 0
FEATURE_AXIS = 1

# load data and labels into numpy arrays
def load_data(file):
    if isinstance(file, str):
        file = open(file, 'r')
    data = []
    labels = []
    for line in file:
        if line[0] == '@' or line[0] == '%':
            continue
        row = line.strip().split(',')
        labels.append(row.pop())
        datum = [float(value) for value in row]
        data.append(datum)
    return np.array(data), np.array(labels)
   
# calculate mean squared error
def mse(labels, predicted):
   return float(((labels - predicted) ** 2).sum()) / len(labels)

# normalize data using z-scores
def zscore(data):
    means = np.mean(data, axis=DATA_AXIS)
    stds = np.std(data, axis=DATA_AXIS, ddof=1)
    return np.nan_to_num((data - means) / stds)
    
