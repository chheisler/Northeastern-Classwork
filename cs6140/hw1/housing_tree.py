from numpy import array, argsort
from bitarray import bitarray
from sys import maxint
from itertools import permutations

DATA_AXIS = 0
FEATURE_AXIS = 1

class Regressor(object):
	def __init__(self):
		self._root = None
		
	@property
	def root(self):
		return self._root
		
	def load_data(self, filename):
		file = open(filename, 'r')
		data = []
		labels = []
		for line in file:
			tokens = line.split()
			try:
				labels.append(float(tokens.pop()))
				data.append([float(token) for token in tokens])
			except IndexError:
				break
		file.close()
		return (array(data), array(labels))
		
	def train(
		self, filename,
		gain_threshold=0,
		size_threshold=1,
		error_threshold=0,
		max_depth=maxint
	):
		# load the data and labels
		data, labels = self.load_data(filename)
		
		# presort data indices by all features
		sorted = argsort(data, axis=DATA_AXIS).transpose()
		
		# build the regression tree
		root = Node(data, labels, sorted, len(data) * bitarray('1'))
		stack = [root]
		while len(stack) > 0:
			node = stack.pop()
			total_sum = 0.0
			total_square_sum = 0.0
			total_size = 0.0
			for label in node.labels():
				total_sum += label
				total_square_sum += label ** 2
				total_size += 1
			total_error = self._error(total_sum, total_square_sum, total_size)
			total_error /= total_size
				
			# check if we should stop
			if total_size <= size_threshold \
			or node.depth == max_depth \
			or total_error <= error_threshold:
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
				left_sum = label
				left_square_sum = label ** 2
				left_size = 1.0
				for datum, label in sorted_iter:
					value = datum[feature]
					if value != previous_value:
						right_sum = total_sum - left_sum
						right_square_sum = total_square_sum - left_square_sum
						right_size = total_size - left_size
						left_error = self._error(left_sum, left_square_sum, left_size)
						right_error = self._error(right_sum, right_square_sum, right_size)
						new_error = (left_error + right_error) / total_size
						gain = total_error - new_error
						if gain > best_gain:
							best_gain = gain
							best_feature = feature
							best_threshold = (value + previous_value) / 2.0
					left_sum += label
					left_square_sum += label ** 2
					left_size += 1
					previous_value = value
					
			# check if best gain is good enough to split
			if best_gain > gain_threshold:
				node.split(best_feature, best_threshold)
				stack += [node.left, node.right]
			else:
				node.predict()
		self._root = root
		
	def _error(self, total, square_total, size):
		mean = float(total) / float(size)
		return size * mean ** 2 - 2 * mean * total + square_total
			
	def prune(self):
		pass
		
	def predict(self, datum):
		node = self._root
		while node.predicted is None:
			if datum[node.feature] < node.threshold:
				node = node.left
			else:
				node = node.right
		return node.predicted
		
	def test(self, filename):
		data, labels = self.load_data(filename)
		total = 0.0
		for idx, datum in enumerate(data):
			predicted = self.predict(datum)
			actual = labels[idx]
			total += (predicted - actual) ** 2
		return total / len(labels)
		
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
		total = 0.0
		size = 0.0
		for label in self.labels():
			total += label
			size += 1
		self._predicted = total / size
		
def main():
	regressor = Regressor()
	regressor.train('housing_train.txt', max_depth=2)
	train_error = regressor.test('housing_train.txt')
	test_error = regressor.test('housing_test.txt')
	print "error: training=%f, test=%f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()