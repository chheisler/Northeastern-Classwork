package pagerank.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.SequenceFile;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;

import java.io.IOException;
import java.util.Iterator;
import java.net.URI;

import pagerank.writable.VectorItem;

// Reducer for the iterate job. The key for each entry is a row index and
// the value for each entry is a vector item representing a non-zero value
// in that row. On setup, the current ranks are recovered from the distributed
// cache. For each call to map, the products of the vector items and their
// corresponding rank are summed, and the sum is written out as the new rank
// for page with the same index as the row index in the key.
public class IterateReducer
extends Reducer<IntWritable, VectorItem, IntWritable, DoubleWritable> {
	private DoubleWritable value = new DoubleWritable();
	private int numPages;
	private double[] ranks;
	private double alpha;
	private double delta;
	
	public void setup(Context context) throws IOException {
		Configuration config = context.getConfiguration();
		numPages = config.getInt("NUM_PAGES", 0);
		
		// retrieve the current rank vector
		ranks = new double[numPages];
		URI[] uris = context.getCacheFiles();
		for (URI uri : uris) {
			FileSystem fs = FileSystem.get(uri, config);
			Path path = new Path(uri);
			SequenceFile.Reader reader = new SequenceFile.Reader(fs, path, config);
			IntWritable index = new IntWritable();
			DoubleWritable rank = new DoubleWritable();
			while (reader.next(index, rank)) ranks[index.get()] = rank.get();
			reader.close();
		}
		
		alpha = config.getDouble("ALPHA", 0);
		delta = config.getDouble("DELTA", 0);
	}
	
	@Override
	public void reduce(IntWritable row, Iterable<VectorItem> items, Context context)
	throws IOException, InterruptedException {
		double sum = delta;
		for (VectorItem item : items) {
			sum += item.getValue() * ranks[item.getIndex()];
		}
		value.set(alpha / numPages + (1.0 - alpha) * sum);
		context.write(row, value);
	}
}