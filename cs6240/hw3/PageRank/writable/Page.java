package cs6240.writable;

import org.apache.hadoop.io.Writable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.List;

// A writable representing a webpage. Contains the page's current rank and a
// list of page names which the page links to. If the list of linked pages is
// null, it instead represents the rank contribution of a neighboring page.
public class Page implements Writable {
	private double rank;
	private String[] linkNames;
	
	public Page() {}
	
	public Page(double rank, String[] linkNames) {
		this.rank = rank;
		this.linkNames = linkNames;
	}
	
	public void set(double rank, String[] linkNames) {
		this.rank = rank;
		this.linkNames = linkNames;
	}
	
	public void setRank(double rank) {
		this.rank = rank;
	}
	
	public void setLinkNames(String[] linkNames) {
		this.linkNames = linkNames;
	}
	
	public double getRank() {
		return rank;
	}
	
	public String[] getLinkNames() {
		return linkNames;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeDouble(rank);
		if (linkNames != null) {
			out.writeInt(linkNames.length);
			for (String linkName : linkNames) out.writeUTF(linkName);
		}
		else out.writeInt(-1);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		rank = in.readDouble();
		int length = in.readInt();
		if (length == -1) linkNames = null;
		else {
			linkNames = new String[length];
			for (int i = 0; i < length; i++) linkNames[i] = in.readUTF();
		}
	}
	
	public String toString() {
		if (linkNames == null) return new Double(rank).toString();
		else return rank + ":[" + String.join(",", linkNames) + "]";
	}
}
