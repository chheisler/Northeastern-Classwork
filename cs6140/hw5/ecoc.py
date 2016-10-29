import numpy as np
from random import randint
from util import load_trec
import adaboost, stump
from itertools import product
from random import choice, shuffle
from sys import stdout

def train(data, labels, code_len, learner, predictor):
	num_classes = len(np.unique(labels))
	codes = np.zeros((num_classes, code_len), dtype='int')
	predictors = np.zeros(code_len, dtype='object')
	
	# randomly pick codes
	possible_bits = [
		bits
		for bits in product((0,1), repeat=num_classes)
		if bits[0] == 1 and 0 in bits
	]
	shuffle(possible_bits)
	for j in range(code_len):
		codes[:,j] = np.array(possible_bits.pop())
	
	# train each predictor
	for j, bits in enumerate(codes.T):
		stdout.write("training function %d... " % j)
		binary_labels = np.zeros(labels.shape, dtype='int')
		true_labels = np.where(bits == 1)[0]
		for label in true_labels:
			binary_labels[np.where(labels == label)] = 1
		binary_labels[np.where(binary_labels == 0)] = -1
		params = learner(data, binary_labels)
		predictors[j] = _predictor(predictor, params)
		error = adaboost.test(*params, data=data, labels=binary_labels)
		stdout.write("error=%.6f\n" % error)
	return codes, predictors
		
def _predictor(predictor, params):
	return lambda data: predictor(data, *params)
	
def predict(data, codes, predictors):
	predicted_codes = np.zeros((data.shape[0], codes.shape[1]))
	for j, predictor in enumerate(predictors):
		predicted_codes[:,j] = predictor(data)
	predicted_codes[np.where(predicted_codes == -1)] = 0
	predicted = np.zeros(data.shape[0], dtype='int')
	for i, predicted_code in enumerate(predicted_codes):
		best_matches = 0
		for k, code in enumerate(codes):
			matches = (predicted_code == code).sum()
			if matches > best_matches:
				best_matches = matches
				best_classes = [k]
			elif matches ==  best_matches:
				best_classes.append(k)
		predicted[i] = choice(best_classes)
	return predicted
	
def test(data, labels, codes, predictors):
	predicted = predict(data, codes, predictors)
	return (predicted != labels).sum() / float(len(labels))
	
def main():
	learner = lambda d, l: adaboost.train(stump.random, stump.predict, data=d, labels=l, iters=3000)
	codes, predictors = train('data/8newsgroup/train.trec', 8, learner, adaboost.predict)
	train_error = test('data/8newsgroup/train.trec', codes, predictors)
	test_error = test('data/8newsgroup/test.trec', codes, predictors)
	print "\ntrain_err=%.6f, test_err=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()