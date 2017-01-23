package pagerank.mapper;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.VectorItem;

// The rank mapper for the iterate job. For each rank it writes a dummy value
// so that pages which have no incoming links can be recovered and updated
// with the rank incoming from dangling nodes.
public class IterateRankMapper
extends Mapper<IntWritable, DoubleWritable, IntWritable, VectorItem> {
	private VectorItem dummy = new VectorItem(0, 0.0);
	
	@Override
	public void map(IntWritable index, DoubleWritable rank, Context context)
	throws IOException, InterruptedException {
		context.write(index, dummy);
	}
}