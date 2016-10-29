package cs6240.partitioner;

import org.apache.hadoop.mapreduce.Partitioner;

import cs6240.writable.StationYear;
import cs6240.writable.Reading;

// a partitioner which assigns a partition based on the hash of the name
public class StationPartitioner
extends Partitioner<StationYear, Reading> {
	@Override
	public int getPartition(StationYear key, Reading value, int numPartitions) {
		return Math.abs(key.getStation().hashCode()) % numPartitions;
	}
}