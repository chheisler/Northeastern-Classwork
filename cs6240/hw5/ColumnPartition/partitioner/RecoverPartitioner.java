package pagerank.partitioner;

import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Partitioner;

import pagerank.writable.PageIndex;

// The partitioner for the recover job. Records are partitioned using the
// numerical index of the page index key.
public class RecoverPartitioner extends Partitioner<PageIndex, DoubleWritable> {
	public int getPartition(PageIndex key, DoubleWritable value, int numPartitions) {
		return key.getIndex() % numPartitions;
	}
}