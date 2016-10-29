package cs6240.writable;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.Writable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;

//a writable tuple corresponding to a measurement type and value from a given
// year
public class Reading implements Writable {
	private Text type;
	private IntWritable year;
	private IntWritable value;
	
	public Reading() {
		type = new Text();
		year = new IntWritable();
		value = new IntWritable();
	}
	
	public String getType() { return type.toString(); }
	public int getYear() { return year.get(); }
	public int getValue() { return value.get(); }
	
	@Override
	public void write(DataOutput out) throws IOException {
		type.write(out);
		year.write(out);
		value.write(out);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		type.readFields(in);
		year.readFields(in);
		value.readFields(in);
	}
	
	public void set(String type, int year, int value) {
		this.type.set(type);
		this.year.set(year);
		this.value.set(value);
	}
}
