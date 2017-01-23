package pagerank.partitioner;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Partitioner;

import pagerank.writable.PageIndex;

// The partitioner for the link job. Records are partitioned using the page
// name of the page index key.
public class LinkPartitioner extends Partitioner<PageIndex, Text> {
	public int getPartition(PageIndex key, Text value, int numPartitions) {
		return Math.abs(key.getPage().hashCode()) % numPartitions;
	}
}