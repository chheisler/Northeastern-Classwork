from util import load_data, FEATURE_AXIS
from housing_tree import Regressor
import numpy as np
from sys import stdout

def train(filenames, iters=10):
    data, labels = load_data(filenames)
    predictors = np.zeros(iters, dtype='object')
    for t in range(iters):
        regressor = Regressor()
        regressor.train(data, labels, max_depth=2)
        predictors[t] = _predictor(regressor)
        labels -= np.apply_along_axis(predictors[t], FEATURE_AXIS, data)
    return predictors
    
def _predictor(regressor):
    return lambda datum: regressor.predict(datum)
    
def predict(data, predictors):
    return sum([
        np.apply_along_axis(predictor, FEATURE_AXIS, data)
        for predictor in predictors
    ])
    
def test(filenames, predictors):
    data, labels = load_data(filenames)
    predicted = predict(data, predictors)
    diff = predicted - labels
    return np.dot(diff, diff) / float(len(labels))
    
def main():
    for i in range(1, 21):
        predictors = train(('data/housing_train.txt',), iters=i)
        train_error = test(('data/housing_train.txt',), predictors)
        test_error = test(('data/housing_test.txt',), predictors)
        print "iters=%d, train_err=%.6f, test_err=%.6f" % (i, train_error, test_error)
    
if __name__ == '__main__':
    main()