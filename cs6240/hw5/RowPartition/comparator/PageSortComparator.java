package pagerank.comparator;

import org.apache.hadoop.io.WritableComparator;
import org.apache.hadoop.io.WritableComparable;

import pagerank.writable.PageIndex;

// A comparator which sorts page indices by their page names. Used when
// joining values for which only the page name is known to the set of page
// indices.
public class PageSortComparator extends WritableComparator {
	protected PageSortComparator() {
		super(PageIndex.class, true);
	}
	
	@Override
	public int compare(WritableComparable x, WritableComparable y) {
		return compare((PageIndex) x, (PageIndex) y);
	}
	
	public int compare(PageIndex x, PageIndex y) {
		String page1 = x.getPage();
		String page2 = y.getPage();
		int diff = page1.compareTo(page2);
		if (diff != 0) return diff;
		if (x.getIndex() == PageIndex.NULL_INDEX) return 1;
		if (y.getIndex() == PageIndex.NULL_INDEX) return -1;
		return diff;
	}
}