package cs6240.comparator;

import org.apache.hadoop.io.WritableComparator;
import org.apache.hadoop.io.WritableComparable;

import cs6240.writable.StationYear;

// a comparator which groups stations by name alone
public class GroupComparator extends WritableComparator {
	protected GroupComparator() {
		super(StationYear.class, true);
	}
	
	@Override
	public int compare(WritableComparable x, WritableComparable y) {
		return compare((StationYear) x, (StationYear) y);
	}
	
	public int compare(StationYear x, StationYear y) {
		return x.getStation().compareTo(y.getStation());
	}
}