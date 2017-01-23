package pagerank.comparator;

import org.apache.hadoop.io.WritableComparator;
import org.apache.hadoop.io.WritableComparable;

import pagerank.writable.MatrixIndex;

// Grouping comparator for the iterate job. Groups keys by index.
public class IterateGroupComparator extends WritableComparator {
	protected IterateGroupComparator() {
		super(MatrixIndex.class, true);
	}
	
	@Override
	public int compare(WritableComparable x, WritableComparable y) {
		return compare((MatrixIndex) x, (MatrixIndex) y);
	}
	
	public int compare(MatrixIndex x, MatrixIndex y) {
		return x.getIndex() - y.getIndex();
	}
}