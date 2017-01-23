package pagerank.writable;

import org.apache.hadoop.io.Writable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.Collection;
import java.util.Arrays;

// A writable representing a list of vector indices.
public class Indices implements Writable {
	private Integer[] values;
	
	public Indices() {
		values = new Integer[0];
	}
	
	public void set(Collection<Integer> values) {
		if (values == null) this.values = new Integer[0];
		else {
			this.values = new Integer[values.size()];
			values.toArray(this.values);
		}
	}
	
	public Integer[] get() {
		return values;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeInt(values.length);
		for (Integer value : values) out.writeInt(value);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		Integer length = in.readInt();
		values = new Integer[length];
		for (Integer i = 0; i < length; i++) values[i] = in.readInt();
	}
	
	@Override
	public String toString() {
		return Arrays.toString(values);
	}
}

