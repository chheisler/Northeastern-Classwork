import numpy as np
from math import e
from random import choice

INPUT_SIZE = 8
HIDDEN_SIZE = 3
OUTPUT_SIZE = 8

def load_data():
	inputs = np.array([
		[1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[1.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
		[1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
		[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
		[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
		[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
	])
	targets = np.array([
		[1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0],
		[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0],
		[0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
		[0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0],
		[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0],
		[0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0]
	])
	return inputs, targets
	
def train(rate, threshold):
	# initialize inputs, targets and weights
	inputs, targets = load_data()
	input_weights = np.random.rand(HIDDEN_SIZE + 1, INPUT_SIZE + 1)
	hidden_weights = np.random.rand(OUTPUT_SIZE, HIDDEN_SIZE + 1)
	error = mse(inputs, targets, input_weights, hidden_weights)
	
	# iteratively seek optimum
	while True:
		index = choice(range(len(inputs)))
		input = inputs[index]
		target = targets[index]
		result = feed_forward(input, input_weights, hidden_weights)
		hidden, output, hidden_net, output_net = result
		
		# update the input weights
		for j in range(1,len(hidden)):
			for i in range(len(input)):
				total = 0.0
				for k in range(len(output)):
					total += (target[k] - output[k]) \
					* sigmoid_prime(output_net[k]) * hidden_weights[k][j]
				input_weights[j][i] += rate * total \
				* sigmoid_prime(hidden_net[j]) * input[i]
			
		# update the hidden weights
		for k in range(len(output)):
			for j in range(len(hidden)):
				hidden_weights[k][j] += rate * (target[k] - output[k]) \
				* sigmoid_prime(output_net[k]) * hidden[j]
				
		# check if the error update is small enough to stop
		new_error = mse(inputs, targets, input_weights, hidden_weights)
		#print "error: %f new error: %f" % (error, new_error)
		if abs(new_error - error) < threshold:
			return input_weights, hidden_weights
		error = new_error
		
def feed_forward(input, input_weights, hidden_weights):
	hidden = np.zeros(HIDDEN_SIZE + 1)
	hidden_net = np.zeros(HIDDEN_SIZE + 1)
	hidden[0] = 1.0
	for j in range(1, len(hidden)):
		hidden_net[j] = np.dot(input_weights[j].transpose(), input)
		hidden[j] = sigmoid(hidden_net[j])
	output = np.zeros(OUTPUT_SIZE)
	output_net = np.zeros(OUTPUT_SIZE)
	for k in range(len(output)):
		output_net[k] = np.dot(hidden_weights[k].transpose(), hidden)
		output[k] = sigmoid(output_net[k])
	return hidden, output, hidden_net, output_net
	
def sigmoid(z):
	return 1.0 / (1.0 + e ** -z)
	
def sigmoid_prime(z):
	return sigmoid(z) * (1.0 - sigmoid(z))
	
def mse(inputs, targets, input_weights, hidden_weights):
	error = 0.0
	for index in range(len(inputs)):
		input = inputs[index]
		target = targets[index]
		result = feed_forward(input, input_weights, hidden_weights)
		hidden, output, hidden_net, output_net = result
		diff = target - output
		error += np.dot(diff.transpose(), diff)
	return error / (OUTPUT_SIZE * len(inputs))
	
def trial(input, target, input_weights, hidden_weights):
	result = feed_forward(input, input_weights, hidden_weights)
	hidden, output, hidden_net, output_net = result
	for i in range(len(output)):
		output[i] = round(output[i])
	mistakes = (target - output != 0).sum()
	for i in range(len(hidden)):
		hidden[i] = round(hidden[i])
	print "target=%s hidden=%s output=%s" % (target, hidden[1:], output)
	return int(mistakes != 0)
	
def main():
	input_weights, hidden_weights = train(5, 0.000000001)
	for j in range(1, HIDDEN_SIZE + 1):
		for i in range(INPUT_SIZE + 1):
			print "w_(j=%d,i=%d)=%f" % (j, i, input_weights[j][i])
	for k in range(OUTPUT_SIZE):
		for j in range(HIDDEN_SIZE + 1):
			print "w_(k=%d,j=%d)=%f" % (k + 1, j, input_weights[j][i]) 
	print "\n"
	inputs, targets = load_data()
	mistakes = 0
	for index in range(len(inputs)):
		input = inputs[index]
		target = targets[index]
		mistakes += trial(input, target, input_weights, hidden_weights)
	print "\nmistakes=%d" % mistakes
	
if __name__ == '__main__':
	main()