from util import load_data, zscore, accuracy, DATA_AXIS, FEATURE_AXIS
import numpy as np
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

    # initialize set of unused features
    data_indices = [x for x in range(data.shape[DATA_AXIS])]
    candidates = set([j for j in range(d)])
    features = []
    best_accr = 0.0

    # search for the best feature to add next
    while len(candidates) > 0:
        best_candidate = None
        for candidate in candidates:
            test_features = features + [candidate]
            subdata = data[:,test_features]

            # run LOOCV and find average accuracy
            correct = 0.0
            for i in range(n):
                indices = data_indices[:i] + data_indices[i+1:]
                predicted = predict(
                    subdata[None,i],
                    subdata[indices],
                    labels[indices], k
                )
                if predicted[0] == labels[i]:
                    correct += 1
            accr = correct / n

            # update best accuracy if better
            if (accr > best_accr):
                best_accr = accr
                best_candidate = candidate

        # update set of features or break if none found    
        if best_candidate is None:
            break
        else:
            candidates.remove(best_candidate)
            features.append(best_candidate)
            pretty_features = [index + 1 for index in features]
            msg = "features=%s,accuracy=%f"
            print msg % (pretty_features, best_accr)
    print

if __name__ == '__main__':
    main()
