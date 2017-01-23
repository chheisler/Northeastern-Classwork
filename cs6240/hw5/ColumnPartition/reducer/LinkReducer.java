package pagerank.reducer;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;
import java.util.Iterator;

import pagerank.writable.PageIndex;

// Reducer for the link job. The input key is a page index and the value is
// is the name of a page which links to another. Page indices are grouped by
// page name and for each page name one page index will also contain a unique
// numerical index. This key is sorted first and used to recover the index of
// of the page with the same name. Each following page name value is then the
// name of a page which links to the page for which the index was recovered.
public class LinkReducer extends Reducer<PageIndex, Text, Text, IntWritable> {
	private Text page = new Text();
	private IntWritable index = new IntWritable();
	
	@Override
	public void reduce(PageIndex pageIndex, Iterable<Text> pages, Context context)
	throws IOException, InterruptedException {
		Iterator<Text> iter = pages.iterator();
		index.set(pageIndex.getIndex());
		iter.next();
		while (iter.hasNext()) {
			page.set(iter.next().toString());
			context.write(page, index);
		}
	}
}