from regress import Regressor
from random import shuffle
from numpy import dot
from util import normalize
from os import mkdir
from shutil import rmtree

def trial(name, regressor, fn, *args, **kwargs):
	print '\n%s:' % name
	mkdir('./tmp')
	namer = lambda filename: filename.replace('data/', 'tmp/norm_')
	normalize(('data/housing_train.txt', 'data/housing_test.txt'), namer)
	coefs = fn(regressor, ('tmp/norm_housing_train.txt',), *args, **kwargs)
	train_error = regressor.test(('tmp/norm_housing_train.txt',), coefs)
	test_error = regressor.test(('tmp/norm_housing_test.txt',), coefs)
	print 'error: training=%f, test=%f' % (train_error, test_error)
	rmtree('./tmp')
	return train_error, test_error
	
def error(predicted, labels):
	diff = predicted - labels
	return dot(diff.transpose(), diff) / len(labels)

def main():
	regressor = Regressor(error=error)
	trial('linear', regressor, Regressor.linear)
	trial('ridge', regressor, Regressor.linear, lagrange=2)
	trial('stochastic descent', regressor, Regressor.stochastic, 0.0125, 0.000001)
	
if __name__ == '__main__':
	main()