import numpy as np
from os import mkdir
from shutil import rmtree
from random import shuffle

DATA_AXIS = 0
FEATURE_AXIS = 1
NUM_FOLDS = 10

def load_data(filenames, delimiter=None, dummy=False, labeled=True):
    data = []
    labels = []
    for filename in filenames:
        file = open(filename, 'r')
        for line in file:
            tokens = line.strip().split(delimiter)
            try:
                if labeled:
                    labels.append(float(tokens.pop()))
                datum = [float(token) for token in tokens]
                if dummy:
                    datum.insert(0, 1.0)
                data.append(datum)
            except IndexError:
                break
        file.close()
    if labeled:
        return np.array(data), np.array(labels)
    else:
        return np.array(data)
    
def trial(name, train, test):
    # create a temporary directory
    try:
        mkdir('./tmp')
    except OSError:
        pass
        
    # create folds of data
    file = open('data/spambase.data', 'r')
    lines = [line for line in file]
    file.close()
    shuffle(lines)
    folds = [open('tmp/fold%d.data' % x, 'w') for x in range(NUM_FOLDS)]
    for index, line in enumerate(lines):
        folds[index % NUM_FOLDS].write(line)
    for fold in folds:
        fold.close()
        
    # do set of trials using generated folds
    print "\n%s:" % name
    # print r'\begin{tabular}{ r|c|c|c|c|c| } \multicolumn{1}{r}{}'
    # print r'& \multicolumn{1}{c}{false positive rate}'
    # print r'& \multicolumn{1}{c}{false negative rate}'
    # print r'& \multicolumn{1}{c}{error rate} \\'
    # print r'\cline{2-4}'
    # msg = r'%s & \shortstack{train=%.3f \\ test=%.3f}' \
    # + r'& \shortstack{train=%.3f \\ test=%.3f}' \
    # + r'& \shortstack{train=%.3f \\ test=%.3f} \\' \
    # + r'\cline{2-4}'
    
    msg = "%s: train_fp=%.3f, train_fn=%.3f, train_err=%.3f, test_fp=%.3f, test_fn=%.3f test_err=%.3f"
    folds = ['tmp/fold%d.data' % x for x in range(NUM_FOLDS)]
    train_false_positives = []
    train_false_negatives = []
    train_errors = []
    test_false_positives = []
    test_false_negatives = []
    test_errors = []
    for x in range(len(folds)):
        args = train(folds[:-1])
        train_false_positive, train_false_negative, train_error = test(folds[:-1], *args)
        test_false_positive, test_false_negative, test_error = test((folds[-1],), *args)
        train_false_positives.append(train_false_positive)
        train_false_negatives.append(train_false_negative)
        train_errors.append(train_error)
        test_false_positives.append(test_false_positive)
        test_false_negatives.append(test_false_negative)
        test_errors.append(test_error)
        folds = folds[1:] + folds[0:1]
        print msg % ("fold %d" % (x + 1),
            train_false_positive, test_false_positive,
            train_false_negative, test_false_negative,
            train_error, test_error)
        
    train_false_positive = sum(train_false_positives) / float(len(train_false_positives))
    train_false_negative = sum(train_false_negatives) / float(len(train_false_negatives))
    train_error = sum(train_errors) / len(train_errors)
    test_false_positive = sum(test_false_positives) / float(len(test_false_positives))
    test_false_negative = sum(test_false_negatives) / float(len(test_false_negatives))
    test_error = sum(test_errors) / len(test_errors)
    print msg % ("average", train_false_positive, test_false_positive,
        train_false_negative, test_false_negative,
        train_error, test_error)
    #print r'\end{tabular}'
    rmtree('./tmp')