from util import load_data, DATA_AXIS, FEATURE_AXIS
import numpy as np

def train(data, labels):
	# transform the data
	means = np.zeros(data.shape[FEATURE_AXIS])
	for j in range(data.shape[FEATURE_AXIS]):
		column = data[:,j]
		means[j] = column[~np.isnan(column)].mean()
	data = prep_data(data, means)
	
	# learn on the transformed
	priors = np.zeros(2)
	probs = np.zeros((2, 2, data.shape[FEATURE_AXIS]))
	for label in range(2):
		priors[label] = (labels == label).sum() / float(len(labels))
		for j in range(data.shape[FEATURE_AXIS]):
			column = data[:,j]
			i = np.where((~np.isnan(column)) & (labels == label))[0]
			print column[i]
			print column[i].astype('int64')
			print np.bincount(column[i].astype('int64'), minlength=2).dtype
			probs[label,:,j] = np.bincount(column[i].astype('int64'), minlength=2)
			probs[label,:,j] = (probs[label,:,j] + 1) / (len(i) + 2)
	return means, priors, probs
	
def test(data, labels, means, priors, probs):
    data = prep_data(data, means)
    predicted = np.apply_along_axis(
        lambda datum: predict(datum, priors, probs),
        FEATURE_AXIS,
        data
    )
    return (predicted != labels).sum() / float(len(labels))
    
def predict(datum, priors, probs):
    best_prob = 0.0
    best_label = 0
    for label in range(2):
        prob = priors[label]
        for j in range(len(datum)):
			if not np.isnan(datum[j]):
				prob *= probs[label][datum[j]][j]
        if prob > best_prob:
            best_prob = prob
            best_label = label
    return best_label
	
def prep_data(data, means):
	data[data <= means] = 0.0
	data[data > means] = 1.0
	return data
	
def main():
	train_data, train_labels = load_data(('data/20_percent_missing_train.txt',), delimiter=',')
	test_data, test_labels = load_data(('data/20_percent_missing_test.txt',), delimiter=',')
	means, priors, probs = train(train_data, train_labels)
	train_error = test(train_data, train_labels, means, priors, probs)
	test_error = test(test_data, test_labels, means, priors, probs)
	print "train_err=%.6f test_err=%.6f" % (train_error, test_error)
	
if __name__ == '__main__':
	main()