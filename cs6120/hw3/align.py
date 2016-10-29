import re
from collections import defaultdict

class AlignmentParser:
	TRANSLATE_PATTERN = re.compile(r'^(.+)\s+(.+)\s+(-\d+\.\d+)$')
	
	def __init__(self, filename, in_order, reversed, src_epsln, epsln_tgt):
		# generate dictionary
		file = open(filename, 'r')
		dictionary = defaultdict(dict)
		for line in file:
			match = re.match(self.TRANSLATE_PATTERN, line)
			if match:
				src_token = match.group(1)
				tgt_token = match.group(2)
				score = float(match.group(3))
				dictionary[src_token][tgt_token] = score
		self.dictionary = dictionary
		
		# set up production rule scores
		self.scores = {
			Production.IN_ORDER: in_order,
			Production.REVERSED: reversed,
			Production.SRC_EPSILON: src_epsln,
			Production.EPSILON_TGT: epsln_tgt
		}
		
	def align(self, source, target, swap=True):
		# tokenize the source and target sentences
		source = source.split()
		target = target.split()
	
		# build an empty table of probability scores
		parse = [
				[
					[
						[None for l in range(len(target) + 1)]
						for k in range(len(target))
					]
					for j in range(len(source) + 1)
				]
				for i in range(len(source))
			]

		# initialize entries in table
		for i in range(len(source)):
			for j in range(len(target)):
				src_token = source[i]
				tgt_token = target[j]
				
				# initialize dictionary entries
				if src_token in self.dictionary \
				and tgt_token in self.dictionary[src_token]:
					production = Production(
						rule=Production.TRANSLATION,
						score=self.dictionary[src_token][tgt_token],
						products=(src_token + '/' + tgt_token,)
					)
					parse[i][1][j][1] = production
					
				# initialize source to epsilon production
				production = Production(
					rule=Production.SRC_EPSILON,
					score=self.scores[Production.SRC_EPSILON],
					products=(src_token + '/EPSILON',)
				)
				parse[i][1][j][0] = production
				
				# initialize epsilon to target production
				production = Production(
					rule=Production.EPSILON_TGT,
					score=self.scores[Production.EPSILON_TGT],
					products = ('EPSILON/' + tgt_token,)
				)
				parse[i][0][j][1] = production
					
		# iteratively go through possible spanning matches
		for src_len in range(len(source) + 1):
			for src_idx in range(len(source)):
				for tgt_len in range(len(target) + 1):
					for tgt_idx in range(len(target)):
						span = parse[src_idx][src_len][tgt_idx][tgt_len]
						
						# partition span and look for matches
						for src_prt in range(src_len + 1):
							src_sub_idx = src_idx + src_prt
							src_sub_len = src_len - src_prt
							for tgt_prt in range(tgt_len + 1):
								tgt_sub_idx = tgt_idx + tgt_prt
								tgt_sub_len = tgt_len - tgt_prt
								if src_sub_idx >= len(source) or tgt_sub_idx >= len(target):
									continue
									
								# check for in order
								left = parse[src_idx][src_prt][tgt_idx][tgt_prt]
								right = parse[src_sub_idx][src_sub_len][tgt_sub_idx][tgt_sub_len]
								if left and right:
									span = self._bracket(span, left, right, False)
									parse[src_idx][src_len][tgt_idx][tgt_len] = span
									
								# check for reversed
								if swap:
									left = parse[src_idx][src_prt][tgt_sub_idx][tgt_sub_len]
									right = parse[src_sub_idx][src_sub_len][tgt_idx][tgt_prt]
									if left and right:
										span = self._bracket(span, left, right, True)
										parse[src_idx][src_len][tgt_idx][tgt_len] = span
										
		#return the best parse
		return parse[0][len(source)][0][len(target)]
		
	def _bracket(self, span, left, right, swap):
		"""Helper to build new bracket"""
		score = left.score + right.score
		if swap:
			rule = Production.REVERSED
			score += self.scores[Production.REVERSED]
		else:
			rule = Production.IN_ORDER
			score += self.scores[Production.IN_ORDER]
		if span is None or score > span.score:
			return Production(
				rule=rule,
				score=score,
				products=(left,right)
			)
		else:
			return span
			
class Production:
	"""Class representing a grammar rule production"""
	
	# production rules
	IN_ORDER = 0
	REVERSED = 1
	SRC_EPSILON = 2
	EPSILON_TGT = 3
	TRANSLATION = 4
	EPSILON = (SRC_EPSILON, EPSILON_TGT)
	
	def __init__(self, rule, score, products):
		self.rule = rule
		self.score = score
		self.products = products
		
	def display(self, indent=False, stdout=True):
		"""Print a production recursively with indentation"""
		stack = [(self, 0)]
		if not indent:
			output = []
		while len(stack) > 0:
			product, depth = stack.pop()
			if isinstance(product, str):
				if indent:
					output = product
				else:
					output.append(product)
			elif len(product.products) > 1:
				if product.rule == Production.IN_ORDER:
					if indent:
						output = '['
					else:
						output.append('[')
					stack.append((']', depth))
				else:
					if indent:
						output = '<'
					else:
						output.append('<')
					stack.append(('>', depth))
				for subproduct in reversed(product.products):
					stack.append((subproduct, depth + 1))
			else:
				if indent:
					output = product.products[0]
				else:
					output.append(product.products[0])
			if indent:
				print ('  ' * depth) + output
		if not indent:
			if stdout:
				print ' '.join(output)
			else:
				return ' '.join(output)
			