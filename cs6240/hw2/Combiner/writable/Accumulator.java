package cs6240.writable;

import org.apache.hadoop.io.Writable;
import org.apache.hadoop.io.IntWritable;

import java.io.IOException;
import java.io.DataInput;
import java.io.DataOutput;

// a writable data structure which accumulates the total and counts for TMIN
// and TMAX measurements from a station
public class Accumulator implements Writable {
	private int minTempTotal = 0;
	private int minTempCount = 0;
	private int maxTempTotal = 0;
	private int maxTempCount = 0;
	
	public int getMinTempTotal() { return minTempTotal; }
	public int getMinTempCount() { return minTempCount; }
	public int getMaxTempTotal() { return maxTempTotal; }
	public int getMaxTempCount() { return maxTempCount; }

	public void addMinTemp(int value) {
		minTempTotal += value;
		minTempCount++;
	}

	public void addMaxTemp(int value) {
		maxTempTotal += value;
		maxTempCount++;
	}

	public void add(Accumulator other) {
		minTempTotal += other.getMinTempTotal();
		minTempCount += other.getMinTempCount();
		maxTempTotal += other.getMaxTempTotal();
		maxTempCount += other.getMaxTempCount();
	}
	
	public float averageMinTemp() {
		return (float) minTempTotal / minTempCount;
	}
	
	public float averageMaxTemp() {
		return (float) maxTempTotal / maxTempCount;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeInt(minTempTotal);
		out.writeInt(minTempCount);
		out.writeInt(maxTempTotal);
		out.writeInt(maxTempCount);

	}

	@Override
	public void readFields(DataInput in) throws IOException {
		minTempTotal = in.readInt();
		minTempCount = in.readInt();
		maxTempTotal = in.readInt();
		maxTempCount = in.readInt();
	}

	public void set(Accumulator other) {
		minTempTotal = other.getMinTempTotal();
		minTempCount = other.getMinTempCount();
		maxTempTotal = other.getMaxTempTotal();
		maxTempCount = other.getMaxTempCount();
	}
}
