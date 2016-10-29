import numpy as np

def load_data(filename):
	file = open(filename, 'r')
	data = []
	labels = []
	for line in file:
		tokens = line.split()
		try:
			labels.append(float(tokens.pop()))
			data.append([1.0] + [float(token) for token in tokens])
		except IndexError:
			break
	file.close()
	return (np.array(data), np.array(labels))

def regress(filename):
	data, labels = load_data(filename)
	return np.dot(
		np.dot(
			np.linalg.pinv(np.dot(data.transpose(), data)),
			data.transpose()
		),
		labels
	)
	
def test(filename, coefs):
	data, labels = load_data(filename)
	predicted = np.dot(data, coefs)
	error = np.subtract(predicted, labels)
	return np.dot(error.transpose(), error) / len(labels)
	
def main():
	coefs = regress('housing_train.txt')
	train_error = test('housing_train.txt', coefs)
	test_error = test('housing_test.txt', coefs)
	print "error: training=%f, test=%f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()