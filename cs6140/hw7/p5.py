from util import load_data, normalize, DATA_AXIS, FEATURE_AXIS
import numpy as np
from random import shuffle

def test(test_data, test_labels, data, labels, k, fn):
	predicted = predict(test_data, data, labels, k, fn)
	return (predicted != test_labels).sum() / float(len(test_labels))
	
def predict(unlabeled, data, labels, k, fn):
	predictor = lambda datum: _predict(datum, data, labels, k, fn)
	return np.apply_along_axis(predictor, FEATURE_AXIS, unlabeled)
	
def _predict(datum, data, labels, k, fn):
	similarities = fn(datum, data)
	indices = similarities.argsort()
	return np.argmax(
		np.bincount(
			labels[indices[-k:]].astype('int64')
		)
	)
	
def relief(data, labels):
	scores = np.zeros(data.shape[FEATURE_AXIS])
	for i in range(data.shape[DATA_AXIS]):
		datum = data[i]
		similarities = euclidean(datum, data)
		indices = np.argsort(similarities)
		same = opp = None
		for j in indices[::-1]:
			if i == j:
				continue
			if same is None and labels[i] == labels[j]:
				same = data[j]
			if opp is None and labels[i] != labels[j]:
				opp = data[j]
			if same is not None and opp is not None:
				break
		scores -= (datum - same) ** 2 + (datum - opp) ** 2
	return scores
			
def euclidean(datum, data):
	return -np.sqrt(((data - datum) ** 2).sum(axis=FEATURE_AXIS))
	
NUM_FOLDS = 10

def main():
	namer = lambda name: name + '.norm'
	normalize(('data/spambase.data',), namer, delimiter=",")
	data, labels = load_data(('data/spambase.data.norm',), delimiter=",")
	scores = relief(data, labels)
	indices = np.argsort(scores)[-5:]
	print "best features: %s" % indices
	data = data[:,indices]
	indices = range(len(data))
	shuffle(indices)
	train_errors = []
	test_errors = []
	step = len(data) / NUM_FOLDS
	for i in range(NUM_FOLDS):
		train_indices = indices[0:i*step] + indices[(i+1)*step:-1]
		test_indices = indices[i*step:(i+1)*step]
		train_error = test(
			data[train_indices], labels[train_indices],
			data[train_indices], labels[train_indices],
			1, euclidean
		)
		test_error = test(
			data[test_indices], labels[test_indices],
			data[train_indices], labels[train_indices],
			1, euclidean
		)
		train_errors.append(train_error)
		test_errors.append(test_error)
		print "fold %d: train_error=%.6f test_error=%.6f" % (i + 1, train_error, test_error)
	train_error = sum(train_errors) / float(NUM_FOLDS)
	test_error = sum(test_errors) / float(NUM_FOLDS)
	print "average: train_error=%.6f test_error=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()