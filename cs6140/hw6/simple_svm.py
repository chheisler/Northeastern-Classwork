import numpy as np
from random import randint
from util import FEATURE_AXIS

class SVM(object):
	def __init__(self, data, labels, tolerance, epsilon, cost, kernel):
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
		
	def train(self, max_passes=10000):
		passes = 0
		while passes < max_passes:
			num_changed = 0
			for i in range(len(self.data)):
				datum_i = self.data[i]
				alpha_i = self.alphas[i]
				label_i = self.labels[i]
				error_i = self.predict(datum_i) - label_i
				r = label_i * error_i
				if (r < -self.tolerance and alpha_i < self.cost) \
				or (r > self.tolerance and alpha_i > 0):
					j = randint(0, len(self.data) - 1)
					if i == j:
						continue
					datum_j = self.data[j]
					label_j = self.labels[j]
					alpha_j = self.alphas[j]
					error_j = self.predict(datum_j) - label_j
					if label_i == label_j:
						low = max(0, alpha_i + alpha_j - self.cost)
						high = min(self.cost, alpha_i + alpha_j)
					else:
						low = max(0, alpha_j - alpha_i)
						high = min(self.cost, self.cost + alpha_j - alpha_i)
					if low == high:
						continue
					eta = 2 * self.kernel(datum_i, datum_j) - self.kernel(datum_i, datum_i) - self.kernel(datum_j, datum_j)
					if eta >= 0:
						continue
					new_alpha_j = alpha_j - label_j * (error_i - error_j) / eta
					if new_alpha_j > high:
						new_alpha_j = high
					elif new_alpha_j < low:
						new_alpha_j = low
					if abs(new_alpha_j - alpha_j) < 0.0001:
						continue
					new_alpha_i = alpha_i + label_i * label_j * (alpha_j - new_alpha_j)
					b1 = self.bias - error_i \
						- label_i * (new_alpha_i - alpha_i) * self.kernel(datum_i, datum_i) \
						- label_j * (new_alpha_j - alpha_j) * self.kernel(datum_i, datum_j)
					b2 = self.bias - error_j \
						- label_i * (new_alpha_i - alpha_i) * self.kernel(datum_i, datum_j) \
						- label_j * (new_alpha_j - alpha_j) * self.kernel(datum_j, datum_j)
					if new_alpha_i > 0 and new_alpha_i < self.cost:
						self.bias = b1
					elif new_alpha_j > 0 and new_alpha_j < self.cost:
						self.bias = b2
					else:
						self.bias = (b1 + b2) / 2.0
					self.alphas[i] = new_alpha_i
					self.alphas[j] = new_alpha_j
					self.weights += label_i * (new_alpha_i - alpha_i) * datum_i \
						+ label_j * (new_alpha_j - alpha_j) * datum_j
					num_changed += 1
			if num_changed == 0:
				passes += 1
			else:
				passes = 0
				
	def predict(self, datum):
		if self.kernel == linear_kernel:
			return np.dot(self.weights.transpose(), datum) + self.bias
		else:
			return sum(
				self.alphas[j] * self.labels[j] * self.kernel(self.data[j], datum)
				for j in range(len(self.data))
			) + self.bias
		
	def test(self, data, labels):
		if self.kernel == linear_kernel:
			predicted = np.dot(data, self.weights) + self.bias
		else:
			predictor = lambda datum: self.predict(datum)
			predicted = np.apply_along_axis(predictor, FEATURE_AXIS, data)
		predicted = sign(predicted)
		return (predicted != labels).sum() / float(len(labels))
		
def linear_kernel(datum_i, datum_j):
	return np.dot(datum_i, datum_j)
	
@np.vectorize
def sign(x):
	if x >= 0:
		return 1
	else:
		return -1