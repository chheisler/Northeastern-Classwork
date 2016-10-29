package cs6240.combiner;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

import cs6240.writable.Page;

// A combiner which takes in a page name and a list of pages, and emits a
// the page name and its page with the updated rank. One of the incoming pages
// may contain the link list for the page, the others contain the rank
// contributions from neighboring pages.
public class IterateCombiner extends Reducer<Text, Page, Text, Page> {
	private Page outPage = new Page();
	
	// add the rank from incoming pages and recover its link list if available
	public void reduce(Text pageName, Iterable<Page> inPages, Context context)
	throws IOException, InterruptedException {
		double rank = 0;
		for (Page inPage : inPages) {
			rank += inPage.getRank();
			String[] linkNames = inPage.getLinkNames();
			if (linkNames != null) outPage.setLinkNames(linkNames);
		}
		outPage.setRank(rank);
		context.write(pageName, outPage);
	}
}
