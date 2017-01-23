package pagerank.mapper;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.MatrixIndex;
import pagerank.writable.VectorItem;

// Rank mapper for the iterate job. Each rank is mapped with its row index
// as the key and its value. The key is also used to mark that this is a row
// and should be sorted before column indices from the adjacency matrix.
public class IterateRankMapper
extends Mapper<IntWritable, DoubleWritable, MatrixIndex, VectorItem> {
	private MatrixIndex indexOut = new MatrixIndex(0, true);
	private VectorItem item = new VectorItem();
	
	@Override
	public void map(IntWritable indexIn, DoubleWritable rank, Context context)
	throws IOException, InterruptedException {
		indexOut.setIndex(indexIn.get());
		item.setValue(rank.get());
		context.write(indexOut, item);
	}
}