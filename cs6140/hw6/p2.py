from random import shuffle
import svm
from util import load_data, normalize
import numpy as np

NUM_FOLDS = 10

def main():
	namer = lambda name: name + '.norm'
	normalize(('data/spambase.data',), namer, delimiter=",")
	data, labels = load_data(('data/spambase.data.norm',), delimiter=",", label_map={0.0:-1.0,1.0:1.0})
	indices = range(len(data))
	shuffle(indices)
	train_errors = []
	test_errors = []
	step = len(data) / NUM_FOLDS
	for k in range(NUM_FOLDS):
		train_indices = indices[0:k*step] + indices[(k+1)*step:-1]
		test_indices = indices[k*step:(k+1)*step]
		learner = svm.SVM(
			data=data[train_indices],
			labels=labels[train_indices],
			tolerance=0.01,
			epsilon=0.001,
			cost=0.75,
			kernel=svm.linear_kernel
		)
		learner.train()
		train_error = learner.test(data[train_indices], labels[train_indices])
		test_error = learner.test(data[test_indices], labels[test_indices])
		train_errors.append(train_error)
		test_errors.append(test_error)
		print "fold %d: train_error=%.6f test_error=%.6f" % (k + 1, train_error, test_error)
	train_error = sum(train_errors) / float(NUM_FOLDS)
	test_error = sum(test_errors) / float(NUM_FOLDS)
	print "average: train_error=%.6f test_error=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()