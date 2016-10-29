package cs6240.writable;

import org.apache.hadoop.io.Writable;

import java.io.IOException;
import java.io.DataInput;
import java.io.DataOutput;
import java.util.ArrayList;
import java.util.ListIterator;

import cs6240.writable.Average;

// a wrible list of tuples corresponding to the average TMIN and TMAX values
// for a station for a given year
public class AverageList implements Writable {
	private ArrayList<Average> averages;
	
	public AverageList() {
		averages = new ArrayList<>();
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		for (Average average : averages) average.write(out);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		for (Average average : averages) average.readFields(in);
	}
	
	public void add(Average average) {
		averages.add(average);
	}
	
	@Override
	public String toString() {
		StringBuffer buffer = new StringBuffer();
		buffer.append("[");
		ListIterator<Average> iterator = averages.listIterator();
		while (iterator.hasNext()) {
			Average average = iterator.next();
			buffer.append(average.toString());
			if (iterator.hasNext()) buffer.append(",");
		}
		buffer.append("]");
		return buffer.toString();
	}
}