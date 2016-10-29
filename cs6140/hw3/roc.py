from util import load_data, NUM_FOLDS, FEATURE_AXIS
from bayes import bernoulli_train, gaussian_train, four_bin_train, nine_bin_train, bin_data
from os import mkdir
from shutil import rmtree
from matplotlib import pyplot
from random import shuffle
import numpy as np
from math import log, e, pi, sqrt

def predict(datum, priors, probs):
    false_prob = priors[0]
    for j in range(len(datum)):
        false_prob *= probs[0][datum[j]][j]
    true_prob = priors[1]
    for j in range(len(datum)):
        true_prob *= probs[1][datum[j]][j]
    return log(true_prob / false_prob)
    
def trial(filenames, bins, priors, probs):
    data, labels = load_data(filenames, delimiter=",")
    data = bin_data(data, bins)
    predicted = np.apply_along_axis(
        lambda a: predict(a, priors, probs),
        FEATURE_AXIS,
        data
    )
    points = set()
    for prediction in predicted:
        points.add(plot(predicted, labels, prediction))
    points = list(points)
    points.sort()
    x_series = []
    y_series = []
    for x, y in points:
        x_series.append(x)
        y_series.append(y)
    return x_series, y_series
    
def gaussian_trial(filenames, priors, means, stds):
    data, labels = load_data(filenames, delimiter=",")
    predicted = np.apply_along_axis(
        lambda a: gaussian_predict(a, priors, means, stds),
        FEATURE_AXIS,
        data
    )
    points = set()
    for prediction in predicted:
        points.add(plot(predicted, labels, prediction))
    points = list(points)
    points.sort()
    x_series = []
    y_series = []
    for x, y in points:
        x_series.append(x)
        y_series.append(y)
    return x_series, y_series

def gaussian_predict(datum, priors, means, vars):
    false_prob = priors[0]
    for j in range(len(datum)):
        mean = means[0][j]
        var = vars[j]
        exp = e ** -((datum[j] - mean) ** 2 / (2.0 * var))
        false_prob *= 1.0 / (var ** 0.5 * sqrt(2.0 * pi)) * exp
    true_prob = priors[1]
    for j in range(len(datum)):
        mean = means[1][j]
        var = vars[j]
        exp = e ** -((datum[j] - mean) ** 2 / (2.0 * var))
        true_prob *= 1.0 / (var ** 05 * sqrt(2.0 * pi)) * exp
    return log(true_prob / false_prob)
    
def plot(predicted, labels, threshold):
    positives = 0.0
    negatives = 0.0
    true_positives = 0.0
    false_positives = 0.0
    for i in range(len(predicted)):
        prediction = int(predicted[i] >= threshold)
        if labels[i]:
            positives += 1
            if prediction:
                true_positives += 1
        else:
            negatives += 1
            if prediction:
                false_positives += 1
    x = false_positives / negatives
    y = true_positives / positives
    return x, y
    
def auc(x, y):
	total = 0.0
	for i in range(1, len(x)):
		total += 0.5 * (x[i] - x[i-1]) * (y[i] + y[i-1])
	return total
    
def main():
    # create a temporary directory
    try:
        mkdir('./tmp')
    except OSError:
        pass
        
    # create folds of data
    file = open('data/spambase.data', 'r')
    lines = [line for line in file]
    file.close()
    shuffle(lines)
    folds = [open('tmp/fold%d.data' % x, 'w') for x in range(NUM_FOLDS)]
    for index, line in enumerate(lines):
        folds[index % NUM_FOLDS].write(line)
    for fold in folds:
        fold.close()
    folds = ['tmp/fold%d.data' % x for x in range(NUM_FOLDS)]
    
    # set up pyplot
    pyplot.figure()
    pyplot.xlim(0, 1)
    pyplot.ylim(0, 1)
    
    # run trial for bernoulli
    bins, priors, probs = bernoulli_train(folds[:-1])
    x_series, y_series = trial((folds[-1],), bins, priors, probs)
    pyplot.plot(x_series, y_series, label="bernoulli")
    print "bernoulli AUC: %f" % auc(x_series, y_series)
    
    # run trial for gaussian
    priors, means, stds = gaussian_train(folds[:-1])
    x_series, y_series = gaussian_trial((folds[-1],), priors, means, stds)
    pyplot.plot(x_series, y_series, label="gaussian")
    print "gaussian AUC: %f" % auc(x_series, y_series)
    
    # run trial for four bins
    bins, priors, probs = four_bin_train(folds[:-1])
    x_series, y_series = trial((folds[-1],), bins, priors, probs)
    pyplot.plot(x_series, y_series, label="four bins")
    print "four bin AUC: %f" % auc(x_series, y_series)
    
    # run trial for nine bins
    bins, priors, probs = nine_bin_train(folds[:-1])
    x_series, y_series = trial((folds[-1],), bins, priors, probs)
    pyplot.plot(x_series, y_series, label="nine bins")
    print "nine bin AUC: %f" % auc(x_series, y_series)
    
    # save and clean up
    pyplot.legend(loc="lower right")
    pyplot.savefig('roc.png')
    rmtree('./tmp')
    
if __name__ == '__main__':
    main()
    