package cs6240.writable;

import org.apache.hadoop.io.Writable;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.FloatWritable;

import java.io.IOException;
import java.io.DataInput;
import java.io.DataOutput;

// a writable tuple corresponding to the average TMIN and TMAX for a station
// for a year
public class Average implements Writable {
	private IntWritable year;
	private FloatWritable minTemp;
	private FloatWritable maxTemp;
	
	public Average() {
		year = new IntWritable();
		minTemp = new FloatWritable();
		maxTemp = new FloatWritable();
	}

	@Override
	public void write(DataOutput out) throws IOException {
		year.write(out);
		minTemp.write(out);
		maxTemp.write(out);
	}

	@Override
	public void readFields(DataInput in) throws IOException {
		year.readFields(in);
		minTemp.readFields(in);
		maxTemp.readFields(in);
	}

	public void set(int year, float minTemp, float maxTemp) {
		this.year.set(year);
		this.minTemp.set(minTemp);
		this.maxTemp.set(maxTemp);
	}

	@Override
	public String toString() {
		return "(" + year.get() + "," + minTemp.toString() + "," + maxTemp.toString() + ")";
	}
}
