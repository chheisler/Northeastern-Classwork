import align
import re
from sys import argv
	
def main():
	# check for swap
	if len(argv) > 1:
		swap = bool(int(argv[1]))
	else:
		swap = True
		
	# create an aligner engine
	aligner = align.AlignmentParser(
		filename="itg.dict",
		in_order=-1,
		reversed=-2,
		src_epsln=-20,
		epsln_tgt=-21
	)
	
	# open the files we need
	en_file = open('test.en', 'r')
	de_file = open('test.de', 'r')
	out_file = open('test.out', 'w')
	
	# counters for statistics
	aligns = 0
	translates = 0
	src_epsilons = 0
	epsilon_tgts = 0
	in_orders = 0
	swaps = 0
	
	# patterns for checking terminal productions
	translate_p = re.compile(r'(?<!EPSILON)/(?!EPSILON)')
	src_epsilon_p = re.compile(r'(?<!EPSILON)/(?=EPSILON)')
	epsilon_tgt_p = re.compile(r'(?<=EPSILON)/(?!EPSILON)')
	in_order_p = re.compile('\[')
	swap_p = re.compile('\<(?!num\>)')
	
	# run an alignment for each sentence pair
	while True:
		en_line = en_file.readline()
		de_line = de_file.readline()
		if en_line == '' or de_line == '':
			break
		alignment = aligner.align(en_line, de_line, swap)
		output = alignment.display(stdout=False)
		aligns += 1
		translates += len(re.findall(translate_p, output))
		src_epsilons += len(re.findall(src_epsilon_p, output))
		epsilon_tgts += len(re.findall(epsilon_tgt_p, output))
		in_orders += len(re.findall(in_order_p, output))
		swaps += len(re.findall(swap_p, output))
		out_file.write(alignment.display(stdout=False) + "\n")
		
	# close our files
	en_file.close()
	de_file.close()
	out_file.close()
	
	# print out statistics
	print "%d alignments parsed" % aligns
	print "%d pairs of source and target words aligned to each other" % translates
	print "%d source words aligned to epsilon" % src_epsilons
	print "%d target words aligned to epsilon" % epsilon_tgts
	print "%d in-order binary productions" % in_orders
	print "%d reversed binary productions" % swaps
	
if __name__ == '__main__':
	main()