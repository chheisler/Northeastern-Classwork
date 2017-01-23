package pagerank.reducer;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;
import java.util.Iterator;

import pagerank.writable.PageIndex;

// Reducer for the recover job. The input key is a page index and the value is
// the rank of a page. Page indices are grouped by numerical index and for
// each numerical index one page index will also contain a unique page name.
// This key is sorted first and used to recover the name of the page with the
// same numerical index. The following rank value is then the rank of the page
// for which the name was recovered.
public class RecoverReducer
extends Reducer<PageIndex, DoubleWritable, Text, DoubleWritable> {
	private Text page = new Text();
	
	@Override
	public void reduce(PageIndex pageIndex, Iterable<DoubleWritable> ranks, Context context)
	throws IOException, InterruptedException {
		Iterator<DoubleWritable> iter = ranks.iterator();
		page.set(pageIndex.getPage());
		iter.next();
		if (iter.hasNext()) context.write(page, iter.next());
	}
}