package cs6240.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.util.LinkedList;
import java.util.PriorityQueue;
import java.io.IOException;

import cs6240.writable.NameAndRank;

// A reducer which takes in a name and rank tuple and uses an in memory
// priority queue to find the top 100 ranked pages. Emits these pages on
// cleanup.
public class TopReducer
extends Reducer<NullWritable, NameAndRank, NullWritable, NameAndRank> {
	private PriorityQueue<NameAndRank> top; // priority queue of top ranked pages
	
	public void setup(Context context) {
		top = new PriorityQueue<>();
	}
	
	// For each incoming value, put it in the priority queue if there are less than
	// 100 items in it or if its rank is higher than the lowest member in the queue.
	public void reduce(NullWritable key, Iterable<NameAndRank> values, Context context)
	throws IOException, InterruptedException {
		for (NameAndRank value : values) {
			if (top.size() < 100) top.offer(new NameAndRank(value));
			else {
				NameAndRank bottom = top.peek();
				if (bottom.getRank() < value.getRank()) {
					top.poll();
					top.offer(new NameAndRank(value));
				}
			}
		}
	}
	
	// Write the top 100 pages in the priority queue out in descending order.
	// All ranks are normalized to improve the legibility of the final output.
	public void cleanup(Context context)
	throws IOException, InterruptedException {
		NullWritable key = NullWritable.get();
		LinkedList<NameAndRank> stack = new LinkedList<>();
		long numPages = context.getConfiguration().getLong("numPages", 0);
		while (top.size() > 0) {
			NameAndRank value = top.poll();
			value.setRank(value.getRank() / numPages);
			stack.push(value);
		}
		while (stack.size() > 0) context.write(key, stack.pop());
	}
}
