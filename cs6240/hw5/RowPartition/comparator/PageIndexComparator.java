package pagerank.comparator;

import org.apache.hadoop.io.WritableComparator;
import org.apache.hadoop.io.WritableComparable;

import pagerank.writable.PageIndex;

// A comparator which compares page indices by either their pagename or their
// numerical index depending on which one is set. Used to group data for which
// only the page name or index is known with the set of page indices.
public class PageIndexComparator extends WritableComparator {
	protected PageIndexComparator() {
		super(PageIndex.class, true);
	}
	
	@Override
	public int compare(WritableComparable x, WritableComparable y) {
		return compare((PageIndex) x, (PageIndex) y);
	}
	
	public int compare(PageIndex x, PageIndex y) {
		String page1 = x.getPage();
		String page2 = y.getPage();
		if (page1 != null && page2 != null) return page1.compareTo(page2);
		long index1 = x.getIndex();
		long index2 = y.getIndex();
		if (index1 != PageIndex.NULL_INDEX && index2 != PageIndex.NULL_INDEX)
			return new Long(index1).compareTo(index2);
		return x.hashCode() - y.hashCode();
	}
}