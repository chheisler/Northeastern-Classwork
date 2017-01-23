package pagerank.mapper;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.PageIndex;

// The mapper for ranks in the recover job. Each input record is the numerical
// index of a page and its current rank. For each entry, a page index with
// just the index set to the index of the entry is written as a key, and the
// rank of the entry is written as a value.
public class RecoverRankMapper
extends Mapper<IntWritable, DoubleWritable, PageIndex, DoubleWritable> {
	private PageIndex pageIndex = new PageIndex();
	
	@Override
	public void map(IntWritable index, DoubleWritable rank, Context context)
	throws IOException, InterruptedException {
		pageIndex.setIndex(index.get());
		context.write(pageIndex, rank);
	}
}