package pagerank.comparator;

import org.apache.hadoop.io.WritableComparator;
import org.apache.hadoop.io.WritableComparable;

import pagerank.writable.PageIndex;

// A comparator which sorts page indices by their indices. Used when joining
// values for which only the index is known to the set of page indices.
public class IndexSortComparator extends WritableComparator {
	protected IndexSortComparator() {
		super(PageIndex.class, true);
	}
	
	@Override
	public int compare(WritableComparable x, WritableComparable y) {
		return compare((PageIndex) x, (PageIndex) y);
	}
	
	public int compare(PageIndex x, PageIndex y) {
		int diff = x.getIndex() - y.getIndex();
		if (diff != 0) return diff;
		if (x.getPage() == null) return 1;
		if (y.getPage() == null) return -1;
		return diff;
	}
}