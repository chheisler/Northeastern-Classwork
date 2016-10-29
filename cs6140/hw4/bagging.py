import numpy as np
from util import load_data, trial
from spam_tree import Classifier
from sys import stdout

def train(filenames, iters=50):
    data, labels = load_data(filenames, delimiter=",")
    predictors = np.zeros(iters, dtype='object')
    stdout.write('iteration ')
    for t in range(iters):
        stdout.write('%d... ' % (t + 1))
        indices = np.random.choice(len(data), size=len(data))
        sample_data = data[indices]
        sample_labels = labels[indices]
        predictors[t] = Classifier()
        predictors[t].train(sample_data, sample_labels, max_depth=2)
    stdout.write('\n')
    return (predictors,)
    
def predict(data, predictors):
    predicted = np.zeros(len(data))
    # for i, datum in enumerate(data):
        # for predictor in predictors:
            # predicted[i] += predictor.predict(datum)
    # return predicted > (len(predictors) / 2.0)
    for predictor in predictors:
        fn = lambda datum: predictor.predict(datum)
        predicted += np.apply_along_axis(fn, 1, data)
    return predicted > (len(predictors) / 2.0)
    #return predicted
    
def test(filenames, predictors):
    data, labels = load_data(filenames, delimiter=",")
    predicted = predict(data, predictors)
    return (predicted != labels).sum() / float(len(labels))
    
def main():
    trial('bagging', train, test)
    
if __name__ == '__main__':
    main()