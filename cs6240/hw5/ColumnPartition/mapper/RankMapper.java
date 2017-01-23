package pagerank.mapper;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

// A simple identity mapper for the ranks vector used in the dangling job.
public class RankMapper
extends Mapper<IntWritable, DoubleWritable, IntWritable, DoubleWritable> {
	public void map(IntWritable index, DoubleWritable rank, Context context)
	throws IOException, InterruptedException {
		context.write(index, rank);
	}
}