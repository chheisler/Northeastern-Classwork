from django.shortcuts import render
from overwatch import models
from django.shortcuts import render
from django.core.urlresolvers import reverse
from util import bbc_strip
from django.http import HttpResponse, HttpResponseBadRequest
import json

def label(request):
	id, factbook, tags, embassies = _get_region()		
	next_url = reverse(label_next);
	context = {
		'id': id,
		'factbook': factbook,
		'tags': tags,
		'embassies': embassies,
		'next_url': next_url
	}
	return render(request, 'label.html', context)
	
def label_next(request):
	try:
		id = int(request.POST['id'])
		label = request.POST['label']
		if label == 'true':
			label = True
		elif label == 'false':
			label = False
		else:
			raise Exception()
	except Exception:
		return HttpResponseBadRequest();
	models.Region.objects.filter(id=id).update(label=label)
	id, factbook, tags, embassies = _get_region()
	data = {'id': id, 'factbook': factbook, 'tags': tags, 'embassies': embassies}
	return HttpResponse(json.dumps(data), content_type='application/json') 
	
def _get_region():
	unlabeled = models.Region.objects.filter(label__isnull=True)
	try:
		margined = unlabeled.filter(margin__isnull=False)
		region = margined.order_by('margin')[0]
	except IndexError:
		try:
			region = unlabeled[0]
		except IndexError:
			region = None
	if region is None:
		id = factbook = tags = embassies = None
	else:
		id = region.id
		factbook = bbc_strip(region.factbook)
		tags = [tag.name for tag in region.tags.all()]
		embassies = [embassy.name for embassy in region.embassies.all()]	
	return id, factbook, tags, embassies