package cs6240.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import cs6240.writable.Page;

// A mapper which takes in a page name as a key and the rank and outlinks of
// the page as a value. It emits the key and value as is to maintain the
// structure of the graph, and then for each outlink emits an equal portion
// of its rank with the outlink's page name as key
public class IterateMapper extends Mapper<Text, Page, Text, Page> {
	Text outLink = new Text();
	Page outPage = new Page();
	
	public void map(Text pageName, Page inPage, Context context)
	throws IOException, InterruptedException {
		// write the name and page links to keep the graph structure
		outPage.set(0, inPage.getLinkNames());
		context.write(pageName, outPage);
		
		// distribute the page's rank equally to all linked pages
		String[] linkNames = inPage.getLinkNames();
		double rank = inPage.getRank() / linkNames.length;
		outPage.set(rank, null);
		for (String linkName : linkNames) {
			outLink.set(linkName);
			context.write(outLink, outPage);
		}
	}
}
