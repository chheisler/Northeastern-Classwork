package pagerank.mapper;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

// The mapper for the dangling job. Each input is just the numberical
// index of a dangling page. Each index is is output as a key with
// one over the number of pages as the value.
public class DanglingMapper
extends Mapper<IntWritable, NullWritable, IntWritable, DoubleWritable> {
	private DoubleWritable value = new DoubleWritable();
	
	public void setup(Context context) {
		Configuration config = context.getConfiguration();
		int numPages = config.getInt("NUM_PAGES", 0);
		value.set(1.0 / numPages);
	}
	
	public void map(IntWritable index, NullWritable none, Context context)
	throws IOException, InterruptedException {
		context.write(index, value);
	}
}