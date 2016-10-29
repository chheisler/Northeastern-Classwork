import numpy as np
from math import e, pi
from util import load_data, trial, DATA_AXIS, FEATURE_AXIS

def train(filenames):
    data, labels = load_data(filenames, delimiter=",")
    mean_0 = data[np.where(labels == 0)[0],:].mean(axis=DATA_AXIS)
    mean_1 = data[np.where(labels == 1)[0],:].mean(axis=DATA_AXIS)
    covar = np.cov(data, rowvar=0)
    return mean_0, mean_1, covar
    
def test(filenames, mean_0, mean_1, covar):
    data, labels = load_data(filenames, delimiter=",")
    prob = prob_fn(data.shape[FEATURE_AXIS], covar)
    predicted = np.array([
        predict(prob, datum, mean_0, mean_1)
        for datum in data
    ])
    false_positive = len(np.where((labels == 0) & (predicted == 1))[0]) / float(len(labels))
    false_negative = len(np.where((labels == 1) & (predicted == 0))[0]) / float(len(labels))
    error = (predicted != labels).sum() / float(len(labels))
    return false_positive, false_negative, error
    
def predict(prob, datum, mean_0, mean_1):
    prob_0 = prob(datum, mean_0)
    prob_1 = prob(datum, mean_1)
    return int(prob_1 > prob_0)
    
def prob_fn(size, covar):
    inv = np.linalg.pinv(covar)
    det = np.linalg.det(covar)
    factor = 1.0 / ((2 * pi) ** (size / 2.0) * det ** 0.5)
    def prob(datum, mean):
        diff = datum - mean
        exp = e ** np.dot(np.dot(-0.5 * diff.transpose(), inv), diff)
        return factor * exp
    return prob
    
def main():
    trial("gda", train, test)
    
if __name__ == '__main__':
    main()