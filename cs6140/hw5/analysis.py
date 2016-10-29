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
    sorted = np.argsort(data, axis=DATA_AXIS).transpose()
    weights = np.zeros(data.shape[DATA_AXIS])
    weights.fill(1.0 / data.shape[DATA_AXIS])
    alphas = np.zeros(iters)
    predictors = np.zeros(iters, dtype='object')
    confidences = np.zeros(data.shape[FEATURE_AXIS])
    if verbose:
        train_errors = []
        test_errors = []
        train_margins = np.zeros(data.shape[DATA_AXIS])
        test_margins = np.zeros(test_data.shape[DATA_AXIS])
        round_errors = []
    for t in range(iters):
        params = learner(data, labels, weights, sorted)
        predictors[t] = _predictor(predictor, params)
        predicted = predictors[t](data)
        error = np.dot(predicted != labels, weights)
        alphas[t] = 0.5 * log((1.0 - error) / error)
        weights *= e ** (-alphas[t] * labels * predicted)
        weights /= weights.sum()
        feature, threshold = params
        confidences[feature] += (labels * alphas[t] * predicted).sum()
        if verbose:
            train_margins += predict(data, alphas[:t+1], predictors[:t+1], raw=True)
            test_margins += predict(test_data, alphas[:t+1], predictors[:t+1], raw=True)
            train_error = _error(np.sign(train_margins), labels)
            test_error = _error(np.sign(test_margins), test_labels)
            train_errors.append(train_error)
            test_errors.append(test_error)
            round_errors.append(error)
            msg = "round %d: round_err=%.6f, train_err=%.6f, test_err=%.6f"
            print msg % (t + 1, error, train_error, test_error)
    confidences /= (labels * predict(data, alphas, predictors, raw=True)).sum()
    print "best features:", np.flipud(np.argsort(confidences))[:10]
    if verbose:
        return round_errors, train_errors, test_errors
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
    
def trial(learner, iters):
    data, labels = load_data(('data/spambase.data',), delimiter=",", label_map={0.0:-1.0,1.0:1.0})
    state = np.random.get_state()
    np.random.shuffle(data)
    np.random.set_state(state)
    np.random.shuffle(labels)
    i = ceil(0.9 * len(data))
    round_errs, train_errs, test_errs = train(
        learner, stump.predict,
        data=data[:i], labels=labels[:i],
        test_data=data[i:], test_labels=labels[i:],
        iters=iters, verbose=True
    )
    
def polluted_trial():
    train_data, train_labels = load_data(
        ('data/spam_polluted/train_feature.txt',),
        labels_filenames=('data/spam_polluted/train_label.txt',),
        label_map={0.0: -1.0, 1.0: 1.0}
    )
    test_data, test_labels = load_data(
        ('data/spam_polluted/test_feature.txt',),
        labels_filenames=('data/spam_polluted/test_label.txt',),
        label_map={0.0: -1.0, 1.0: 1.0}
    )
    train(
        stump.train, stump.predict,
        data=train_data, labels=train_labels,
        test_data=test_data, test_labels=test_labels,
        iters=100, verbose=True
    )
    
def main():
    trial(stump.train, 300)
   #polluted_trial()
    
    
    
    
if __name__ == '__main__':
    main()