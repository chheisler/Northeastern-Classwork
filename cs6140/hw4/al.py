import numpy as np
import stump, adaboost
from util import load_data
from math import ceil

def active_learning(filenames, random=False):
    data, labels = load_data(filenames, delimiter=",", label_map={0.0:-1.0,1.0:1.0})
    total = len(data)
    state = np.random.get_state()
    np.random.shuffle(data)
    np.random.set_state(state)
    np.random.shuffle(labels)
    step = int(ceil(0.025 * len(labels)))
    sample_data = np.copy(data[-step*2:])
    sample_labels = np.copy(labels[-step*2:])
    data = np.delete(data, np.s_[-step*2:], axis=0)
    labels = np.delete(labels, np.s_[-step*2:])
    for x in range(19):
        assert len(data) + len(sample_data) == total
        assert len(labels) + len(sample_labels) == total
        
        # train using data
        alphas, predictors = adaboost.train(
            stump.random, stump.predict,
            data=sample_data, labels=sample_labels, iters=1000
        )
        
        # calculate the error
        train_error = adaboost.test(alphas, predictors, data=sample_data, labels=sample_labels)
        test_error = adaboost.test(alphas, predictors, data=data, labels=labels)
        sample = (x + 2) * 0.025
        msg = "sample=%.3f, train_err=%.6f, test_err=%.6f"
        print msg % (sample, train_error, test_error)
        
        # pick new sample points
        if random:
            sample_data = np.append(sample_data, data[-step:], axis=0)
            sample_labels = np.append(sample_labels, labels[-step:])
            data = np.delete(data, np.s_[-step:], axis=0)
            labels = np.delete(labels, np.s_[-step:])
        else:
            margins = np.absolute(sum([
                alpha * predictor(data)
                for alpha, predictor in zip(alphas, predictors)
            ]))
            sorted = margins.argsort()[:step]
            sample_data = np.append(sample_data, data[sorted], axis=0)
            sample_labels = np.append(sample_labels, labels[sorted])
            data = np.delete(data, sorted, axis=0)
            labels = np.delete(labels, sorted)
            
def main():
    print "active learning"
    active_learning(('data/spambase.data',), random=False)
    print "\nrandom"
    active_learning(('data/spambase.data',), random=True)
    
if __name__ == '__main__':
    main()