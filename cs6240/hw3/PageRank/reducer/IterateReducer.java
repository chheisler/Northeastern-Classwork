package cs6240.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;

import java.io.IOException;

import cs6240.writable.Page;

// A reducer which takes in a page name and a list of pages, and emits a
// the page name and its page with the updated rank. One of the incoming pages
// contains the link list for the page, the others contain the rank
// contributions from neighboring pages.
public class IterateReducer extends Reducer<Text, Page, Text, Page> {
	private long numPages = 0; // the total number of pages
	private double alpha; // the probability of randomly jumping to a page
	private double oneMinusAlpha; // probability of coming to this page from a link
	private double delta = 0; // the total rank of dangling pages
	private double deltaPerPage; // the rank from dangling pages to add to each page
	private MultipleOutputs multiOut;
	private Page outPage = new Page();

	public void setup(Context context) {
		multiOut = new MultipleOutputs(context);
		Configuration config = context.getConfiguration();
		numPages = config.getLong("numPages", 0);
		alpha = config.getDouble("alpha", 0);
		oneMinusAlpha = config.getDouble("oneMinusAlpha", 0);
		deltaPerPage = config.getDouble("deltaPerPage", 0);
	}
	
	public void reduce(Text pageName, Iterable<Page> inPages, Context context)
	throws IOException, InterruptedException {
		// add the rank from dangling pages
		double rank = deltaPerPage;
		
		// recover the page's links and add the rank from incoming pages
		for (Page inPage : inPages) {
			rank += inPage.getRank();
			String[] linkNames = inPage.getLinkNames();
			if (linkNames != null) outPage.setLinkNames(linkNames);
		}

		// add the weight from a random jump
		// pages are intialized to rank of 1, so use alpha, not alpha / |V|
		rank = alpha + oneMinusAlpha * rank;

		// if the page is dangling add its rank to the total delta
		if (outPage.getLinkNames().length == 0) delta += rank;
		
		// write the page with its updated rank
		outPage.setRank(rank);
		context.write(pageName, outPage);
	}
	
	// write out the total delta so it can be used the next iteration
	public void cleanup(Context context)
	throws IOException, InterruptedException {
		multiOut.write("delta", NullWritable.get(), new DoubleWritable(delta), "delta/part");
		multiOut.close();
	}
}
