package pagerank.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.PageIndex;

// The mapper for links for the build job. Each link entry is the name of a
// page and the index of a page it links to. For each entry the key output
// is a page index object with just the page name set and the value is the
// link index.
public class BuildLinkMapper
extends Mapper<Text, IntWritable, PageIndex, IntWritable> {
	private PageIndex pageIndex = new PageIndex();
	
	public void map(Text page, IntWritable link, Context context)
	throws IOException, InterruptedException {
		pageIndex.setPage(page.toString());
		context.write(pageIndex, link);
	}
}