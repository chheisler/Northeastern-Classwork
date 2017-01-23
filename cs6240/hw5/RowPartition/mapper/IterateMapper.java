package pagerank.mapper;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.Indices;
import pagerank.writable.VectorItem;

// Mapper for the iterate job. As input it takes the sparse representation of
// the adjacency matrix, each entry in which is the index of a column and a
// list of rows for which it has non-zero values. The value of each entry is
// calculated as one over the number of non-zero values. For each entry, the
// row index is written as key and a vector item composed of the column index
// and the calculated value is written as the value.
public class IterateMapper
extends Mapper<IntWritable, Indices, IntWritable, VectorItem> {
	private VectorItem item = new VectorItem();
	private IntWritable index = new IntWritable();
	
	public void map(IntWritable column, Indices rows, Context context)
	throws IOException, InterruptedException {
		double value = 1.0 / rows.get().length;
		item.set(column.get(), value);
		for (int row : rows.get()) {
			index.set(row);
			context.write(index, item);
		}
	}
}