from django.db import models
from util import find_words
import numpy as np

class Region(models.Model):
	name = models.CharField(max_length=40)
	date = models.DateField()
	factbook = models.TextField()
	tags = models.ManyToManyField('Tag')
	embassies = models.ManyToManyField('Embassy')
	label = models.NullBooleanField(db_index=True)
	margin = models.FloatField(null=True,db_index=True)
	
	class Meta:
		unique_together = (('name', 'date'),)

	def get_features(self):
		features = find_words(self.factbook)
		features |= set(['#' + tag.name for tag in self.tags.all()])
		features |= set(['@' + embassy.name for embassy in self.embassies.all()])
		return features
		
	def get_datum(self, features):
		datum = np.zeros(len(features), dtype='int8')
		own_features = self.get_features()
		for j, feature in enumerate(features):
			if isinstance(feature, (str, unicode)):
				datum[j] = feature in own_features
			elif isinstance(feature, Feature):
				datum[j] = feature.name in own_features
			else:
				raise TypeError()
		return datum
		
	def __unicode__(self):
		return self.name
	
class Tag(models.Model):
	name = models.CharField(max_length=255, unique=True)
	
class Embassy(models.Model):
	name = models.CharField(max_length=40,unique=True)

class Classifier(models.Model):
	name = models.CharField(max_length=255, unique=True)
	prior = models.FloatField()
	
	class Predictor(object):
		def __init__(self, classifier):
			self.prior = classifier.prior 
			self.features = list(
				classifier.features.filter(
					true_prior__isnull=False,
					false_prior__isnull=False
				).order_by('id')
			)
			self.true_priors = np.array([feature.true_prior for feature in self.features])
			self.false_priors = np.array([feature.false_prior for feature in self.features])
			
		def predict(self, object):
			datum = object.get_datum(self.features)
			true_prob, false_prob = self._probs(datum)
			return true_prob > false_prob
			
		def margin(self, object):
			datum = object.get_datum(self.features)
			true_prob, false_prob = self._probs(datum)
			norm = true_prob + false_prob
			true_prob /= norm
			false_prob /= norm
			return abs(true_prob - false_prob)
			
		def _probs(self, datum):
			true_prob = self._prob(datum, self.prior, self.true_priors)
			false_prob = self._prob(datum, 1 - self.prior, self.false_priors)
			return true_prob, false_prob
			
		def _prob(self, datum, prior, priors):
			return prior * np.prod((1 - priors) + (2 * priors - 1) * datum)
			
	def predictor(self):
		return self.Predictor(self)
		
class Feature(models.Model):
	name = models.CharField(max_length=255)
	true_prior = models.FloatField(null=True)
	false_prior = models.FloatField(null=True)
	classifier = models.ForeignKey('Classifier', related_name='features')
	
	class Meta:
		unique_together = (('name', 'classifier'),)