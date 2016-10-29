from random import shuffle
from sys import stdout
import numpy as np
from zipfile import ZipFile
from matplotlib import pyplot
from util import load_data, mse, DATA_AXIS
from regress import regress, predict

# plot learning curves for a data set for lagranges 1, 46 and 150
def plot(name, train_file, test_file):
    train_data, train_labels = load_data(train_file, dummy=1.0)
    test_data, test_labels = load_data(test_file, dummy=1.0)
    num_samples = [x for x in range(1, train_data.shape[DATA_AXIS] + 1)]
    log = open('logs/q2/%s.log' % name, 'w')
    stdout.write("Drawing plot for data set '%s'... " % name)
    stdout.flush()
    
    # set up the plot
    pyplot.figure()
    pyplot.title("Data set '%s'" % name)
    pyplot.xlabel('Sample size')
    pyplot.ylabel('Mean squared error')
    pyplot.xlim(1, len(num_samples))
    
    # for each lagrange plot a learning curve
    for lagrange in (1, 46, 150):
        errors = curve(
            train_data, train_labels,
            test_data, test_labels,
            lagrange
        )
        pyplot.plot(num_samples, errors, label='$\lambda=%d$' % lagrange)
        for i, error in enumerate(errors):
            message = 'lagrange=%d samples=%d error=%.3f\n'
            log.write(message % (lagrange, i + 1, error))
            
    # finalize the plot
    pyplot.legend(loc='upper right')
    pyplot.savefig('plots/q2/%s.png' % name)
    stdout.write("done.\n")
    stdout.write("Plot image written to 'plots/q2/%s.png'.\n" % name)
    stdout.write("Plot data written to '%s'.\n" % log.name)
    stdout.flush()
    log.close()
    
    
# get the average error for a learning curve over 10 trials
def curve(train_data, train_labels, test_data, test_labels, lagrange):
    avg_errors = np.zeros(train_data.shape[DATA_AXIS])
    for trial in range(10):
        indices = [i for i in range(train_data.shape[DATA_AXIS])]
        shuffle(indices)
        for num_samples in range(1, train_data.shape[DATA_AXIS] + 1):
            data = train_data[indices[:num_samples]]
            labels = train_labels[indices[:num_samples]]
            coefs = regress(data, labels, lagrange)
            predicted = predict(test_data, coefs)
            avg_errors[num_samples - 1] += mse(test_labels, predicted)
    return avg_errors / 10
    
    
def main():
    zipfile = ZipFile('HW1_data.zip', 'r')

    # draw plots for data set '100-10'
    train_file = zipfile.open('train-100-10.csv', 'r')
    test_file = zipfile.open('test-100-10.csv', 'r')
    plot('100-10', train_file, test_file)
    
    # draw plots for data set '100-100'
    train_file = zipfile.open('train-100-100.csv', 'r')
    test_file = zipfile.open('test-100-100.csv', 'r')
    plot('100-100', train_file, test_file)

    # draw plots for data set '1000-100'
    train_file = zipfile.open('train-1000-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot('1000-100', train_file, test_file)

    # draw plots for data set '50(1000)-100'
    train_file = open('train-50(1000)-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot('50(1000)-100.csv', train_file, test_file)
    
    # draw plots for data set '100(1000)-100'
    train_file = open('train-100(1000)-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot('100(1000)-100.csv', train_file, test_file)

    # draw plots for data set '150(1000)-100'
    train_file = open('train-150(1000)-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot('150(1000)-100', train_file, test_file)

    # draw plots for data set 'wine'
    train_file = zipfile.open('train-wine.csv', 'r')
    test_file = zipfile.open('test-wine.csv', 'r')
    plot('wine', train_file, test_file)
    
    
if __name__ == '__main__':
    main()
    
