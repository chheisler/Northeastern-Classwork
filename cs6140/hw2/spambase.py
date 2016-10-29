from regress import Regressor
from random import shuffle
from numpy import dot
from os import mkdir
from shutil import rmtree
from util import normalize

NUM_FOLDS = 10

def trial(name, regressor, fn, *args, **kwargs):
	logarithmic = kwargs.get('logarithmic') or False
	# normalize the data
	mkdir('./tmp')
	namer = lambda filename: filename.replace('data/', 'tmp/norm_')
	normalize(('data/spambase.data',), namer, delimiter=",")
	
	# create folds of data
	file = open('tmp/norm_spambase.data', 'r')
	lines = [line for line in file]
	file.close()
	shuffle(lines)
	folds = [open('tmp/fold%d.data' % x, 'w') for x in range(NUM_FOLDS)]
	for index, line in enumerate(lines):
		folds[index % 10].write(line)
	for fold in folds:
		fold.close()
		
	# do set of trials using generated folds
	print "\n%s:" % name
	msg = "%s: training=%f, test=%f"
	folds = ['tmp/fold%d.data' % x for x in range(NUM_FOLDS)]
	train_errors = []
	test_errors = []
	for x in range(len(folds)):
	#for x in range(1):
		coefs = fn(regressor, folds[:-1], *args, **kwargs)
		train_error = regressor.test(folds[:-1], coefs, logarithmic)
		test_error = regressor.test([folds[-1]], coefs, logarithmic)
		train_errors.append(train_error)
		test_errors.append(test_error)
		folds = folds[1:] + folds[0:1]
		print msg % ("iteration %d" % (x + 1), train_error, test_error)
	train_error = sum(train_errors) / len(train_errors)
	test_error = sum(test_errors) / len(test_errors)
	print msg % ("average", train_error, test_error)
	rmtree('./tmp')
	
def error(predicted, labels):
	#predicted -= predicted.min()
	#predicted /= predicted.max()
	for i in range(len(predicted)):
		predicted[i] = float(predicted[i] >= 0.5)
		#predicted[i] = predicted[i] >= 0.4
	return float((predicted - labels != 0).sum()) / len(labels)

def main():
	regressor = Regressor(error=error, delimiter=",")
	trial('linear', regressor, Regressor.linear)
	trial('ridge', regressor, Regressor.linear, lagrange=0.25)
	trial('gradient descent', regressor, Regressor.batch, 0.00025, 0.000001, maxiters=1000)
	#trial('gradient descent', regressor, Regressor.stochastic, 0.25, 0, maxiters=100000)
	#trial('gradient descent', regressor, Regressor.stochastic, 0.5, 0, maxiters=10000)
	# managed 0.120747 0.124536
	trial('logarithmic', regressor, Regressor.batch, 0.0025, 0.000001, logarithmic=True, maxiters=1000)
if __name__ == '__main__':
	main()