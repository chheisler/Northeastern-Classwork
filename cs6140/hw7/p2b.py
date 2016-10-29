import numpy as np
from sys import argv, maxint
from util import load_data, load_mnist, normalize, DATA_AXIS, FEATURE_AXIS
from random import shuffle, sample
from math import e, pi

def test(test_data, test_labels, data, labels, fn):
	predicted = predict(test_data, data, labels, fn)
	return (predicted != test_labels).sum() / float(len(test_labels))
	
def predict(unlabeled, data, labels, fn):
	predictor = lambda datum: _predict(datum, data, labels, fn)
	return np.apply_along_axis(predictor, FEATURE_AXIS, unlabeled)
	
def _predict(datum, data, labels, fn):
	possible = np.unique(labels)
	best_score = -np.inf
	for possibility in possible:
		indices = np.where(labels == possibility)[0]
		prob = (labels == possibility).sum() / float(len(labels))
		kernel_sum = fn(datum, data[indices]).sum()
		score = (1.0 / len(indices)) * kernel_sum
		if score > best_score:
			best_score = score
			best_possibility = possibility
	return best_possibility
		
def euclidean(datum, data):
	return -np.sqrt(((data - datum) ** 2).sum(axis=FEATURE_AXIS))
	
def cosine(datum, data):
	dots = (data * datum).sum(axis=FEATURE_AXIS)
	dists = np.sqrt((data * data).sum(axis=FEATURE_AXIS))
	dist = np.sqrt(np.dot(datum, datum))
	return dots / (dist * dists)
	
def gaussian(datum, data, var=0.01):
	#d = len(datum)
	#factor = (2 * pi * var) ** (d / 2.0)
	square_norms = ((data - datum) ** 2).sum(axis=FEATURE_AXIS)
	return e ** (-(square_norms / (2.0 * var)))
	
def polynomial(datum, data):
	return np.dot(data, datum) ** 2
	
NUM_FOLDS = 10

def main():
	fns = {
		'euclidean': euclidean,
		'cosine': cosine,
		'gaussian': gaussian,
		'polynomial': polynomial
	}
	part = argv[1]
	fn = fns[argv[2]]
	if part == 'spam':
		spam(fn)
	elif part == 'digits':
		digits(fn)
		
def spam(fn):
	namer = lambda name: name + '.norm'
	normalize(('data/spambase.data',), namer, delimiter=",")
	data, labels = load_data(('data/spambase.data.norm',), delimiter=",")
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
			fn
		)
		test_error = test(
			data[test_indices], labels[test_indices],
			data[train_indices], labels[train_indices],
			fn
		)
		train_errors.append(train_error)
		test_errors.append(test_error)
		print "fold %d: train_error=%.6f test_error=%.6f" % (i + 1, train_error, test_error)
	train_error = sum(train_errors) / float(NUM_FOLDS)
	test_error = sum(test_errors) / float(NUM_FOLDS)
	print "average: train_error=%.6f test_error=%.6f" % (train_error, test_error)
	
def digits(fn):
	# create some random rectangles
	print "Generating rectangles..."
	rectangles = []
	for x in range(0, 24):
		for y in range(0, 24):
			for width in range(5, 14):
				for height in range(5, 14):
					area = width * height
					if area >= 130 and area <= 170 \
					and x + width <= 28 and y + height <= 28:
						top_left = (x, y)
						bottom_right = (x + width, y + height)
						rectangles.append((top_left, bottom_right))
	rectangles = sample(rectangles, 100)
	
	# prepare the training and test data
	print "Loading images..."
	images, labels = load_mnist(dataset="training", path="data")
	print "Preparing training data..."
	train_indices = sample(range(len(images)), len(images) / 10)
	train_data = prep_data(images[train_indices], rectangles)
	train_labels = labels[train_indices].reshape(len(train_indices))
	# prepare the testing data
	print "Preparing testing data..."
	images, labels = load_mnist(dataset="testing", path="data")
	test_indices = list(set(range(len(images))) - set(train_indices))
	test_data = prep_data(images[test_indices], rectangles)
	test_labels = labels[test_indices].reshape(len(test_indices))
	
	# test the data
	train_error = test(train_data, train_labels, train_data, train_labels, fn)
	test_error = test(test_data, test_labels, train_data, train_labels, fn)
	print "train_error=%.6f test_error=%.6f" % (train_error, test_error)
	
def prep_data(images, rectangles):
	images = images > 127
	data = np.zeros((len(images), 2 * len(rectangles)))
	for i, image in enumerate(images):
		counts = np.zeros((image.shape[0] + 1, image.shape[1] + 1))
		for x, column in enumerate(counts[1:]):
			for y, row in enumerate(column[1:]):
				counts[x+1,y+1] = counts[x+1,y] + counts[x,y+1] - counts[x,y] + image[x,y]
		for j, rectangle in enumerate(rectangles):
			top_left, bottom_right = rectangle
			
			# calculate horizontal feature
			width = bottom_right[0] - top_left[0]
			corner = (bottom_right[0] - width / 2, bottom_right[1])
			left = black(counts, top_left, corner)
			corner = (bottom_right[0] - width / 2, top_left[1])
			right = black(counts, corner, bottom_right)
			horizontal = left - right
			
			# calculate vertical feature
			height = bottom_right[1] - top_left[1]
			corner = (bottom_right[0], bottom_right[1] - height / 2)
			above = black(counts, top_left, corner)
			corner = (top_left[0], bottom_right[1] - height / 2, )
			below = black(counts, corner, bottom_right)
			vertical = above - below
			
			# update the data
			data[i][j] = horizontal
			data[i][j + len(rectangles)] = vertical
	
	# normalize and return data
	data -= data.min(axis=DATA_AXIS)
	data /= data.max(axis=DATA_AXIS)
	return data
	
def black(counts, top_left, bottom_right):
	top_right = (bottom_right[0], top_left[1])
	bottom_left = (top_left[0], bottom_right[1])
	return counts[bottom_right] - counts[top_right] - counts[bottom_left] + counts[top_left]
	
if __name__ == '__main__':
	main()