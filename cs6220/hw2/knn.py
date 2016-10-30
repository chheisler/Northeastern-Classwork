from math import sqrt
import numpy as np
from util import load_data, FEATURE_AXIS, mse, zscore

# k values to test
K = (1, 5, 11, 21, 41, 61, 81, 101, 201, 401)

# number of samples to print labels for
NUM_SAMPLES = 50

# predict labels for data using k-nearest-neighbors
def predict(unlabeled, data, labels, k):
    predictor = lambda datum: _predict(datum, data, labels, k)
    return np.apply_along_axis(predictor, FEATURE_AXIS, unlabeled)

def _predict(datum, data, labels, k):
    distances = np.sqrt(((data - datum) ** 2).sum(axis=FEATURE_AXIS))
    indices = distances.argsort()[:k]
    return np.argmax(np.bincount(labels[indices].astype('int64')))

def main():
    train_data, train_labels = load_data('spam_train.csv', start=1)
    test_data, test_labels = load_data('spam_test.csv', start=1)

    # train and test without normalization
    print "without normalization" 
    for k in K:
        predicted = predict(test_data, train_data, train_labels, k)
        error = mse(test_labels, predicted)
        print "k=%d accr=%.3f" % (k, 1.0 - error)
    print
    
    # train and test with normalization
    print "with normalization"
    train_data = zscore(train_data)
    test_data = zscore(test_data)
    for k in K:
        predicted = predict(test_data, train_data, train_labels, k)
        error = mse(test_labels, predicted)
        print "k=%d accr=%.3f" % (k, 1.0 - error)
    print

    # report labels for first 50 data points
    print "labels for first 50 data points"
    test_data = test_data[:NUM_SAMPLES]
    predicted = np.zeros((len(K), NUM_SAMPLES))
    for i, k in enumerate(K):
        predicted[i] = predict(test_data, train_data, train_labels, k)
    print ' k= %s' % ' '.join(['%3d' % k for k in K])
    for i in range(NUM_SAMPLES):
        labels = ['yes' if y == 1 else 'no ' for y in predicted[:,i]]
        print '%2d: %s' % (i + 1, ' '.join(labels))
        
if __name__ == '__main__':
    main()
