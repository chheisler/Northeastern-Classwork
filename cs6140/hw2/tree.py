from numpy import array, argsort, zeros
from bitarray import bitarray
from sys import maxint
from itertools import permutations
from collections import defaultdict
from math import log
from random import shuffle

DATA_AXIS = 0
FEATURE_AXIS = 1

class Classifier(object):
	def __init__(self):
		self._root = None
		
	@property
	def root(self):
		return self._root
		
	def load_data(self, filenames):
		data = []
		labels = []
		for filename in filenames:
			file = open(filename, 'r')
			for line in file:
				tokens = line.split(',')
				try:
					labels.append(float(tokens.pop()))
					data.append([float(token) for token in tokens])
				except IndexError:
					break
			file.close()
		return (array(data), array(labels))
		
	def train(
		self, filenames,
		gain_threshold=0,
		size_threshold=1,
		entropy_threshold=0,
		max_depth=maxint
	):
		# load the data and labels
		data, labels = self.load_data(filenames)
		
		# presort data indices by all features
		sorted = argsort(data, axis=DATA_AXIS).transpose()
		
		# build the regression tree
		root = Node(data, labels, sorted, len(data) * bitarray('1'))
		stack = [root]
		while len(stack) > 0:
			node = stack.pop()
			counts = defaultdict(float)
			size = 0.0
			for label in node.labels():
				counts[label] += 1
				size += 1
			entropy = self._entropy(counts, size)
				
			# check if we should stop
			if size <= size_threshold \
			or node.depth == max_depth \
			or entropy <= entropy_threshold:
				node.predict()
				continue
				
			# search for the best feature and threshold
			best_gain = 0.0
			best_feature = None
			best_threshold = None
			for feature in range(data.shape[FEATURE_AXIS]):
				sorted_iter = iter(node.sorted(feature))
				datum, label = sorted_iter.next()
				previous_value = datum[feature]
				left_counts = defaultdict(float)
				left_counts[label] = 1.0
				left_size = 1.0
				for datum, label in sorted_iter:
					value = datum[feature]
					if value != previous_value:
						right_counts = {
							label: counts[label] - left_counts[label]
							for label, count in counts.iteritems()
						}
						right_size = size - left_size
						left_entropy = left_size * self._entropy(left_counts, left_size)
						right_entropy = right_size * self._entropy(right_counts, right_size)
						new_entropy = (left_entropy + right_entropy) / size
						gain = entropy - new_entropy
						if gain > best_gain:
							best_gain = gain
							best_feature = feature
							best_threshold = (value + previous_value) / 2.0
					left_counts[label] += 1.0
					left_size += 1
					previous_value = value
					
			# check if best gain is good enough to split
			if best_gain > gain_threshold:
				node.split(best_feature, best_threshold)
				stack += [node.left, node.right]
			else:
				node.predict()
		self._root = root
		
	def _entropy(self, counts, size):
		entropy = 0.0
		for label, count in counts.iteritems():
			if count > 0:
				probability = count / size
				entropy += probability * log(probability, 2)
		return -entropy
		
	def predict(self, datum):
		node = self._root
		while node.predicted is None:
			if datum[node.feature] < node.threshold:
				node = node.left
			else:
				node = node.right
		return node.predicted
		
	def test(self, filenames):
		data, labels = self.load_data(filenames)
		wrong = 0.0
		for idx, datum in enumerate(data):
			predicted = self.predict(datum)
			actual = labels[idx]
			if predicted != actual:
				wrong += 1
		return wrong / len(labels)
		
	def confusion(self, filenames):
		data, labels = self.load_data(filenames)
		matrix = zeros((2, 2))
		for i in range(len(data)):
			actual = labels[i]
			predicted = round(self.predict(data[i]))
			matrix[actual][predicted] += 1
		return matrix
		
class Node(object):
	def __init__(self, data, labels, sorted, present, depth=0):
		self._data = data
		self._labels = labels
		self._sorted = sorted
		self._present = present
		self._depth = depth
		self._left = None
		self._right = None
		self._feature = None
		self._threshold = None
		self._predicted = None
		
	def data(self):
		for idx, label in enumerate(self._data):
			if self._present[idx]:
				yield datum
			
	def labels(self):
		for idx, label in enumerate(self._labels):
			if self._present[idx]:
				yield label
				
	def sorted(self, feature):
		for idx in self._sorted[feature]:
			if self._present[idx]:
				yield (self._data[idx], self._labels[idx])
				
	@property
	def present(self):
		return self._present
		
	@property
	def depth(self):
		return self._depth
		
	@property
	def left(self):
		return self._left
		
	@property
	def right(self):
		return self._right
		
	@property
	def feature(self):
		return self._feature
		
	@ property
	def threshold(self):
		return self._threshold
		
	@property
	def predicted(self):
		return self._predicted
		
	def split(self, feature, threshold):
		self._feature = feature
		self._threshold = threshold
		left_present = bitarray('0') * len(self._data)
		for idx in self._sorted[feature]:
			if self._present[idx]:
				if self._data[idx][feature] < threshold:
					left_present[idx] = True
				else:
					break
		self._left = Node(self._data, self._labels, self._sorted,
			left_present, self._depth + 1)
		self._right = Node(self._data, self._labels, self._sorted,
			self._present & ~left_present, self._depth + 1)
			
	def predict(self):
		counts = defaultdict(float)
		predicted = None
		for label in self.labels():
			counts[label] += 1
			if counts[label] > counts[predicted]:
				predicted = label
		self._predicted = predicted
		