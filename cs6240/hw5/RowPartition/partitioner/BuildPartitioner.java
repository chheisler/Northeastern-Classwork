package pagerank.partitioner;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Partitioner;

import pagerank.writable.PageIndex;

// The partitioner for the build job. Records are partitioned using the page
// name of the page index key.
public class BuildPartitioner extends Partitioner<PageIndex, IntWritable> {
	public int getPartition(PageIndex key, IntWritable value, int numPartitions) {
		return Math.abs(key.getPage().hashCode()) % numPartitions;
	}
}
