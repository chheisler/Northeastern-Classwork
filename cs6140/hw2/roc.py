from regress import Regressor
from util import normalize, load_data
from random import shuffle
import numpy as np
from os import mkdir
from shutil import rmtree
from matplotlib import pyplot
from math import e

NUM_FOLDS = 10

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
	
def trial(filenames, coefs, logarithmic=False):
	data, labels = load_data(filenames, delimiter=",", dummy=True)
	predicted = np.dot(data, coefs)
	if logarithmic:
		for i in range(len(predicted)):
			predicted[i] = 1.0 / (1 + e ** -predicted[i])
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
	
def main():
	# normalize the data
	mkdir('./tmp')
	namer = lambda filename: filename.replace('data/', 'tmp/norm_')
	normalize(('data/spambase.data',), namer, delimiter=",")
	
	# create folds of data
	file = open('tmp/norm_spambase.data', 'r')
	lines = [line for line in file]
	file.close()
	shuffle(lines)
	folds = [open('tmp/fold%d.data' % x, 'w') for x in range(NUM_FOLDS)]
	for index, line in enumerate(lines):
		folds[index % 10].write(line)
	for fold in folds:
		fold.close()
	folds = ['tmp/fold%d.data' % x for x in range(NUM_FOLDS)]
	
	# set up pyplot
	pyplot.figure()
	pyplot.xlim(0, 1)
	pyplot.ylim(0, 1)
	
	# run the trial for linear regression
	regressor = Regressor(None, delimiter=",")
	coefs = regressor.batch(folds[:-1], 0.00025, 0.000001, maxiters=1000)
	x_series, y_series = trial((folds[-1],), coefs)
	pyplot.plot(x_series, y_series, label="linear")
	print "linear AUC: %f" % auc(x_series, y_series)
	
	# run the trial for logistic regression
	regressor = Regressor(None, delimiter=",")
	coefs = regressor.batch(folds[:-1], 0.0025, 0.000001, logarithmic=True, maxiters=1000)
	x_series, y_series = trial((folds[-1],), coefs, logarithmic=True)
	pyplot.plot(x_series, y_series, label="logistic")
	print "logistic AUC: %f" % auc(x_series, y_series)
	
	# save and clean up
	pyplot.legend(loc="lower right")
	pyplot.savefig('roc.png')
	rmtree('./tmp')
	
if __name__ == '__main__':
	main()