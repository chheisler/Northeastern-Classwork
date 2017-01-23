import numpy as np
from pcc import pcc
from util import load_data, DATA_AXIS, FEATURE_AXIS, zscore, accuracy
from knn import predict

# number of nearest neighbors to use
k = 7

def main():
    # load and normalize the data
    data, labels = load_data(
        'veh-prime.arff',
        filterFn = lambda line: len(line.strip()) > 0 and line[0] != '@',
        labelFn = lambda label: {'car': 1.0, 'noncar': 0.0}[label]
    )
    data = zscore(data)
    n = data.shape[DATA_AXIS]
    d = data.shape[FEATURE_AXIS]

    # score each feature in the data
    scores = np.zeros(d)
    for j in range(d):
        scores[j] = abs(pcc(data[:,j], labels))
    feature_indices = np.flipud(scores.argsort())
    for index in feature_indices:
        print "f=%d,|r|=%f" % (index + 1, scores[index])
    print

    # try adding features in order of score
    data_indices = [x for x in range(data.shape[DATA_AXIS])]
    for m in range(1,d+1):
        correct = 0.0
        subdata = data[:,feature_indices[:m]]
        for i in range(n):
            indices = data_indices[:i] + data_indices[i+1:]
            predicted = predict(
                subdata[None,i],
                subdata[indices],
                labels[indices], k
            )      
            if predicted[0] == labels[i]:
                correct += 1
        print "m=%d,accuracy=%f" % (m, correct / n)
    print

if __name__ == '__main__':
    main()
