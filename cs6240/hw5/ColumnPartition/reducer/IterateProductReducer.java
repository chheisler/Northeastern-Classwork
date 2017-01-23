package pagerank.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;
import java.util.Iterator;

import pagerank.writable.MatrixIndex;
import pagerank.writable.VectorItem;

// Reducer for the iterate product job. Calculates every non-zero value in the
// cross product of a column from the adjacency matrix and a row from the rank
// matrix. Columns and rows are grouped by index, and sorted so tha the unique
// rank row index for each reduce call is sorted first. A zero dummy value is
// also written for each incoming row to account for rows with no in-links.
public class IterateProductReducer
extends Reducer<MatrixIndex, VectorItem, IntWritable, DoubleWritable> {
	private IntWritable indexOut = new IntWritable();
	private DoubleWritable rankOut = new DoubleWritable();
	private DoubleWritable zero = new DoubleWritable(0);
	
	@Override
	public void reduce(MatrixIndex indexIn, Iterable<VectorItem> items, Context context)
	throws IOException, InterruptedException {
		indexOut.set(indexIn.getIndex());
		context.write(indexOut, zero);
		Iterator<VectorItem> iter = items.iterator();
		double rankIn = iter.next().getValue();
		while (iter.hasNext()) {
			VectorItem item = iter.next();
			indexOut.set(item.getIndex());
			rankOut.set(rankIn * item.getValue());
			context.write(indexOut, rankOut);
		}
	}
}