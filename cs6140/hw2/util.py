import numpy as np
from sys import maxint

DATA_AXIS = 0
FEATURE_AXIS = 1

def load_data(filenames, delimiter=None, dummy=False):
	data = []
	labels = []
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
	return np.array(data), np.array(labels)
	
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