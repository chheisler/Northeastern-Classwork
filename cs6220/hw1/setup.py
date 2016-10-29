from argparse import ArgumentParser
from os import remove, makedirs, path
from shutil import rmtree
from zipfile import ZipFile

# parse arguments from the command line
parser = ArgumentParser()
parser.add_argument('--clean', '-c', action='store_true')
args = parser.parse_args()

# create additional data files
def add_files():
    zipfile = ZipFile('HW1_data.zip', 'r')
    file = zipfile.open('train-1000-100.csv', 'r')
    file50 = open('train-50(1000)-100.csv', 'w')
    file100 = open('train-100(1000)-100.csv', 'w')
    file150 = open('train-150(1000)-100.csv', 'w')
    for i, line in enumerate(file):
        if i == 150:
            return
        if i < 50:
            file50.write(line)
        if i < 100:
            file100.write(line)
        file150.write(line)

# create a directory if it does not exist
def make_dir(name):
    if not path.exists(name):
        makedirs(name)

# set up the work environment
def setup():
    # create directories for generated logs and plots
    make_dir('logs')
    make_dir('logs/q1')
    make_dir('logs/q2')
    make_dir('logs/q3')
    make_dir('plots')
    make_dir('plots/q1')
    make_dir('plots/q2')
    make_dir('plots/q3')
    
    # create additional data sets
    add_files()
    
# clean up the the work environment
def cleanup():
    # remove plots
    rmtree('logs')
    rmtree('plots')
    
    # remove generated data files
    remove('train-50(1000)-100.csv')
    remove('train-100(1000)-100.csv')
    remove('train-150(1000)-100.csv')

def main():
    if args.clean:
        cleanup()
    else:
        setup()
       
if __name__ == '__main__':
    main() 
