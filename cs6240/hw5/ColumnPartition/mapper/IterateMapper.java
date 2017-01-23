package pagerank.mapper;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.Indices;
import pagerank.writable.VectorItem;
import pagerank.writable.MatrixIndex;

// Mapper for the iterate job. For each entry in the adjacency matrix it
// writes the entry's column as a key its row and value as the value. The
// key is also marked to indicate that this is a column index which should be
// sorted after a row index in the reducer.
public class IterateMapper
extends Mapper<IntWritable, Indices, MatrixIndex, VectorItem> {
	private VectorItem item = new VectorItem();
	private MatrixIndex index = new MatrixIndex();
	
	public void map(IntWritable column, Indices rows, Context context)
	throws IOException, InterruptedException {	
		double value = 1.0 / rows.get().length;
		index.setIndex(column.get());
		item.setValue(value);
		for (int row : rows.get()) {
			item.setIndex(row);
			context.write(index, item);
		}
	}
}