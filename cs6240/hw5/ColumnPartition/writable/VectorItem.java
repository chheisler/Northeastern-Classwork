package pagerank.writable;

import org.apache.hadoop.io.Writable;

import java.io.IOException;
import java.io.DataInput;
import java.io.DataOutput;

// A writable representing a value in a vector or matrix column or row.
public class VectorItem implements Writable {
	private int index;
	private double value;
	
	public VectorItem() {
		index = 0;
		value = 0;
	}
	
	public VectorItem(VectorItem other) {
		index = other.getIndex();
		value = other.getValue();
	}
	public void set(int index, double value) {
		this.index = index;
		this.value = value;
	}
	
	public void setIndex(int index) {
		this.index = index;
	}
	
	public void setValue(double value) {
		this.value = value;
	}
	
	public int getIndex() {
		return index;
	}
	
	public double getValue() {
		return value;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeInt(index);
		out.writeDouble(value);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		index = in.readInt();
		value = in.readDouble();
	}
	
	@Override
	public String toString() {
		return "(" + index + "," + value + ")";
	}
}
