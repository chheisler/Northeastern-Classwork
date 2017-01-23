package pagerank.reducer;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

import pagerank.writable.PageAndRank;

// The reducer for the top job. The input key is a page name and rank key
// which is sorted by rank in descending order, then by name in ascending
// order. For the first hundred entries, the name and ranks are extracted
// and output. The remaining entries are ignored. 
public class TopReducer
extends Reducer<PageAndRank, NullWritable, Text, DoubleWritable> {
	private Text page = new Text();
	private DoubleWritable rank = new DoubleWritable();
	private int count = 0;
	
	@Override
	public void reduce(PageAndRank key, Iterable<NullWritable> none, Context context)
	throws IOException, InterruptedException {
		if (count < 100) {
			page.set(key.getPage());
			rank.set(key.getRank());
			context.write(page, rank);
			count++;
		}
	}
}