from util import load_data, trial, DATA_AXIS, FEATURE_AXIS
import numpy as np
from math import e, pi, sqrt
from sklearn.decomposition import PCA

def train(data, labels, min_var=0.001):
	classes = len(np.unique(labels))
	priors = np.zeros(classes)
	means = np.zeros((classes, data.shape[FEATURE_AXIS]))
	for label in range(classes):
		priors[label] = (labels == label).sum() / float(len(labels))
		i = np.where(labels == label)[0]
		means[label] = data[i,:].mean(axis=DATA_AXIS)
	vars = data.var(axis=DATA_AXIS)
	vars[np.where(vars < min_var)] = min_var
	return priors, means, vars
	
def test(data, labels, priors, means, vars):
	predicted = np.apply_along_axis(
		lambda datum: predict(datum, priors, means, vars),
		FEATURE_AXIS, data
	)
	error = (predicted != labels).sum() / float(len(labels))
	return error

def predict(datum, priors, means, vars):
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
	
def main():
	# load the data
	train_data, train_labels = load_data(
		('data/spam_polluted/train_feature.txt',),
		labels_filenames=('data/spam_polluted/train_label.txt',)
	)
	test_data, test_labels = load_data(
		('data/spam_polluted/test_feature.txt',),
		labels_filenames=('data/spam_polluted/test_label.txt',)
	)
	
	# train without principle component analysis
	print "without PCA"
	priors, means, vars = train(train_data, train_labels)
	train_error = test(train_data, train_labels, priors, means, vars)
	test_error = test(test_data, test_labels, priors, means, vars)
	print "train_err=%.6f test_err=%.6f" % (train_error, test_error)
	
	# train with principle component analysis
	print "with PCA"
	pca = PCA(n_components=100, copy=False)
	pca.fit(train_data)
	train_data = pca.transform(train_data)
	test_data = pca.transform(test_data)
	priors, means, vars = train(train_data, train_labels)
	train_error = test(train_data, train_labels, priors, means, vars)
	test_error = test(test_data, test_labels, priors, means, vars)
	print "train_err=%.6f test_err=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()