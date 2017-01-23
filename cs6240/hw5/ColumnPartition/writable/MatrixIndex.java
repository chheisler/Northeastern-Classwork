package pagerank.writable;

import org.apache.hadoop.io.WritableComparable;

import java.io.DataOutput;
import java.io.DataInput;
import java.io.IOException;

// Writable representing either a row or column index in a matrix. Row indices
// are sorted before equal column indices.
public class MatrixIndex implements WritableComparable {
	private int index;
	private boolean isRow;
	
	public MatrixIndex() {
		index = 0;
		isRow = false;
	}
	
	public MatrixIndex(int index, boolean isRow) {
		this.index = index;
		this.isRow = isRow;
	}
	
	public void setIndex(int index) {
		this.index = index;
	}
	
	public int getIndex() {
		return index;
	}
	
	public boolean getIsRow() {
		return isRow;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeInt(index);
		out.writeBoolean(isRow);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		index = in.readInt();
		isRow = in.readBoolean();
	}
	
	@Override
	public int compareTo(Object other) {
		return compareTo((MatrixIndex) other);
	}
	
	public int compareTo(MatrixIndex other) {
		int diff = index - other.getIndex();
		if (diff != 0) return diff;
		boolean otherIsRow = other.getIsRow();
		if (isRow == otherIsRow) return 0;
		else {
			if (isRow) return -1;
			else return 1;
		}
	}
	
	@Override
	public String toString() {
		return "(" + index + "," + isRow + ")";
	}
}