from shutil import rmtree
from os import mkdir
import numpy as np
import os, struct
from array import array as pyarray
from sys import maxint

DATA_AXIS = 0
FEATURE_AXIS = 1
NUM_FOLDS = 10

def load_data(filenames, labels_filenames=None, delimiter=None, dummy=False, label_map=None):
	data = []
	labels = []
	if labels_filenames is not None:
		for data_filename, labels_filename in zip(filenames, labels_filenames):
			data_file = open(data_filename, 'r')
			labels_file = open(labels_filename, 'r')
			for datum_line, label_line in zip(data_file, labels_file):
				datum_tokens = datum_line.strip().split(delimiter)
				label_token = label_line.strip()
				try:
					datum = [float(token) for token in datum_tokens]
					if dummy:
						datum.insert(0, 1.0)
					data.append(datum)
					labels.append(float(label_token))
				except IndexError:
					break
			data_file.close()
			labels_file.close()
	else:
		for filename in filenames:
			file = open(filename, 'r')
			for line in file:
				tokens = line.strip().split(delimiter)
				try:
					labels.append(float(tokens.pop()))
					datum = [float(token) for token in tokens]
					if dummy:
						datum.insert(0, 1.0)
					data.append(datum)
				except IndexError:
					break
			file.close()
	if label_map is not None:
		labels = map(lambda label: label_map[label], labels)
	return np.array(data), np.array(labels)
	
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
	
def normalize(filenames, namer, delimiter=None):
	raw = [
		load_data((filename,), delimiter=delimiter)
		for filename in filenames
	]
	
	data, labels = raw[0]
	for feature in range(data.shape[FEATURE_AXIS]):
		# find and subtract the minimum value
		min_val = maxint
		for data, labels in raw:
			min_val = min(min_val, np.min(data[:,feature]))
		for data, labels in raw:
			data[:,feature] -= float(min_val)
			
		# find and divide by the maximum value
		max_val = -maxint + 1
		for data, labels in raw:
			max_val = max(max_val, np.max(data[:,feature]))
		for data, labels in raw:
			data[:,feature] /= float(max_val)
			
	# write normalized data back out to file
	if delimiter is None:
		delimiter = ' '
	for i, filename in enumerate(filenames):
		new_filename = namer(filename)
		file = open(new_filename, 'w')
		data, labels = raw[i]
		for j, datum in enumerate(data):
			for value in datum:
				file.write(str(value) + delimiter)
			file.write(str(labels[j]) + '\n')
		file.close()