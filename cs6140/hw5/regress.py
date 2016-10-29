from util import load_data, DATA_AXIS, FEATURE_AXIS
from math import log, e
from sys import maxint
import numpy as np
from sklearn import linear_model

def train(data, labels, rate, threshold, maxiters=maxint):
	coefs = np.random.rand(data.shape[FEATURE_AXIS]) * 2 - 1
	predicted, performance = _performance(data, coefs, labels)
	iters = 0
	while True:
		iters += 1
		for j in range(data.shape[FEATURE_AXIS]):
			coefs[j] += rate * np.dot((labels - predicted), data[:,j])
		predicted, new_performance = _performance(data, coefs, labels)
		if abs(new_performance - performance) < threshold \
		or iters == maxiters:
			return coefs
		performance = new_performance
		
def ridge_train(data, labels, rate, threshold, maxiters, limit):
	coefs = np.random.rand(data.shape[FEATURE_AXIS]) * 2 - 1
	predicted, performance = _performance(data, coefs, labels)
	iters = 0
	while True:
		iters += 1
		print "iter=%d performance=%.6f" % (iters, performance)
		for j in range(data.shape[FEATURE_AXIS]):
			slope = 1.0 / len(data) * np.dot(predicted - labels, data[:,j])
			ridge = limit / len(data) * coefs[j]
			coefs[j] -= rate * (slope + ridge)
		predicted, new_performance = _performance(data, coefs, labels)
		if abs(new_performance - performance) < threshold \
		or iters == maxiters:
			return coefs
		performance = new_performance
		
def _performance(data, coefs, labels):
	predicted = 1.0 / (1.0 + e ** -np.dot(data, coefs))
	performance = _likelihood(predicted, labels)
	return predicted, performance
	
def _likelihood(predicted, labels):
	return (labels * np.log(predicted) + (1 - labels) * np.log(1 - predicted)).sum()
	
def logistic_test(data, labels, coefs):
	predicted = (1.0 / (1.0 + e ** -np.dot(data, coefs))) >= 0.5
	return (predicted != labels).sum() / float(len(labels))
	
def linear_test(data, labels, coefs):
	predicted = np.dot(data, coefs) >= 0.5
	return (predicted != labels).sum() / float(len(labels))
	
def lasso_test(data, labels, regressor, threshold):
	predicted = regressor.predict(data) >= threshold
	return (predicted != labels).sum() / float(len(labels))
	
def main():
	# load and normalize the data
	train_data, train_labels = load_data(
		('data/spam_polluted/train_feature.txt',),
		labels_filenames=('data/spam_polluted/train_label.txt',),
		dummy=True
	)
	test_data, test_labels = load_data(
		('data/spam_polluted/test_feature.txt',),
		labels_filenames=('data/spam_polluted/test_label.txt',),
		dummy=True
	)
	mins = np.concatenate((train_data[:,1:], test_data[:,1:]), axis=DATA_AXIS).min(axis=DATA_AXIS)
	train_data[:,1:] = np.apply_along_axis(lambda datum: datum - mins, FEATURE_AXIS, train_data[:,1:])
	test_data[:,1:] = np.apply_along_axis(lambda datum: datum - mins, FEATURE_AXIS, test_data[:,1:])
	maxs = np.concatenate((train_data[:,1:], test_data[:,1:]), axis=DATA_AXIS).max(axis=DATA_AXIS)
	train_data[:,1:] = np.apply_along_axis(lambda datum: datum / maxs, FEATURE_AXIS, train_data[:,1:])
	test_data[:,1:] = np.apply_along_axis(lambda datum: datum / maxs, FEATURE_AXIS, test_data[:,1:])
	
	# train without regularization
	# coefs = train(train_data, train_labels, 0.0025, 0.001, maxiters=250)
	# train_error = logistic_test(train_data, train_labels, coefs)
	# test_error = logistic_test(test_data, test_labels, coefs)
	# print "logistic: train_err=%.6f test_err=%.6f" % (train_error, test_error)
	
	# train with ridge regularization
	# regressor = linear_model.Ridge(alpha=1.5, fit_intercept=False, tol=0.001, max_iter=250)
	# regressor.fit(train_data, train_labels)
	# train_error = linear_test(train_data, train_labels, regressor.coef_)
	# test_error = linear_test(test_data, test_labels, regressor.coef_)
	# print "ridge: train_err=%.6f test_err=%.6f" % (train_error, test_error)
	
	# traint with lasso regularization
	# for x in range(1000):
		# alpha = x / 100000.0
	# regressor = linear_model.Lasso(alpha=0.001, max_iter=10000)
	# regressor.fit(train_data[:,1:], train_labels)
	#train_error = linear_test(train_data, train_labels, regressor.coef_)
	#test_error = linear_test(test_data, test_labels, regressor.coef_)
	# for x in range(100):
		# threshold = x / 100.0
		# train_error = lasso_test(train_data[:,1:], train_labels, regressor, threshold)
		# test_error = lasso_test(test_data[:,1:], test_labels, regressor, threshold)
		# print "threshold=%.3f train_err=%.6f test_err=%.6f" % (threshold, train_error, test_error)
		
	# train with custom ridge regularization
	coefs = ridge_train(train_data, train_labels, 6.0, 0.001, 10000, 0.8)
	train_error = logistic_test(train_data, train_labels, coefs)
	test_error = logistic_test(test_data, test_labels, coefs)
	print "custom ridge: train_err=%.6f test_err=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()
	