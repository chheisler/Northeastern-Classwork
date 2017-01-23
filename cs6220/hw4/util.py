import numpy as np
from math import log

# axes of data array
DATA_AXIS = 0
FEATURE_AXIS = 1

# load data and labels into numpy arrays
def load_data(file, filterFn=None, labelFn=None):
    if isinstance(file, str):
        file = open(file, 'r')
    data = []
    labels = []
    for line in file:
        if filterFn is not None and not filterFn(line):
            continue
        row = line.strip().split(',')
        if labelFn is not None:
            labels.append(labelFn(row.pop()))
        else:
            labels.append(row.pop())
        datum = [float(value) for value in row]
        data.append(datum)
    return np.array(data), np.array(labels)
   
# calculate mean squared error
def mse(labels, predicted):
   return float(((labels - predicted) ** 2).sum()) / len(labels)

# calculate accuracy
def accuracy(labels, predicted):
    return (labels == predicted).sum() / float(len(labels))

# normalize data using z-scores
def zscore(data):
    means = np.mean(data, axis=DATA_AXIS)
    stds = np.std(data, axis=DATA_AXIS, ddof=1)
    return np.nan_to_num((data - means) / stds)
    
