import csv
import numpy as np
from math import log

# axes of data array
DATA_AXIS = 0
FEATURE_AXIS = 1

# load data and labels into numpy arrays
def load_data(file, start=0, dummy=None):
    if isinstance(file, str):
        file = open(file, 'r')
    data = []
    labels = []
    reader = csv.reader(file)
    reader_iter = iter(reader)
    next(reader_iter)
    for row in reader_iter:
        labels.append(float(row.pop()))
        datum = [float(value) for value in row[start:]]
        if dummy is not None:
            datum.insert(0, float(dummy))
        data.append(datum)
    return np.array(data), np.array(labels)
   
# calculate mean squared error
def mse(labels, predicted):
   return float(((labels - predicted) ** 2).sum()) / len(labels)

# normalize data using z-scores
def zscore(data):
    means = np.mean(data, axis=DATA_AXIS)
    stds = np.std(data, axis=DATA_AXIS)
    return (data - means) / stds
    
