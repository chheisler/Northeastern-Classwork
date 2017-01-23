package pagerank.reducer;

import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

// Reducer for the dangling job. The input key is a vector index and and the
// input value is a non-zero value at that index. For each key there will be
// at most two values, one from the dangling vector and another from the rank
// vector. If a key has two values, they are multiplied and added to a running
// sum. This sum is output on clean up.
public class DanglingReducer
extends Reducer<IntWritable, DoubleWritable, NullWritable, DoubleWritable> {
	private double sum = 0;
	
	@Override
	public void reduce(IntWritable index, Iterable<DoubleWritable> values, Context context)
	throws IOException, InterruptedException {
		double[] operands = new double[2];
		int count = 0;
		for (DoubleWritable value : values) {
			operands[count] = value.get();
			count++;
		}
		if (count == 2) sum += operands[0] * operands[1];
	}
	
	@Override
	public void cleanup(Context context)
	throws IOException, InterruptedException {
		NullWritable none = NullWritable.get();
		DoubleWritable delta = new DoubleWritable(sum);
		context.write(none, delta);
	}
}