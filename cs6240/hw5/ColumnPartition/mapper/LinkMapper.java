package pagerank.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;

import pagerank.writable.Links;
import pagerank.writable.PageIndex;

// The mapper for parsed link data in the link job. Each input record is a
// page name and a list of its links. For each link, page index is written
// with the page set to the link name and the parent page is written as a
// the value.
public class LinkMapper extends Mapper<Text, Links, PageIndex, Text> {
	private PageIndex pageIndex = new PageIndex();
	
	public void map(Text page, Links links, Context context)
	throws IOException, InterruptedException {
		for (String link : links.get()) {
			pageIndex.setPage(link);
			context.write(pageIndex, page);
		}
	}
}
