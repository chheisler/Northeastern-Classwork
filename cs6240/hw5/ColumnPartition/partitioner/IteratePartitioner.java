package pagerank.partitioner;

import org.apache.hadoop.mapreduce.Partitioner;

import pagerank.writable.VectorItem;
import pagerank.writable.MatrixIndex;

// Partitioner for the iterate job. Partitions items by their index.
public class IteratePartitioner extends Partitioner<MatrixIndex, VectorItem> {
	public int getPartition(MatrixIndex key, VectorItem value, int numPartitions) {
		return key.getIndex() % numPartitions;
	}
}
