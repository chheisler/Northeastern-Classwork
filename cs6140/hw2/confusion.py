from tree import Classifier
from random import shuffle
from os import mkdir
from shutil import rmtree
from util import normalize
from regress import Regressor

NUM_FOLDS = 10

def main():
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
	folds = ['tmp/fold%d.data' % x for x in range(NUM_FOLDS)]
	
	# run the trial for the tree
	print "\ntree:"
	classifier = Classifier()
	classifier.train(folds[:-1], max_depth=5)
	print classifier.confusion((folds[-1],))
	
	# run the trial for linear regression
	print "\nlinear:"
	regressor = Regressor(None, delimiter=",")
	coefs = regressor.batch(folds[:-1], 0.00025, 0.000001, maxiters=1000)
	print regressor.confusion((folds[-1],), coefs)
	
	# run the trial for logistic regression
	print "\nlogarithmic:"
	regressor = Regressor(None, delimiter=",")
	coefs = regressor.batch(folds[:-1], 0.0025, 0.000001, logarithmic=True, maxiters=1000)
	print regressor.confusion((folds[-1],), coefs, logarithmic=True)
	
	# clean up our temporary directory
	rmtree('./tmp')

if __name__ == '__main__':
	main()
	