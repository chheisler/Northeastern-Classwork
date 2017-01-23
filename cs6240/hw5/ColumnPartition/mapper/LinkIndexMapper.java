package pagerank.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;
import pagerank.writable.PageIndex;

// The mapper for page indices in the build job. Each index entry is a unique
// page name and unique numerical index. Each entry is written as a page index
// key with a null string. This key is used to recover the index of page names
// mapped from the LinkMapper in the LinkReducer.
public class LinkIndexMapper extends Mapper<Text, IntWritable, PageIndex, Text> {
	private PageIndex pageIndex = new PageIndex();
	private Text empty = new Text();
	
	public void map(Text page, IntWritable index, Context context)
	throws IOException, InterruptedException {
		pageIndex.set(page.toString(), index.get());
		context.write(pageIndex, empty);
	}
}