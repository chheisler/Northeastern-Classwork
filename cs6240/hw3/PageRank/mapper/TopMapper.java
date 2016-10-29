package cs6240.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Mapper;

import cs6240.writable.Page;
import cs6240.writable.NameAndRank;

import java.util.PriorityQueue;
import java.io.IOException;

// A mapper which takes in page names and values and finds the top 100
// ranked pages using an in memory priority queue. The top 100 pages are
// emitted on cleanup.
public class TopMapper extends Mapper<Text, Page, NullWritable, NameAndRank> {
	private PriorityQueue<NameAndRank> top; // the top 100 pages to emit
	private long numPages;
	
	public void setup(Context context) {
		top = new PriorityQueue<>();
	}
	
	// For each page, put a new name, rank tuple in the prioritiy queue if
	// there are less than 100 items in or if the lowest ranked item in the
	// queue is less than the new page's rank.
	public void map(Text pageName, Page page, Context context)
	throws IOException, InterruptedException {
		String name = pageName.toString();
		double rank = page.getRank();
		if (top.size() < 100) top.offer(new NameAndRank(name, rank));
		else {
			NameAndRank bottom = top.peek();
			if (bottom.getRank() < rank) {
				top.poll();
				top.offer(new NameAndRank(name, rank));
			}
		}
	}
	
	// Write out the top 100 page names and ranks collected in the queue.
	public void cleanup(Context context)
	throws IOException, InterruptedException {
		NullWritable key = NullWritable.get();
		for (NameAndRank value : top) context.write(key, value);
	}
}
