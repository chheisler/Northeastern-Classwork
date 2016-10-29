package cs6240.writable;

import org.apache.hadoop.io.WritableComparable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;

// A comparable writable representing a name, rank tuple for a single page.
// Sorts by rank first, then page name.
public class NameAndRank implements WritableComparable {
	private String name;
	private double rank;
	
	public NameAndRank() {}
	
	public NameAndRank(String name, double rank) {
		this.name = name;
		this.rank = rank;
	}
	
	public NameAndRank(NameAndRank other) {
		this.name = other.getName();
		this.rank = other.getRank();
	}
	
	public String getName() {
		return name;
	}
	
	public double getRank() { 
		return rank;
	}
	
	public void set(String name, double rank) {
		this.name = name;
		this.rank = rank;
	}

	public void setRank(double rank) {
		this.rank = rank;
	}
	
	@Override
	public int compareTo(Object other) {
		return compareTo((NameAndRank) other);
	}
	
	// sort by rank then name
	public int compareTo(NameAndRank other) {
		int diff = new Double(rank).compareTo(other.getRank());
		if (diff == 0) return name.compareTo(other.getName());
		else return diff;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeUTF(name);
		out.writeDouble(rank);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		name = in.readUTF();
		rank = in.readDouble();
	}
	
	@Override
	public String toString() {
		return name + "\t" + rank;
	}
}
