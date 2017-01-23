package pagerank.writable;

import org.apache.hadoop.io.WritableComparable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;

// A writable representing the pair of a unique page name and a unique
// numerical index for the page. Used as a key when joining data which
// has only the page name or index with the complete list of page indices.
// For each record in the list of page indices a unique PageIndex with both
// page and index set is written and sorted first by the reducer, so that the
// name or index for the joined records can be retrieved and applied
// immediately.
public class PageIndex implements WritableComparable {
	public static final int NULL_INDEX = -1;
	private String page = null;
	private int index = NULL_INDEX;
	
	public void set(String page, int index) {
		this.page = page;
		this.index = index;
	}
	
	public void setIndex(int index) {
		this.index = index;
	}
	
	public void setPage(String page) {
		this.page = page;
	}
	
	public String getPage() {
		return page;
	}
	
	public int getIndex() {
		return index;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		if (page == null) out.writeUTF("");
		else out.writeUTF(page);
		out.writeInt(index);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		page = in.readUTF();
		if (page.equals("")) page = null;
		index = in.readInt();
	}
	
	@Override
	public int compareTo(Object other) {
		return compareTo((PageIndex) other);
	}
	
	public int compareTo(PageIndex other) {
		return this.hashCode() - other.hashCode();
	}
	
	@Override
	public String toString() {
		return "(" + page + "," + index + ")";
	}
}
