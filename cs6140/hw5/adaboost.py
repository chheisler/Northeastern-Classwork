import numpy as np
from math import e, log, ceil
import stump
from util import load_data, trial, DATA_AXIS, FEATURE_AXIS
from matplotlib import pyplot

def train(
	learner, predictor,
	filenames=None,
	data=None, labels=None,
	iters=100, verbose=False,
	test_data=None, test_labels=None
):
	if data is None:
		data, labels = load_data(filenames, delimiter=",", label_map={0.0:-1.0,1.0:1.0})
	else:
		labels[np.where(labels == 0)] = -1
		
	# presort data thresholds and indices
	sorted = np.argsort(data, axis=DATA_AXIS).transpose()
	sorted_jagged = np.zeros(data.shape[FEATURE_AXIS], dtype='object')
	for j in range(data.shape[FEATURE_AXIS]):
		parts = []
		indices = []
		prev_val = data[0][j] - 1
		for i in sorted[j]:
			val = data[i][j]
			if val != prev_val:
				parts.append((prev_val, indices))
				indices = []
			indices.append(i)
			prev_val = val
		parts.append((data[-1][j] + 1, indices))
		sorted_jagged[j] = parts
	#sorted = sorted_jagged
	
	# begin adaboost
	weights = np.zeros(data.shape[DATA_AXIS])
	weights.fill(1.0 / data.shape[DATA_AXIS])
	alphas = np.zeros(iters)
	predictors = np.zeros(iters, dtype='object')
	if verbose:
		train_errors = []
		test_errors = []
		train_margins = np.zeros(data.shape[DATA_AXIS])
		test_margins = np.zeros(test_data.shape[DATA_AXIS])
		round_errors = []
		train_aucs = []
		test_aucs = []
	for t in range(iters):
		# print "adaboost iter %d" % t
		params = learner(data, labels, weights, sorted)
		predictors[t] = _predictor(predictor, params)
		predicted = predictors[t](data)
		error = np.dot(predicted != labels, weights)
		alphas[t] = 0.5 * log((1.0 - error) / error)
		weights *= e ** (-alphas[t] * labels * predicted)
		weights /= weights.sum()
		if verbose:
			train_margins += predict(data, alphas[:t+1], predictors[:t+1], raw=True)
			test_margins += predict(test_data, alphas[:t+1], predictors[:t+1], raw=True)
			train_error = _error(np.sign(train_margins), labels)
			test_error = _error(np.sign(test_margins), test_labels)
			train_auc = auc(train_margins, labels)
			test_auc = auc(test_margins, test_labels)
			train_errors.append(train_error)
			test_errors.append(test_error)
			round_errors.append(error)
			train_aucs.append(train_auc)
			test_aucs.append(test_auc)
			msg = "round %d: params=%s, round_err=%.6f, train_err=%.6f, test_err=%.6f, train_auc=%.6f, test_auc=%.6f"
			print msg % (t + 1, params, error, train_error, test_error, train_auc, test_auc)
	if verbose:
		return round_errors, train_errors, test_errors, train_aucs, test_aucs
	else:
		return alphas, predictors
	
def predict(data, alphas, predictors, raw=False):
	predicted = sum([
		alpha * predictor(data)
		for alpha, predictor in zip(alphas, predictors)
	])
	if raw:
		return predicted
	return np.sign(predicted)
	
def test(alphas, predictors, filenames=None, data=None, labels=None):
	if filenames is not None:
		data, labels = load_data(filenames, delimiter=",", label_map={0.0:-1.0,1.0:1.0})
	predicted = predict(data, alphas, predictors)
	return _error(predicted, labels)
	
def _error(predicted, labels):
	return (predicted != labels).sum() / float(len(labels))
	
def _predictor(predictor, params):
	return lambda data: predictor(data, *params)
	
def trial(name, learner, iters):
	# gather the data
	print name
	data, labels = load_data(('data/spambase.data',), delimiter=",", label_map={0.0:-1.0,1.0:1.0})
	state = np.random.get_state()
	np.random.shuffle(data)
	np.random.set_state(state)
	np.random.shuffle(labels)
	i = ceil(0.9 * len(data))
	alphas, predictors = train(
		learner, stump.predict,
		data=data[:i], labels=labels[:i],
		test_data=data[i:], test_labels=labels[i:],
		iters=iters, verbose=False
	)
	train_error = test(alphas, predictors, data=data[:i], labels=labels[:i])
	test_error = test(alphas, predictors, data=data[i:], labels=labels[i:])
	print train_error
	print test_error
	
def main():
	trial('optimal', stump.train, 100)
	#trial('random', stump.random, 1000)
	
if __name__ == '__main__':
	main()