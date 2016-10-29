from itertools import combinations
import svm
from util import load_mnist, DATA_AXIS
from random import sample
import numpy as np

def main():
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
	
	# prepare the training data
	print "Loading images..."
	images, labels = load_mnist(dataset="training", path="data")
	print "Preparing training data..."
	train_indices = sample(range(len(images)), len(images) / 10)
	train_data = prep_data(images[train_indices], rectangles)
	train_labels = labels[train_indices].reshape(len(train_indices))
	
	# train learners
	print "Training..."
	learners = {}
	for pair in combinations(range(10), 2):
		digit_1, digit_2 = pair
		indices = np.where((train_labels == digit_1) | (train_labels == digit_2))[0]
		data = train_data[indices]
		labels = train_labels[indices].copy()
		labels[labels == digit_1] = -1
		labels[labels == digit_2] = 1
		learners[pair] = learner = svm.SVM(
			data=data,
			labels=labels,
			tolerance=0.001,
			epsilon=0.001,
			cost=0.75,
			kernel=svm.linear_kernel
		)
		learner.train()
	
	# prepare the testing data
	print "Preparing testing data..."
	images, labels = load_mnist(dataset="testing", path="data")
	test_indices = list(set(range(len(images))) - set(train_indices))
	test_data = prep_data(images[test_indices], rectangles)
	test_labels = labels[test_indices].reshape(len(test_indices))
	
	# test the learners
	print "Testing..."
	train_error = test(learners, train_data, train_labels)
	test_error = test(learners, test_data, test_labels)
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
	
def predict(learners, data):
	predicted = np.zeros(len(data))
	for i, datum in enumerate(data):
		votes = np.zeros(10, dtype='uint8')
		for pair, learner in learners.iteritems():
			digit_1, digit_2 = pair
			prediction = learner.predict(datum)
			if prediction < 0:
				votes[digit_1] += 1
			else:
				votes[digit_2] += 1
		predicted[i] = np.argmax(votes)
	return predicted
	
def test(learners, data, labels):
	predicted = predict(learners, data)
	return (predicted != labels).sum() / float(len(labels))
	
if __name__ == '__main__':
	main()