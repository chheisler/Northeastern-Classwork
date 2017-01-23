package pagerank.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

// The reducer for the iterate sum job. Takes the cross products calculated
// by the iterate product job, sums them and then combines them with the
// dangling probability mass and the alpha parameter to get a new rank.
public class IterateSumReducer
extends Reducer<IntWritable, DoubleWritable, IntWritable, DoubleWritable> {
	private DoubleWritable rankOut = new DoubleWritable();
	private int numPages;
	private double alpha;
	private double delta;
	
	@Override
	public void setup(Context context) {
		Configuration config = context.getConfiguration();
		numPages = config.getInt("NUM_PAGES", 0);
		alpha = config.getDouble("ALPHA", 0);
		delta = config.getDouble("DELTA", 0);
	}
	
	@Override
	public void reduce(IntWritable index, Iterable<DoubleWritable> ranks, Context context)
	throws IOException, InterruptedException {
		double sum = delta;
		for (DoubleWritable rankIn : ranks) sum += rankIn.get();
		rankOut.set(alpha / numPages + (1 - alpha) * sum);
		context.write(index, rankOut);
	}
}