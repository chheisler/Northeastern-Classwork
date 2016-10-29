package cs6240.writable;

import org.apache.hadoop.io.Writable;
import org.apache.hadoop.io.FloatWritable;

import java.io.IOException;
import java.io.DataInput;
import java.io.DataOutput;

// a writable tuple corresponding to the average TMIN and TMAX for a station
public class Average implements Writable {
	private FloatWritable minTemp = new FloatWritable();
	private FloatWritable maxTemp = new FloatWritable();

	@Override
	public void write(DataOutput out) throws IOException {
		minTemp.write(out);
		maxTemp.write(out);
	}

	@Override
	public void readFields(DataInput in) throws IOException {
		minTemp.readFields(in);
		maxTemp.readFields(in);
	}

	public void set(float minTemp, float maxTemp) {
		this.minTemp.set(minTemp);
		this.maxTemp.set(maxTemp);
	}

	@Override
	public String toString() {
		return "(" + minTemp.toString() + "," + maxTemp.toString() + ")";
	}
}
