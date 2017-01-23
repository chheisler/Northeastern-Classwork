from math import sqrt
import numpy as np
from util import FEATURE_AXIS

# predict labels for data using k-nearest-neighbors
def predict(unlabeled, data, labels, k):
    predictor = lambda datum: _predict(datum, data, labels, k)
    return np.apply_along_axis(predictor, FEATURE_AXIS, unlabeled)

def _predict(datum, data, labels, k):
    distances = np.sqrt(((data - datum) ** 2).sum(axis=FEATURE_AXIS))
    indices = distances.argsort()[:k]
    return np.argmax(np.bincount(labels[indices].astype('int64')))
