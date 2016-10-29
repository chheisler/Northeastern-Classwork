import numpy as np
from util import load_data, DATA_AXIS, FEATURE_AXIS

class Perceptron(object):
	def batch(self, filenames, rate, threshold):
		data, labels = load_data(filenames, delimiter="\t", dummy=True)
		coefs = np.random.rand(data.shape[FEATURE_AXIS])
		for i in range(data.shape[DATA_AXIS]):
			if labels[i] == -1:
				data[i] = -data[i]
				labels[i] = 1
		iters = 0
		while True:
			iters += 1
			predicted = np.dot(data, coefs)
			mistakes = []
			for i in range(predicted.shape[DATA_AXIS]):
				if predicted[i] < 0:
					mistakes.append(data[i])
			print "iteration %d: mistakes=%d" % (iters, len(mistakes))
			if len(mistakes) < threshold:
				return coefs
			coefs += rate * sum(mistakes)
		
	def _error(self, data, coefs):
		predicted = np.dot(data, coefs)
		wrong = []
		for i in range(predicted.shape[DATA_AXIS]):
			if predicted[i] < 0:
				wrong.append(data[i])
		return rate * sum(wrong)
		
def main():
	perceptron = Perceptron()
	coefs = perceptron.batch(('data/perceptronData.txt',), 0.5, 1)
	print "\nweights: %s" % coefs
	print "normalized: %s" % (coefs / coefs[0])
	
if __name__ == '__main__':
	main()