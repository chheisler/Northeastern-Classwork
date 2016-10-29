from django.core.management.base import BaseCommand, CommandError
from overwatch import models
from overwatch.util import make_data
import numpy as np
from random import random, randint, choice
from bitarray import bitarray

class Command(BaseCommand):
	def add_arguments(self, parser):
		parser.add_argument('-m', '--model', required=True)
		parser.add_argument('-f', '--features', type=int, default=256)
		parser.add_argument('-n', '--name', required=True)
		parser.add_argument('-s', '--stop')
		parser.add_argument(
			'-S', '--selector',
			choices=['relief', 'chi_square', 'random'],
			default='relief'
		)
		parser.add_argument('-a', '--alpha', type=float, default=1.0)
		parser.add_argument('-t', '--trials', type=int, default=1)
		
	def handle(self, *args, **options):
		model = getattr(models, options['model'])
		features = _findfeatures(
			model,
			options['features'],
			options['selector'],
			options.get('stop')
		)
		avg_train_error = 0.0
		avg_test_error = 0.0
		for i in range(options['trials']):
			test_ids = _train(model, features, options['name'], options['alpha'])
			train_error, test_error = _test(model, options['name'], test_ids)
			avg_train_error += train_error / options['trials']
			avg_test_error += test_error / options['trials']
		print "avg_train_error=%.6f avg_test_error=%.6f\n" % (avg_train_error, avg_test_error)
		_margins(model, options['name'])
		
def _findfeatures(model, d, selector, stop):
	"""Select set of features to use from candidates."""
	features = set()
	for object in model.objects.filter(label__isnull=False):
		features |= object.get_features()
	if stop is not None:
		file = open(stop, 'r')
		features -= set(line.strip() for line in file)
		file.close()
	features = frozenset(features)
	if selector == 'relief':
		scores = _relief(model, features)
	elif selector == 'chi_square':
		scores = _chi_square(model, features)
	elif selector == 'random':
		scores = _random(model, features)
	else:
		raise CommandError("invalid selector '%s'" % selector)
	indices = frozenset(np.flipud(np.argsort(scores))[:d])
	features = [feature for j, feature in enumerate(features) if j in indices]
	print "features=%s\n".encode('utf-8') % ','.join(features).encode('utf-8')
	return features

def _random(model, features):
	return np.random.rand(len(features))
	
def _relief(model, features):
	data, labels = make_data(model, features)
	scores = np.zeros(data.shape[1])
	true_indices = np.where(labels == 1)[0]
	false_indices = np.where(labels == -1)[0]
	updates = 0
	while updates < 10000:
		i = randint(0, len(data) - 1)
		j = choice(true_indices)
		k = choice(false_indices)
		if i == j or i == k:
			continue
		scores -= labels[i] * labels[j] * (data[i] - data[j]) ** 2
		scores -= labels[i] * labels[k] * (data[i] - data[k]) ** 2
		updates += 1
	return scores
	
def _chi_square(model, features):
	true = 0.0
	false = 0.0
	n10 = np.zeros(len(features))
	n11 = np.zeros(len(features))
	for object in model.objects.filter(label__isnull=False):
		datum = object.get_datum(features)
		if object.label:
			n11 += datum
			true += 1.0
		else:
			n10 += datum
			false += 1.0
	n00 = false - n10
	n01 = true - n11
	n = true + false
	numerators = n * (n11 * n00 - n10 * n01) ** 2
	denominators = (n11 + n01) * (n11 + n10) * (n10 + n00) * (n01 + n00)
	print np.where(denominators == 0)
	return numerators / denominators
	
def _train(model, features, name, alpha):
	"""Train and save a naive Bayes classifier."""
	true_count = false_count = alpha * len(features)
	true_priors = np.empty(len(features))
	true_priors.fill(alpha)
	false_priors = np.empty(len(features))
	false_priors.fill(alpha)
	max_id = model.objects.latest('id').id
	test_ids = bitarray(max_id + 1)
	test_ids[:] = False
	
	# calculate prior and conditional probabilities
	for object in model.objects.filter(label__isnull=False):
		if random() >= 0.9:
			test_ids[object.id] = True
			continue
		if object.label:
			true_count += 1.0
		else:
			false_count += 1.0
		object_features = object.get_features()
		for j, feature in enumerate(features):
			if object.label:
				true_priors[j] += feature in object_features
			else:
				false_priors[j] += feature in object_features
	true_priors /= true_count
	false_priors /= false_count
	prior = true_count / (true_count + false_count)
	
	# create and save classifier
	try:
		classifier = models.Classifier.objects.get(name=name)
	except models.Classifier.DoesNotExist:
		classifier = models.Classifier(name=name)
	models.Feature.objects.filter(classifier=classifier).update(true_prior=None, false_prior=None)
	classifier.prior = prior
	classifier.save()
	for j, feature in enumerate(features):
		classifier_feature, created = models.Feature.objects.get_or_create(
			name=feature,
			classifier=classifier
		)
		classifier_feature.true_prior = true_priors[j]
		classifier_feature.false_prior = false_priors[j]
		classifier_feature.save()
	return test_ids
	
def _test(model, name, test_ids):
	"""Test effectiveness of classifier."""
	classifier = models.Classifier.objects.get(name=name)
	predictor = classifier.predictor()
	train_error = 0.0
	train_total = 0.0
	test_error = 0.0
	test_total = 0.0
	false_positives = []
	false_negatives = []
	for object in model.objects.filter(label__isnull=False):
		predicted = predictor.predict(object)
		if predicted and not object.label:
			false_positives.append(unicode(object))
		elif not predicted and object.label:
			false_negatives.append(unicode(object))
		if test_ids[object.id]:
			if predicted != object.label:
				test_error += 1
			test_total += 1
		else:
			if predicted != object.label:
				train_error += 1
			train_total += 1
	train_error /= train_total
	test_error /= test_total
	print "false_positives=%s\n" % ','.join(false_positives)
	print "false_negatives=%s\n" % ','.join(false_negatives)
	print "train_error=%.6f test_error=%.6f\n" % (train_error, test_error)
	return train_error, test_error
	
def _margins(model, name):
	"""Calculate margins for unlabeled data points."""
	classifier = models.Classifier.objects.get(name=name)
	predictor = classifier.predictor()
	for object in model.objects.filter(label__isnull=True):
		margin = predictor.margin(object)
		model.objects.filter(id=object.id).update(margin=margin)