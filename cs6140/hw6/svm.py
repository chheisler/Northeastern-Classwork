import numpy as np
from random import shuffle
from util import FEATURE_AXIS

class SVM(object):
	def __init__(self, data, labels, tolerance, epsilon, cost, kernel):
		assert ((data < 0) & (data > 1)).sum() == 0
		assert ((labels != 1) & (labels != -1)).sum() == 0
		self.data = data
		self.labels = labels
		self.tolerance = tolerance
		self.epsilon = epsilon
		self.cost = cost
		self.kernel = kernel
		if kernel == linear_kernel:
			self.weights = np.zeros(data.shape[FEATURE_AXIS])
		self.alphas = np.zeros(len(data))
		self.bias = 0.0
		predictor = lambda datum: self.predict(datum)
		if kernel == linear_kernel:
			predicted = np.dot(self.data, self.weights) + self.bias
			self.errors = predicted - self.labels
		else:
			self.errors = np.apply_along_axis(predictor, FEATURE_AXIS, data) - labels
		
	def train(self):
		num_changed = 0
		examine_all = True
		while (num_changed > 0 or examine_all):
			num_changed = 0
			if examine_all:
				for i in range(len(self.data)):
					num_changed += self.examine(i)
			else:
				indices = np.where((self.alphas > 0) & (self.alphas < self.cost))[0]
				for i in indices:
					num_changed += self.examine(i)
			#print "num_changed", num_changed, "examine_all", examine_all
			if examine_all:
				examine_all = False
			elif num_changed == 0:
				examine_all = True
				
	def examine(self, i):
		datum_i = self.data[i]
		label_i = self.labels[i]
		alpha_i = self.alphas[i]
		error_i = self.errors[i]
		r = error_i * label_i
		if (r < -self.tolerance and alpha_i < self.cost) \
		or (r > self.tolerance and alpha_i > 0):
			if ((self.alphas > 0) & (self.alphas < self.cost)).sum() > 1:
				j = np.argmax(np.absolute(error_i - self.errors))
				if self.step(i,j):
					return 1
			indices = np.where((self.alphas > 0) & (self.alphas < self.cost))[0]
			shuffle(indices)
			for j in indices:
				if self.step(i,j):
					return 1
			indices = range(len(self.data))
			shuffle(indices)
			for j in indices:
				if self.step(i,j):
					return 1
		return 0
		
	def step(self, i, j):
		if i == j:
			return False
		datum_i = self.data[i]
		datum_j = self.data[j]
		label_i = self.labels[i]
		label_j = self.labels[j]
		alpha_i = self.alphas[i]
		alpha_j = self.alphas[j]
		error_i = self.errors[i]
		error_j = self.errors[j]
		s = label_i * label_j
		if label_i == label_j:
			low = max(0, alpha_i + alpha_j - self.cost)
			high = min(self.cost, alpha_i + alpha_j)
		else:
			low = max(0, alpha_j - alpha_i)
			high = min(self.cost, alpha_j - alpha_i + self.cost)
		if low == high:
			return False
		kernel_i_i = self.kernel(datum_i, datum_i)
		kernel_j_j = self.kernel(datum_j, datum_j)
		kernel_i_j = self.kernel(datum_i, datum_j)
		eta = kernel_i_i + kernel_j_j - 2 * kernel_i_j
		if eta <= 0:
			return False
		new_alpha_j = alpha_j + label_j * (error_i - error_j) / float(eta)
		if new_alpha_j < low:
			new_alpha_j = low
		elif new_alpha_j > high:
			new_alpha_j = high
		if abs(new_alpha_j - alpha_j) < self.epsilon * (alpha_j + new_alpha_j + self.epsilon):
			return False
		new_alpha_i = alpha_i + s * (alpha_j - new_alpha_j)
		if new_alpha_i > 0 and new_alpha_i < self.cost:
			self.bias = self.bias - error_i \
			+ label_i * (alpha_i - new_alpha_i) * kernel_i_i \
			+ label_j * (alpha_j - new_alpha_j) * kernel_i_j
		elif new_alpha_j > 0 and new_alpha_j < self.cost:
			self.bias = self.bias - error_j \
			+ label_i * (alpha_i - new_alpha_i) * kernel_i_j \
			+ label_j * (alpha_j - new_alpha_j) * kernel_j_j
		else:
			bias_i = self.bias - error_i \
			+ label_i * (alpha_i - new_alpha_i) * kernel_i_i \
			+ label_j * (alpha_j - new_alpha_j) * kernel_i_j
			bias_j = self.bias - error_j \
			+ label_i * (alpha_i - new_alpha_i) * kernel_i_j \
			+ label_j * (alpha_j - new_alpha_j) * kernel_j_j
			self.bias = (bias_i + bias_j) / 2.0
		self.alphas[i] = new_alpha_i
		self.alphas[j] = new_alpha_j
		if self.kernel == linear_kernel:
			self.weights += label_i * (new_alpha_i - alpha_i) * datum_i \
				+ label_j * (new_alpha_j - alpha_j) * datum_j
			predicted = np.dot(self.data, self.weights) + self.bias
		else:
			predictor = lambda datum: self.predict(datum)
			predicted = np.apply_along_axis(predictor, FEATURE_AXIS, self.data)
		self.errors = predicted - self.labels
		return True
		
	def predict(self, datum):
		if self.kernel == linear_kernel:
			return np.dot(self.weights.transpose(), datum) + self.bias
		else:
			return sum(
				self.alphas[i] * self.labels[i] * self.kernel(self.data[i], datum)
				for i in range(len(self.data))
			) + self.bias
		
	def test(self, data, labels):
		if self.kernel == linear_kernel:
			predicted = np.dot(data, self.weights) + self.bias
		else:
			predictor = lambda datum: self.predict(datum)
			predicted = np.apply_along_axis(predictor, FEATURE_AXIS, data)
		predicted = sign(predicted)
		return (predicted != labels).sum() / float(len(labels))
		
@np.vectorize
def sign(x):
	if x >= 0:
		return 1
	else:
		return -1
		
def linear_kernel(datum_i, datum_j):
	return np.dot(datum_i, datum_j)