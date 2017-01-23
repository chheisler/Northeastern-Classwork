package pagerank.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.mapreduce.Mapper;

import java.io.IOException;
import pagerank.writable.PageIndex;

// The mapper for page indices in the build job. Each index entry is a unique
// page name and unique numerical index. Each entry is written as a page index
// key with a dummy value of 0. This key is used to recover the index of
// page names mapped from the BuildLinkMapper in the BuildReducer.
public class BuildIndexMapper
extends Mapper<Text, IntWritable, PageIndex, IntWritable> {
	private PageIndex pageIndex = new PageIndex();
	private IntWritable zero = new IntWritable(0);
	
	public void map(Text page, IntWritable index, Context context)
	throws IOException, InterruptedException {
		pageIndex.set(page.toString(), index.get());
		context.write(pageIndex, zero);
	}
}