import numpy as np
from util import load_data, FEATURE_AXIS
from sys import argv
from math import e

def train(data, labels, kernel, threshold=0):
	counts = np.zeros(len(data))
	iters = 0
	while True:
		iters += 1
		predicted = np.zeros(len(data))
		for i, datum in enumerate(data):
			predicted[i] = predict(datum, labels[i], data, kernel, counts)
		indices = np.where(predicted <= 0)[0]
		counts[indices] += labels[indices]
		print "iter=%d mistakes=%d" % (iters, len(indices))
		if len(indices) <= threshold:
			return counts
			
def predict(datum, label, data, kernel, counts):
	return label * (counts * kernel(data, datum)).sum()
	
def linear(data, datum):
	return np.dot(data, datum)
	
def gaussian(data, datum):
	var = 1.0
	#d = len(datum)
	#factor = (2 * pi * var) ** (d / 2.0)
	square_norms = ((data - datum) ** 2).sum(axis=FEATURE_AXIS)
	return e ** (-(square_norms / (2.0 * var)))
	
def main():
	kernels = {'linear': linear, 'gaussian': gaussian}
	filename = argv[1]
	kernel = kernels[argv[2]]
	data, labels = load_data((filename,), delimiter="\t", dummy=True)
	train(data, labels, kernel)
	
if __name__ == '__main__':
	main()