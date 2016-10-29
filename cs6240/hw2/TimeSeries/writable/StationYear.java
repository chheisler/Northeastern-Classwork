package cs6240.writable;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.WritableComparable;

import java.io.DataOutput;
import java.io.DataInput;
import java.io.IOException;

// a writable tuple corresponding to the station and year of a record
public class StationYear implements WritableComparable {
	private Text station;
	private IntWritable year;

	public StationYear() {
		station = new Text();
		year = new IntWritable();
	}
	
	public String getStation() { return station.toString(); }
	public int getYear() { return year.get(); }
	
	@Override
	public void write(DataOutput out) throws IOException {
		station.write(out);
		year.write(out);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		station.readFields(in);
		year.readFields(in);
	}
	
	@Override
	public int compareTo(Object other) {
		return compareTo((StationYear) other);
	}
	
	// sort by station then year
	public int compareTo(StationYear other) {
		int diff = this.getStation().compareTo(other.getStation());
		if (diff == 0) return this.getYear() - other.getYear();
		else return diff;			
	}
	
	public void set(String station, int year) {
		this.station.set(station);
		this.year.set(year);
	}
}
