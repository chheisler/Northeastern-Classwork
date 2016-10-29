from xml.etree import ElementTree as ET
from django.utils.timezone import utc
import re, gzip
from overwatch.util import id_str
from overwatch.models import Region, Tag, Embassy
from collections import defaultdict
from httplib import HTTPConnection, OK
from urllib import urlencode, urlretrieve
from django.core.management.base import BaseCommand, CommandError
from time import sleep
from datetime import datetime
from django.db.utils import IntegrityError

DUMP_URL = 'http://www.nationstates.net/pages/regions.xml.gz'
DUMP_PATH = '/pages/regions.xml.gz'
DUMP_FILENAME = 'overwatch/data/regions.xml.gz'
LAST_MOD_PATTERN = re.compile(r'^Last-Modified: (\w{3}, \d{2} \w{3} \d{4} \d{2}:\d{2}:\d{2} GMT)')

class Command(BaseCommand):
	def handle(self, *args, **options):
		last_modified = _dump()
		tags = _tags()
		_parse(last_modified, tags)

def _dump():
	"""Retrieve the current daily dump."""
	print "Retrieving regions dump..."
	response = _request(DUMP_PATH, method='HEAD')
	last_modified = response.msg['Last-Modified']
	last_modified = datetime.strptime(last_modified, '%a, %d %b %Y %H:%M:%S %Z')
	last_modified = last_modified.replace(tzinfo=utc).date()
	sleep(7)
	urlretrieve(DUMP_URL, DUMP_FILENAME)
	return last_modified
	
def _tags():
	"""Get tags for all regions."""
	print "Retrieving region tags..."
	response = _request('/page=list_regions/')
	pattern = r'<a href="/page=tag_search/type=region/tag=(\w+)">(?:[\w ]+)</a>'
	content = response.read()
	tags = re.findall(pattern, content)
	region_tags = defaultdict(list)
	for tag in tags:
		xml = _api({'q': 'regionsbytag', 'tags': tag})
		try:
			region_names = id_str(xml.find('REGIONS').text).split(',')
		except TypeError:
			continue
		for region_name in region_names:
			region_tags[id_str(region_name)].append(id_str(tag))
	return region_tags
			
def _parse(last_modified, tags):
	"""Parse a daily dump and add new data entries for labeling."""
	# initialize XML iterator
	print "Initializing XML iterator..."
	xml = gzip.open(DUMP_FILENAME, 'r')
	context = ET.iterparse(xml, events=('start','end'))
	context = iter(context)
	event, root = context.next()
	
	# iterate through XML and process elements
	print "Iterating through XML..."
	elem_count = 0
	for event, elem in context:
		if event == 'end' and elem.tag == 'REGION':
			_elem(elem, last_modified, tags)
			elem_count += 1
			if elem_count % 100 == 0:
				print "%d elements parsed..." % elem_count
			root.clear()
			
def _elem(elem, last_modified, tags):
	"""Parse an element from the daily dump."""
	name = id_str(elem.find('NAME').text)
	factbook = elem.find('FACTBOOK').text or ''
	tag_names = tags[name]
	embassy_names = [id_str(embassy.text) for embassy in elem.find('EMBASSIES')]
	if 'password' in tag_names or 'founderless' not in tag_names:
		return
	try:
		region = Region.objects.create(
			name=name,
			date=last_modified,
			factbook=factbook
		)
	except IntegrityError:
		return
	for tag_name in tag_names:
		tag, created = Tag.objects.get_or_create(name=tag_name)
		region.tags.add(tag)
	for embassy_name in embassy_names:
		embassy, created = Embassy.objects.get_or_create(name=embassy_name)
		region.embassies.add(embassy)
	region.save()
	
def _request(path, method='GET'):
	sleep(7)
	headers = {'User-Agent': 'Region Dump Parser (Gullivania)'}
	conn = HTTPConnection('www.nationstates.net')
	conn.request(method, path, headers=headers)
	response = conn.getresponse()
	if response.status != OK:
		raise CommandError("Unable to contact NationStates: %d" % response.status)
	return response
	
def _api(params):
	sleep(0.7)
	params = urlencode(params)
	headers = {'User-Agent': 'Region Dump Parser (Gullivania)'}
	conn = HTTPConnection('www.nationstates.net')
	conn.request('GET', '/cgi-bin/api.cgi?' + params, headers=headers)
	response = conn.getresponse()
	if response.status != OK:
		raise CommandError("Unable to contact NationStates: %d" % response.status)
	content = response.read()
	xml = ET.fromstring(content)
	conn.close()
	return xml