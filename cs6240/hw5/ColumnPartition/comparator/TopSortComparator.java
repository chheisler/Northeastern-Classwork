package pagerank.comparator;

import org.apache.hadoop.io.WritableComparator;
import org.apache.hadoop.io.WritableComparable;

import pagerank.writable.PageAndRank;

// Comparator used by top job. Sorts page name and rank tuples in descending
// order by rank, then in ascending order by name.
public class TopSortComparator extends WritableComparator {
	protected TopSortComparator() {
		super(PageAndRank.class, true);
	}
	
	@Override
	public int compare(WritableComparable x, WritableComparable y) {
		return compare((PageAndRank) x, (PageAndRank) y);
	}
	
	public int compare(PageAndRank x, PageAndRank y) {
		int diff = new Double(y.getRank()).compareTo(x.getRank());
		if (diff != 0) return diff;
		return x.getPage().compareTo(y.getPage());
	}
}