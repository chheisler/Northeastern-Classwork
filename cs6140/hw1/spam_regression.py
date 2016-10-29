import numpy as np
from random import shuffle

def load_data(filenames):
	data = []
	labels = []
	for filename in filenames:
		file = open(filename, 'r')
		for line in file:
			tokens = line.split(',')
			try:
				labels.append(float(tokens.pop()))
				data.append([1.0] + [float(token) for token in tokens])
			except IndexError:
				break
		file.close()
	return (np.array(data), np.array(labels))

def regress(filenames):
	data, labels = load_data(filenames)
	return np.dot(
		np.dot(
			np.linalg.pinv(np.dot(data.transpose(), data)),
			data.transpose()
		),
		labels
	)
	
def test(filenames, coefs):
	data, labels = load_data(filenames)
	predicted = np.dot(data, coefs)
	for idx, label in enumerate(predicted):
		predicted[idx] = round(label)
	error = predicted - labels
	return float((error != 0).sum()) / len(labels)
	
def main():
	# create 10 folds of data
	file = open('spambase.data', 'r')
	lines = [line for line in file]
	file.close()
	shuffle(lines)
	folds = [open('fold%d.data' % x, 'w') for x in range(10)]
	for idx, line in enumerate(lines):
		folds[idx % 10].write(line)
	for fold in folds:
		fold.close()
		
	# train and test with 10 folds
	msg = "%s: training=%f, test=%f"
	folds = ['fold%d.data' % x for x in range(10)]
	train_errors = []
	test_errors = []
	for x in range(len(folds)):
		coefs = regress(folds[:-1])
		train_error = test(folds[:-1], coefs)
		test_error = test([folds[-1]], coefs)
		train_errors.append(train_error)
		test_errors.append(test_error)
		folds = folds[1:] + folds[0:1]
		print msg % ("iteration %d" % (x + 1), train_error, test_error)
	train_error = sum(train_errors) / len(train_errors)
	test_error = sum(test_errors) / len(test_errors)
	print msg % ("average", train_error, test_error)
	
if __name__ == '__main__':
	main()