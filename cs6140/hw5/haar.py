import numpy as np
import os, struct
from array import array as pyarray
import ecoc, adaboost, stump
from random import sample
from sys import stdout

def load_mnist(dataset="training", digits=np.arange(10), path="."):
    """
    Loads MNIST files into 3D numpy arrays

    Adapted from: http://abel.ee.ucla.edu/cvxopt/_downloads/mnist.py
    """

    if dataset == "training":
        fname_img = os.path.join(path, 'train-images.idx3-ubyte')
        fname_lbl = os.path.join(path, 'train-labels.idx1-ubyte')
    elif dataset == "testing":
        fname_img = os.path.join(path, 't10k-images.idx3-ubyte')
        fname_lbl = os.path.join(path, 't10k-labels.idx1-ubyte')
    else:
        raise ValueError("dataset must be 'testing' or 'training'")

    flbl = open(fname_lbl, 'rb')
    magic_nr, size = struct.unpack(">II", flbl.read(8))
    lbl = pyarray("b", flbl.read())
    flbl.close()

    fimg = open(fname_img, 'rb')
    magic_nr, size, rows, cols = struct.unpack(">IIII", fimg.read(16))
    img = pyarray("B", fimg.read())
    fimg.close()

    ind = [ k for k in range(size) if lbl[k] in digits ]
    N = len(ind)

    images = np.zeros((N, rows, cols), dtype=np.uint8)
    labels = np.zeros((N, 1), dtype=np.int8)
    for i in range(len(ind)):
        images[i] = np.array(img[ ind[i]*rows*cols : (ind[i]+1)*rows*cols ]).reshape((rows, cols))
        labels[i] = lbl[ind[i]]

    return images, labels

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
	
def train(data, labels):
    learner = lambda d, l: adaboost.train(stump.random, stump.predict, data=d, labels=l, iters=5000)
    return ecoc.train(data, labels, 50, learner, adaboost.predict)
	
def test(data, labels, codes, predictors):
	return ecoc.test(data, labels, codes, predictors)
	
def main():
	# create some random rectangles
	print "Picking rectangles..."
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
	print "Preparing training images..."
	images, labels = load_mnist(dataset="training", path="data")
	indices = sample(range(len(images)), len(images) / 10)
	train_data = prep_data(images[indices], rectangles)
	train_labels = labels[indices].reshape(len(indices))
	print "Preparing test images..."
	images, labels = load_mnist(dataset="testing", path="data")
	indices = sample(range(len(images)), len(images) / 10)
	test_data = prep_data(images[indices], rectangles)
	test_labels = labels[indices].reshape(len(indices))
	
	# train and test
	print 'Training model...'
	codes, predictors = train(train_data, train_labels)
	print 'Testing model...'
	train_error = test(train_data, train_labels, codes, predictors)
	test_error = test(test_data, test_labels, codes, predictors)
	print "train_error=%.6f test_error=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()