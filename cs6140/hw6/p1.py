from sklearn import svm
from util import load_data, load_mnist
from random import shuffle, sample
import numpy as np

NUM_FOLDS = 10

def spambase():
	data, labels = load_data(('data/spambase.data',), delimiter=",")
	indices = range(len(data))
	shuffle(indices)
	train_errors = []
	test_errors = []
	step = len(data) / NUM_FOLDS
	for k in range(NUM_FOLDS):
		train_indices = indices[0:k*step] + indices[(k+1)*step:-1]
		test_indices = indices[k*step:(k+1)*step]
		learner = svm.SVC(C=0.01, kernel='linear', tol=0.01)
		learner.fit(data[train_indices], labels[train_indices])
		train_error = test(learner, data[train_indices], labels[train_indices])
		test_error = test(learner, data[test_indices], labels[test_indices])
		train_errors.append(train_error)
		test_errors.append(test_error)
		print "fold %d: train_error=%.6f test_error=%.6f" % (k + 1, train_error, test_error)
	train_error = sum(train_errors) / float(NUM_FOLDS)
	test_error = sum(test_errors) / float(NUM_FOLDS)
	print "average: train_error=%.6f test_error=%.6f" % (train_error, test_error)
	
def digits():
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
	
	# prepare the data
	print "Loading images..."
	images, labels = load_mnist(dataset="training", path="data")
	print "Preparing data..."
	indices = sample(range(len(images)), len(images) / 5)
	train_data = prep_data(images[indices], rectangles)
	train_labels = labels[indices].reshape(len(indices))
	images, labels = load_mnist(dataset="testing", path="data")
	indices = sample(range(len(images)), len(images) / 5)
	test_data = prep_data(images[indices], rectangles)
	test_labels = labels[indices].reshape(len(indices))
	
	# train and test
	print "Training..."
	learner = svm.SVC(C=0.01, kernel='linear', tol=0.01)
	learner.fit(train_data, train_labels)
	print "Testing..."
	train_error = test(learner, train_data, train_labels)
	test_error = test(learner, test_data, test_labels)
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
	
	return data
	
def black(counts, top_left, bottom_right):
	top_right = (bottom_right[0], top_left[1])
	bottom_left = (top_left[0], bottom_right[1])
	return counts[bottom_right] - counts[top_right] - counts[bottom_left] + counts[top_left]
	
def test(learner, data, labels):
	predicted = learner.predict(data)
	return (predicted != labels).sum() / float(len(labels))
	
def main():
	print "Spambase"
	spambase()
	print "\nDigits"
	digits()
	
if __name__ == '__main__':
	main()