import csv
import numpy as np

DATA_AXIS = 0
FEATURE_AXIS = 1

def load_data(file, dummy=None):
    data = []
    labels = []
    reader = csv.reader(file)
    reader_iter = iter(reader)
    next(reader_iter)
    for row in reader_iter:
        labels.append(float(row.pop()))
        datum = [float(value) for value in row]
        if dummy is not None:
            datum.insert(0, float(dummy))
        data.append(datum)
    return np.array(data), np.array(labels)
   
def mse(labels, predicted):
   return float(((labels - predicted) ** 2).sum()) / len(labels)
    
