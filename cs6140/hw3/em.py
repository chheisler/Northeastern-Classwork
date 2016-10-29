from random import random
from math import e, pi
import numpy as np
from util import load_data, DATA_AXIS, FEATURE_AXIS
#np.seterr(all='raise')

def em(filename, sources):
    # load data and initialize variables
    data = load_data((filename,), labeled=False)
    n = len(data)
    d = data.shape[FEATURE_AXIS]
    indicators = np.random.rand(len(data), sources)
    weights = np.zeros(sources)
    means = np.zeros((sources, d))
    covars = np.zeros((sources, d, d))
    remaining = 1
    for i in range(n):
        indicators[i] /= indicators[i].sum()
    
    while True:
        # save old values for converging
        old_weights = weights.copy()
        
        # the maximization step
        indicator_sums = indicators.sum(axis=DATA_AXIS)
        weights = indicator_sums / float(n)
        means = np.dot(indicators.transpose(), data)
        means = (means.transpose() / indicator_sums).transpose()
        for m in range(sources):
            covars[m] = np.zeros(covars[m].shape)
            for i in range(len(data)):
                diff = data[i] - means[m]
                covars[m] += indicators[i][m] * np.outer(diff, diff)
            covars[m] /= indicator_sums[m]
            
        # precompute inverses and factors
        invs = np.zeros(covars.shape)
        factors = np.zeros(sources)
        for m in range(sources):
            invs[m] = np.linalg.inv(covars[m])
            factors[m] = (2 * pi) ** (-0.5 * d) * np.linalg.det(covars[m]) ** -0.5
            
        # the expectation step
        for i in range(n):
            for m in range(sources):
                inv = invs[m]
                diff = data[i] - means[m]
                exp = e ** np.dot(np.dot(-0.5 * diff.transpose(), inv), diff)
                indicators[i][m] = factors[m] * exp * weights[m]
            indicators[i] /= indicators[i].sum()
            
        # check if we've converged
        print "weights: %s" % weights
        if np.absolute(weights - old_weights).sum() < 0.000000001:
            print
            break
            
    # print the result
    for m in range(sources):
        print "mean %d: %s" % (m + 1, np.round(means[m]))
        print "covar %d: %s" % (m + 1, np.around(covars[m], 1))
        print "size %d: %f" % (m + 1, round(weights[m] * n))
        print
        
def main():
    em('data/2gaussian.txt', 2)
    #em('data/3gaussian.txt', 3)
    
if __name__ == '__main__':
    main()
