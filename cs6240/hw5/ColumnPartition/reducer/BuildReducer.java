package pagerank.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;

import java.util.HashSet;
import java.util.Iterator;
import java.io.IOException;

import pagerank.writable.PageIndex;
import pagerank.writable.Indices;

// The reducer for the build job. The input key is a page index and the value
// is the index of a link. Page indices are grouped by page name, and for each
// page name one page index will also contain a unique numerical index. This
// key is sorted first and used to recover the column index in the adjacency
// matrix of the page with the same name. Each following numerical index value
// is then the row index of another page to which the page links.
public class BuildReducer
extends Reducer<PageIndex, IntWritable, IntWritable, Indices> {
	private IntWritable index = new IntWritable();
	private DoubleWritable rank = new DoubleWritable();
	private Indices linksOut = new Indices();
	private NullWritable nullOut = NullWritable.get();
	private MultipleOutputs outputs;

	@Override
	public void setup(Context context) {
		outputs = new MultipleOutputs(context);
		Configuration config = context.getConfiguration();
		int numPages = config.getInt("NUM_PAGES", 0);
		rank.set(1.0 / numPages);
	}
	
	@Override
	public void reduce(PageIndex pageIndex, Iterable<IntWritable> linksIn, Context context) 
	throws IOException, InterruptedException {
		index.set(pageIndex.getIndex());
		Iterator<IntWritable> iter = linksIn.iterator();
		HashSet<Integer> links = new HashSet<>();
		iter.next();
		while (iter.hasNext()) links.add(iter.next().get());
		
		// write an initial rank
		outputs.write("RANKS", index, rank, "ranks/part");
		
		// if the page is dangling write it to the dangling vector
		if (links.size() == 0) {
			outputs.write("DANGLING", index, nullOut, "dangling/part");
		}
		
		// else write it out to the adjacency matrix
		else {
			linksOut.set(links);
			outputs.write("ADJACENT", index, linksOut, "adjacent/part");
		}
	}
	
	@Override
	public void cleanup(Context context)
	throws IOException, InterruptedException {
		outputs.close();
	}
}