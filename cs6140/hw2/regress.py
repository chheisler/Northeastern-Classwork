import numpy as np
from random import random, shuffle
from math import e, log
from util import DATA_AXIS, FEATURE_AXIS, load_data
from sys import maxint

class Regressor(object):
	def __init__(self, error, delimiter=None):
		self._error = error
		self._delimiter = delimiter
		
	def _load_data(self, filenames, norm=None):
		return load_data(filenames, delimiter=self._delimiter, dummy=True)
		
	def linear(self, filenames, lagrange=0):
		data, labels = self._load_data(filenames)
		identity = np.identity(data.shape[FEATURE_AXIS])
		return np.dot(
			np.dot(
				np.linalg.pinv(
					np.dot(data.transpose(), data) + lagrange * identity
				),
				data.transpose()
			),
			labels
		)
		
	def batch(self, filenames, rate, threshold, logarithmic=False, maxiters=maxint):
		data, labels = self._load_data(filenames)
		#coefs = np.zeros(data.shape[FEATURE_AXIS])
		coefs = np.random.rand(data.shape[FEATURE_AXIS]) * 2 - 1
		predicted, performance = self._performance(data, coefs, labels, logarithmic)
		iters = 0
		while True:
			iters += 1
			for j in range(data.shape[FEATURE_AXIS]):
				if logarithmic:
					coefs[j] += rate * np.dot((labels - predicted), data[:,j])
				else:
					coefs[j] -= rate * np.dot((predicted - labels), data[:,j])
			predicted, new_performance = self._performance(data, coefs, labels, logarithmic)
			if abs(new_performance - performance) < threshold \
			or iters == maxiters:
				return coefs
			performance = new_performance
		
	def stochastic(self, filenames, rate, threshold, logarithmic=False, maxiters=maxint):
		data, labels = self._load_data(filenames)
		coefs = np.zeros(data.shape[FEATURE_AXIS])
		predicted, performance = self._performance(data, coefs, labels, logarithmic)
		iters = 0
		while True:
			for i in range(data.shape[DATA_AXIS]):
				iters += 1
				for j in range(data.shape[FEATURE_AXIS]):
					if logarithmic:
						coefs[j] += rate * (labels[i] - predicted[i]) * data[i][j]
					else:
						coefs[j] -= rate * (predicted[i] - labels[i]) * data[i][j]
				predicted, new_performance = self._performance(data, coefs, labels, logarithmic)
				#print "performance: %f new performance: %f" % (performance, new_performance)
				if abs(new_performance - performance) < threshold \
				or iters == maxiters:
					return coefs
				performance = new_performance
	
	def test(self, filenames, coefs, logarithmic=False):
		data, labels = self._load_data(filenames)
		predicted = np.dot(data, coefs)
		if logarithmic:
			for i in range(len(predicted)):
				predicted[i] = 1.0 / (1 + e ** -predicted[i])
		return self._error(predicted, labels)
		
	def confusion(self, filenames, coefs, logarithmic=False):
		data, labels = self._load_data(filenames)
		matrix = np.zeros((2, 2))
		predicted = np.dot(data, coefs)
		for i in range(len(predicted)):
			if logarithmic:
				predicted[i] = 1.0 / (1 + e ** -predicted[i])
			predicted[i] = int(predicted[i] >= 0.5)
			matrix[labels[i]][predicted[i]] += 1
		return matrix
			
		
	def _performance(self, data, coefs, labels, logarithmic):
		predicted = np.dot(data, coefs)
		if logarithmic:
			for i in range(len(predicted)):
				predicted[i] = 1.0 / (1 + e ** -predicted[i])
				if predicted[i] < 0 or predicted[i] >= 1:
					print predicted[i]
					raise Exception()
			performance = self._likelihood(predicted, labels)
		else:
			performance = self._mse(predicted, labels)
		return predicted, performance
		
	def _mse(self, predicted, labels):
		diff = predicted - labels
		return np.dot(diff.transpose(), diff) / len(labels)
		
	def _likelihood(self, predicted, labels):
		likelihood = 0.0
		for i in range(len(predicted)):
			likelihood += labels[i] * log(predicted[i]) \
			+ (1 - labels[i]) * log(1 - predicted[i])
		return likelihood