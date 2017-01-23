package pagerank.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.util.PriorityQueue;
import java.io.IOException;

import pagerank.writable.PageAndRank;

// Mapper for the top job. On setup a local priority queue is initialized.
// Each entry is the name of a page and its rank. If there are less than
// a hundred items in the queue, the page and rank are added to it. If there
// are a hundred items in the queue but the rank is greater than the lowest
// one in the queue, the lowest item in the queue is evicted and the page
// and rank are inserted in its place. On cleanup, the top hundred items
// sorted in the queue are written out.
public class TopMapper
extends Mapper<Text, DoubleWritable, PageAndRank, NullWritable> {
	private PriorityQueue<PageAndRank> top; // the top 100 pages to emit
	
	@Override
	public void setup(Context context) {
		top = new PriorityQueue<>();
	}
	
	@Override
	public void map(Text page, DoubleWritable rank, Context context)
	throws IOException, InterruptedException {
		if (top.size() < 100) top.offer(new PageAndRank(page.toString(), rank.get()));
		else {
			PageAndRank bottom = top.peek();
			if (bottom.getRank() < rank.get()) {
				top.poll();
				top.offer(new PageAndRank(page.toString(), rank.get()));
			}
		}
	}
	
	public void cleanup(Context context)
	throws IOException, InterruptedException {
		NullWritable none = NullWritable.get();
		for (PageAndRank PageAndRank : top) context.write(PageAndRank, none);
	}
}
