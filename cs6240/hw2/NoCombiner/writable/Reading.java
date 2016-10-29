package cs6240.writable;

import org.apache.hadoop.io.Writable;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Text;

import java.io.DataOutput;
import java.io.DataInput;
import java.io.IOException;

// a writable tuple corresponding to a measurement type and value
public class Reading implements Writable {
	private Text type = new Text();
	private IntWritable value = new IntWritable();

	public String getType() { return type.toString(); }
	public int getValue() { return value.get(); }

	@Override
	public void write(DataOutput out) throws IOException {
		type.write(out);
		value.write(out);
	}

	@Override
	public void readFields(DataInput in) throws IOException {
		type.readFields(in);
		value.readFields(in);
	}

	public void set(String type, int value) {
		this.type.set(type);
		this.value.set(value);
	}
}

