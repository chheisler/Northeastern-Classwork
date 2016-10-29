from os import path
import re
from util import DATA_AXIS, FEATURE_AXIS
import numpy as np
from math import ceil
import stump, adaboost

STEPS = [0.05, 0.10, 0.15, 0.20, 0.30, 0.50, 0.60, 0.70, 1.00]

def uci(folder):
    data, labels = load_data(folder)
    for step in STEPS:
        state = np.random.get_state()
        np.random.shuffle(data)
        np.random.set_state(state)
        np.random.shuffle(labels)
        i = ceil(step * data.shape[DATA_AXIS])
        alphas, predictors = adaboost.train(
            stump.random, stump.predict,
            data=data[:i], labels=labels[:i], iters=500
        )
        train_error = adaboost.test(alphas, predictors, data=data[:i], labels=labels[:i])
        test_error = adaboost.test(alphas, predictors, data=data[i:], labels=labels[i:])
        msg = "sample=%.2f, train_err=%.6f, test_err=%.6f"
        print msg % (step, train_error, test_error)

def load_data(folder):
    # create a configuration
    name = path.basename(path.normpath(folder))
    config_file = open(path.join(folder, name + '.config'), 'r')
    config = tuple(line.strip() for line in config_file)
    config_file.close()
    features = 0
    feature_map = []
    for line in config[1:-2]:
        if line == '-1000':
            feature_map.append(features)
            features += 1
        else:
            vals = line.split()
            vals.pop(0)
            mapping = {
                val: features + j
                for j, val in enumerate(vals)
            }
            feature_map.append(mapping)
            features += len(vals)
    tokens = config[-2].split()
    tokens.pop(0)
    label_map = {
        tokens[0]: -1,
        tokens[1]: 1
    }
    match = re.match(r'(\d+)\s+(\d+)\s+(\d+)', config[0])
    size = int(match.group(1))
    raw_features = int(match.group(2)) + int(match.group(3))
    assert len(feature_map) == raw_features
            
    # load data
    data = np.zeros((size, features))
    labels = np.zeros(size)
    missing = np.zeros((size, raw_features), dtype='bool')
    data_file = open(path.join(folder, name + '.data'), 'r')
    for i, line in enumerate(data_file):
        tokens = line.split()
        labels[i] = label_map[tokens.pop()]
        for j, token in enumerate(tokens):
            if token == '?':
                missing[i][j] = True
            else:
                try:
                    data[i][feature_map[j]] = float(token)
                except ValueError, TypeError:
                    data[i][feature_map[j][token]] = 1
    assert i == data.shape[DATA_AXIS] - 1
    
    # fix missing
    replace = np.zeros(raw_features)
    present = np.logical_not(missing)
    for j in range(raw_features):
        if isinstance(feature_map[j], int):
            total = np.dot(data[:,feature_map[j]], present[:,j])
            count = float(present[:,j].sum())
            replace[j] = total / count 
        else:
            features = [feature for value, feature in feature_map[j].iteritems()]
            counts = data[:,features].sum(axis=DATA_AXIS)
            replace[j] = features[list(counts).index(max(counts))]
    for i in range(size):
        for j in range(raw_features):
            if missing[i][j]:
                if isinstance(feature_map[j], int):
                    data[i][feature_map[j]] = replace[j]
                else:
                    data[i][replace[j]] = 1
                    
    # sanity check
    for mapping in feature_map:
        if isinstance(mapping, dict):
            features = [feature for value, feature in mapping.iteritems()]
            counts = data[:,features].sum(axis=DATA_AXIS)
            assert counts.sum() == size
    return data, labels
    
def main():
    print "crx"
    uci('data/crx')
    #print "\nvote"
    #uci('data/vote')
    
if __name__ == '__main__':
    main()