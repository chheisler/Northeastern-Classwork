from util import load_data, trial, DATA_AXIS, FEATURE_AXIS
import numpy as np
from math import e, pi, sqrt

MIN_VAR = 0.001

def bernoulli_train(filenames):
    data, labels = load_data(filenames, delimiter=",")
    bins = np.zeros((1, data.shape[FEATURE_AXIS]))
    bins[0] = data.mean(axis=DATA_AXIS)
    return bin_train(data, labels, bins)
    
def gaussian_train(filenames):
    data, labels = load_data(filenames, delimiter=",")
    priors = np.zeros(2)
    means = np.zeros((2, data.shape[FEATURE_AXIS]))
    #vars = np.zeros((2, data.shape[FEATURE_AXIS]))
    for label in range(2):
        priors[label] = (labels == label).sum() / float(len(labels))
        i = np.where(labels == label)[0]
        means[label] = data[i,:].mean(axis=DATA_AXIS)
        #vars[label] = data[i,:].var(axis=DATA_AXIS)
    vars = data.var(axis=DATA_AXIS)
    vars[np.where(vars < MIN_VAR)] = MIN_VAR
    return priors, means, vars
    
def gaussian_test(filenames, priors, means, vars):
    data, labels = load_data(filenames, delimiter=",")
    predicted = np.apply_along_axis(
        lambda a: gaussian_predict(a, priors, means, vars),
        FEATURE_AXIS,
        data
    )
    false_positive = len(np.where((labels == 0) & (predicted == 1))[0]) / float(len(labels))
    false_negative = len(np.where((labels == 1) & (predicted == 0))[0]) / float(len(labels))
    error = (predicted - labels != 0).sum() / float(len(labels))
    return false_positive, false_negative, error

def gaussian_predict(datum, priors, means, vars):
    best_prob = 0.0
    best_label = 0
    for label in range(2):
        prob = priors[label]
        for j in range(len(datum)):
            mean = means[label][j]
            var = vars[j]
            exp = e ** -((datum[j] - mean) ** 2 / (2.0 * var))
            prob *= exp / (var ** 0.5 * sqrt(2.0 * pi))
        if prob > best_prob:
            best_prob = prob
            best_label = label
    return best_label
    
def four_bin_train(filenames):
    data, labels = load_data(filenames, delimiter=",")
    bins = np.zeros((3, data.shape[FEATURE_AXIS]))
    bins[0] = data.mean(axis=DATA_AXIS)
    bins[1] = data[np.where(labels == 0)[0],:].mean(axis=DATA_AXIS)
    bins[2] = data[np.where(labels == 1)[0],:].mean(axis=DATA_AXIS)
    return bin_train(data, labels, bins)

def nine_bin_train(filenames):
    data, labels = load_data(filenames, delimiter=",")
    mins = data.min(axis=DATA_AXIS)
    maxs = data.max(axis=DATA_AXIS)
    steps = (maxs - mins) / 9.0
    bins = np.zeros((8, data.shape[FEATURE_AXIS]))
    for i in range(8):
        bins[i] = mins + steps * i
    return bin_train(data, labels, bins)
    
def bin_train(data, labels, bins):
    bins.sort(axis=0)
    data = bin_data(data, bins)
    priors = np.zeros(2)
    probs = np.zeros((2, len(bins) + 1, data.shape[FEATURE_AXIS]))
    count = lambda a: np.bincount(a, minlength=len(bins) + 1)
    for label in range(2):
        priors[label] = (labels == label).sum() / float(len(labels))
        i = np.where(labels == label)[0]
        probs[label] = np.apply_along_axis(count, DATA_AXIS, data[i,:])
        probs[label] = (probs[label] + 1) / (len(i) + 2)
    return bins, priors, probs
    
def bin_test(filenames, bins, priors, probs):
    data, labels = load_data(filenames, delimiter=",")
    data = bin_data(data, bins)
    predicted = np.apply_along_axis(
        lambda a: bin_predict(a, priors, probs),
        FEATURE_AXIS,
        data
    )
    false_positive = len(np.where((labels == 0) & (predicted == 1))[0]) / float(len(labels))
    false_negative = len(np.where((labels == 1) & (predicted == 0))[0]) / float(len(labels))
    error = (predicted - labels != 0).sum() / float(len(labels))
    return false_positive, false_negative, error
    
def bin_predict(datum, priors, probs):
    best_prob = 0.0
    best_label = 0
    for label in range(2):
        prob = priors[label]
        for j in range(len(datum)):
            prob *= probs[label][datum[j]][j]
        if prob > best_prob:
            best_prob = prob
            best_label = label
    return best_label
    
def bin_data(data, bins):
    indices = []
    for i in range(bins.shape[0] + 1):
        if i == 0:
            index = np.where(data <= bins[i])
        elif i == bins.shape[0]:
            index = np.where(data > bins[i - 1])
        else:
            index = np.where((data > bins[i - 1]) & (data <= bins[i]))
        indices.append(index)
    for value, index in enumerate(indices):
        data[index] = value
    return data.astype('int32')
    
def main():
    trial("bernoulli", bernoulli_train, bin_test)
    trial("gaussian", gaussian_train, gaussian_test)
    trial("four-bin", four_bin_train, bin_test)
    trial("nine-bin", nine_bin_train, bin_test)
    
if __name__ == '__main__':
    main()