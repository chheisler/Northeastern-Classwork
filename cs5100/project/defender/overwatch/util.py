import codecs, re
from string import ascii_uppercase, ascii_lowercase, maketrans
from HTMLParser import HTMLParser
import numpy as np

def id_str(name):
	i, i2 = codecs.getencoder('ascii')(name)
	return i.translate(id_str.trans)
id_str.trans = maketrans(ascii_uppercase+" ",ascii_lowercase+"_")

def bbc_strip(raw):
	# check if input is none
	if raw is None:
		return ''
	parser = HTMLParser()
	text = parser.unescape(parser.unescape(raw))
		
	# create pattern for matching tokens
	open = r'\[(?!/)(?P<open_tag>[^=\]]+)(?:=(?P<attrib>[^\]]+))?\]'
	close = r'\[/(?P<close_tag>[^\]]+)\]'
	word = r'[^\[]+'
	pattern = r'(?P<open>%s)|(?P<close>%s)|(?P<word>%s)' % (open, close, word)
	
	# strip code from text
	tokens = []
	maybe_token = None
	maybe_index = 0
	for token in re.finditer(pattern, text, re.IGNORECASE | re.UNICODE):
		if token.group('open'):
			if maybe_token is not None:
				tokens.insert(maybe_index, maybe_token)
				maybe_token = None
			tag = token.group('open_tag').lower()
			if tag in ('nation', 'region') and token.group('attrib'):
				maybe_token = token.group('attrib')
				maybe_index = len(tokens)
		elif token.group('close'):
			tag = token.group('close_tag').lower()
			if tag in ('nation', 'region'):
				maybe_token = None
			elif maybe_token is not None:
				tokens.insert(maybe_index, maybe_token)
				maybe_token = None
		else:
			tokens.append(token.group(0))
	if maybe_token is not None:
		tokens.insert(maybe_index, maybe_token)
	return ''.join(tokens)

def find_words(factbook):
	# remove bbc markup
	text = bbc_strip(factbook)
	
	# create pattern for finding words
	pattern = r"(?:[^\W_]" \
		r"|(?<=[^\W_])[-_](?=[^\W_])" \
		r"|(?<=\w)'(?=\w)(?!(?:d|ll|m|re|s|ve)[^\w]))+"
		
	# find the words
	words = re.findall(pattern, text, re.IGNORECASE | re.UNICODE)
	return set([word.lower() for word in words])
	
def make_data(model, features):
	n = model.objects.filter(label__isnull=False).count()
	d = len(features)
	data = np.zeros((n,d), dtype='int8')
	labels = np.zeros(n, dtype='int8')
	for i, object in enumerate(model.objects.filter(label__isnull=False)):
		data[i] = object.get_datum(features)
		labels[i] = label_as_int(object.label)
	return data, labels
	
def label_as_bool(label):
	if isinstance(label, bool):
		return label
	elif isinstance(label, int):
		if label == 1:
			return True
		elif label == -1:
			return False
		else:
			raise ValueError()
	else:
		raise TypeError()
		
def label_as_int(label):
	if isinstance(label, bool):
		return 1 if label else -1
	elif isinstance(label, int):
		return label
	else:
		raise TypeError()