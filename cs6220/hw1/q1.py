from util import load_data, mse
from regress import regress, predict
from matplotlib import pyplot
from zipfile import ZipFile
from os import makedirs
from os.path import exists
from sys import stdout
import logging


# plot MSE for linear regression with lagrange multipliers
def plot_regression(name, train_file, test_file):
    stdout.write("Drawing plot for data set '%s'... " % name)
    stdout.flush()
    train_data, train_labels = load_data(train_file, dummy=1.0)
    test_data, test_labels = load_data(test_file, dummy=1.0)
    lagranges = [lagrange for lagrange in range(151)]
    train_errors = []
    test_errors = []
    log = open('logs/q1/%s.log' % name, 'w')

    # for each lagrange regress and calculate error
    for lagrange in lagranges:
        coefs = regress(train_data, train_labels, lagrange)
        predicted = predict(train_data, coefs)
        train_error = mse(train_labels, predicted)
        train_errors.append(train_error)
        predicted = predict(test_data, coefs)
        test_error = mse(test_labels, predicted)
        test_errors.append(test_error)
        message = 'lagrange=%d train_error=%.3f test_error=%.3f\n'
        log.write(message % (lagrange, train_error, test_error))

    # plot errors as a function of the lagrange
    pyplot.figure()
    pyplot.xlim(0, 150)
    pyplot.title("Data set '%s'" % name)
    pyplot.xlabel('Lagrange multiplier')
    pyplot.ylabel('Mean squared error')
    pyplot.plot(lagranges, train_errors, label="Training")
    pyplot.plot(lagranges, test_errors, label="Testing")
    pyplot.legend(loc='lower right')
    pyplot.savefig('plots/q1/%s.png' % name)
    stdout.write("done.\n")
    stdout.write("Plot image written to 'plots/q1/%s.png'.\n" % name)
    stdout.write("Plot data written to '%s'.\n" % log.name)
    stdout.flush()
    log.close()
     
def main():
    zipfile = ZipFile('HW1_data.zip', 'r')
    
    # draw plots for dataset '100-10'
    train_file = zipfile.open('train-100-10.csv', 'r')
    test_file = zipfile.open('test-100-10.csv', 'r') 
    plot_regression('100-10', train_file, test_file)

    # draw plots for dataset '100-100'
    train_file = zipfile.open('train-100-100.csv', 'r')
    test_file = zipfile.open('test-100-100.csv', 'r')
    plot_regression('100-100', train_file, test_file)

    # draw plots for dataset '1000-100'
    train_file = zipfile.open('train-1000-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot_regression('1000-100', train_file, test_file)

    # draw plots for dataset '50(1000)-100'
    train_file = open('train-50(1000)-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot_regression('50(1000)-100', train_file, test_file)

    # draw plots for dataset '100(1000)-100'
    train_file = open('train-100(1000)-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot_regression('100(1000)-100', train_file, test_file)

    # draw plots for dataset '150(1000)-100'
    train_file = open('train-150(1000)-100.csv', 'r')
    test_file = zipfile.open('test-1000-100.csv', 'r')
    plot_regression('150(1000)-100', train_file, test_file)
    
    # draw plots for dataset 'wine'
    train_file = zipfile.open('train-wine.csv', 'r')
    test_file = zipfile.open('test-wine.csv', 'r')
    plot_regression('wine', train_file, test_file)

 
if __name__ == '__main__':
    main()
