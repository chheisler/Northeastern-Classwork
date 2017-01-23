package pagerank.writable;

import org.apache.hadoop.io.WritableComparable;

import java.io.DataOutput;
import java.io.DataInput;
import java.io.IOException;

// A writable representing a page name and rank tuple. Sorted by rank first
// and then page name.
public class PageAndRank implements WritableComparable {
	private String page;
	private double rank;
	
	public PageAndRank() {
		this.page = "";
		this.rank = 0;
	}
	
	public PageAndRank(String page, double rank) {
		this.page = page;
		this.rank = rank;
	}
	
	public String getPage() {
		return page;
	}
	
	public double getRank() {
		return rank;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeUTF(page);
		out.writeDouble(rank);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		page = in.readUTF();
		rank = in.readDouble();
	}
	
	@Override
	public int compareTo(Object other) {
		return compareTo((PageAndRank) other);
	}
	
	public int compareTo(PageAndRank other) {
		int diff = new Double(rank).compareTo(other.getRank());
		if (diff != 0) return diff;
		return page.compareTo(other.getPage());
	}
	
	@Override
	public String toString() {
		return page + " (" + rank + ")";
	}
}
