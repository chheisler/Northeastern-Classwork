import numpy as np
from os import mkdir, path
from shutil import rmtree
from random import shuffle
import re

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
	
def load_trec(folder):
	config_file = open(path.join(folder, 'config.txt'), 'r')
	config = config_file.read()
	config_file.close()
	n = int(re.search(r'numDataPoints=(\d+)', config).group(1))
	d = int(re.search(r'numFeatures=(\d+)', config).group(1))
	classes = int(re.search(r'numClasses=(\d+)', config).group(1))
	data = np.zeros((n, d))
	labels = np.zeros(n, dtype='int')
	data_file = open(path.join(folder, 'feature_matrix.txt'), 'r')
	for i, line in enumerate(data_file):
		if i == len(labels):
			break
		tokens = line.strip().split()
		labels[i] = int(tokens.pop(0))
		for token in tokens:
			feature, value = token.split(':')
			feature = int(feature)
			value = float(value)
			data[i][feature] = value
	data_file.close()
	return data, labels, classes
	
def trial(name, train, test):
	# create a temporary directory
	try:
		mkdir('./tmp')
	except OSError:
		pass
		
	# create folds of data
	file = open('data/spambase.data', 'r')
	lines = [line for line in file]
	file.close()
	shuffle(lines)
	folds = [open('tmp/fold%d.data' % x, 'w') for x in range(NUM_FOLDS)]
	for index, line in enumerate(lines):
		folds[index % NUM_FOLDS].write(line)
	for fold in folds:
		fold.close()
		
	# do set of trials using generated folds
	print "\n%s:" % name
	msg = r'%s: train=%f test=%f'
	folds = ['tmp/fold%d.data' % x for x in range(NUM_FOLDS)]
	train_errors = []
	test_errors = []
	for x in range(len(folds)):
		args = train(folds[:-1])
		train_error = test(folds[:-1], *args)
		test_error = test((folds[-1],), *args)
		train_errors.append(train_error)
		test_errors.append(test_error)
		folds = folds[1:] + folds[0:1]
		print msg % ("fold %d" % (x + 1), train_error, test_error)
	train_error = sum(train_errors) / len(train_errors)
	test_error = sum(test_errors) / len(test_errors)
	print msg % ("average", train_error, test_error)
	
	# remove temporary directory
	rmtree('./tmp')