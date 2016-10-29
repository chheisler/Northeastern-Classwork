from random import shuffle
from regress import regress, predict
from math import ceil
from sys import maxint, stdout
from util import load_data, mse, DATA_AXIS
from zipfile import ZipFile

NUM_FOLDS = 10

def cross_validate(name, file):
    data, labels = load_data(file, dummy=1.0)
    log = open('logs/q3/%s.log' % name, 'w')
    stdout.write("Evaluating data set '%s'..." % name)
    stdout.flush()
     
    # split the data into folds
    indices = [i for i in range(data.shape[DATA_AXIS])]
    shuffle(indices)
    fold_size = ceil(float(data.shape[DATA_AXIS]) / NUM_FOLDS)

    # evaluate each lagrange
    best_error = maxint
    for lagrange in range(0, 151):
        avg_error = 0.0

        # try each fold average errors
        for i in range(NUM_FOLDS):
            low = int(i * fold_size)
            high = int((i + 1) * fold_size);
            train_indices = indices[:low] + indices[high:]
            test_indices = indices[low:high]
            coefs = regress(data[train_indices], labels[train_indices], lagrange)
            predicted = predict(data[test_indices], coefs)
            error = mse(labels[test_indices], predicted)
            avg_error += error / NUM_FOLDS
            message = 'lagrange=%d fold=%d error=%.3f\n'
            log.write(message % (lagrange, i, error))
            
        # update best error and lagrange if result is better
        if avg_error < best_error:
            best_error = avg_error
            best_lagrange = lagrange
    
    # report the results
    stdout.write('done.\n')
    stdout.write('Best Lagrange value is %d.\n' % best_lagrange)
    stdout.write('Best error is %.3f.\n' % best_error)
    stdout.write("Logs written to '%s'.\n" % log.name)
    stdout.flush()
    log.close()
    
    
def main():
    zipfile = ZipFile('HW1_data.zip', 'r')
    
    # evaluate best Lagrange for data set '100-10'
    file = zipfile.open('train-100-10.csv', 'r')
    cross_validate('100-10', file)
    
    # evaluate best Lagrange for data set '100-100'
    file = zipfile.open('train-100-100.csv', 'r')
    cross_validate('100-100', file)
    
    # evaluate best Lagrange for data set '1000-100'
    file = zipfile.open('train-1000-100.csv', 'r')
    cross_validate('1000-100', file)
    
    # evaluate best Lagrange for data set '50(1000)-100'
    file = open('train-50(1000)-100.csv', 'r')
    cross_validate('50(1000)-100', file)
    
    # evaluate best Lagrange for data set '100(1000)-100'
    file = open('train-100(1000)-100.csv', 'r')
    cross_validate('100(1000)-100', file)
    
    # evaluate best Lagrange for data set '150(1000)-100'
    file = open('train-150(1000)-100.csv', 'r')
    cross_validate('150(1000)-100', file)
    
    # evaluate best Lagrange for data set 'wine'
    file = zipfile.open('train-wine.csv', 'r')
    cross_validate('wine', file)
    
    
if __name__ == '__main__':
    main()
    
