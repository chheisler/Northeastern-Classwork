from random import choice
from util import DATA_AXIS, FEATURE_AXIS
import numpy as np

def train(data, labels, weights, sorted):
	best_diff = 0.0
	for j, ordering in enumerate(sorted):
		error = np.dot(labels != 1, weights)
		for threshold, indices in ordering:
			error += np.dot(labels[indices], weights[indices])
			diff = abs(0.5 - error)
			if diff > best_diff:
				best_diff = diff
				best_feature = j
				best_threshold = threshold
	return best_feature, best_threshold

def random(data, labels, weights, sorted):
	feature = choice(range(data.shape[FEATURE_AXIS]))
	vals = data[:,feature]
	indices = sorted[feature]
	i = choice(range(data.shape[DATA_AXIS] + 1))
	if i == 0:
		threshold = vals[indices[i]] - 1
	elif i == len(data):
		threshold = vals[indices[-1]] + 1
	else:
		threshold = (vals[indices[i]] + vals[indices[i - 1]]) / 2.0
	return feature, threshold
	
def predict(data, feature, threshold):
	return np.where(data[:,feature] > threshold, 1.0, -1.0)
	
def sort(data, labels, weights, sorted, feature):
	yield data[0][feature] - 1, 0, 0
	for i in sorted[feature]:
		yield data[i][feature], labels[i], weights[i]
	yield data[-1][feature] + 1, 0 , 0