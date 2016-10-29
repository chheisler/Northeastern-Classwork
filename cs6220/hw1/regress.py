import numpy as np
from util import FEATURE_AXIS

def regress(data, labels, lagrange):
    transpose = data.transpose();
    identity = np.identity(data.shape[FEATURE_AXIS])
    inverse = np.linalg.pinv(np.dot(transpose, data) + lagrange * identity)
    return np.dot(np.dot(inverse, transpose), labels)
   
def predict(data, coefs):
    return np.dot(data, coefs)
     
