package pagerank.reducer;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.Counter;

import java.io.IOException;

import pagerank.writable.Links;

// Reducer for the parse job. The input key is the name of a page and the input
// values are lists of links for the page. One may contain actual links for the
// page, the rest are empty dummies written out with the name of a parsed link
// so that the parsed link is present as a dangling node even if it is missing
// from the data set. The list of actual links is recovered if present. The
// output key is the name of the page and the output value is its list of
// of links.
//
// A count of items processed by the reducer is also kept. This information is
// saved on cleanup in the configuration as the number of records sent to this
// partition using the page name as key so that an offset for page indices can
// be recovered in the index job. 
public class ParseReducer extends Reducer<Text, Links, Text, Links> {
	private Links empty = new Links();
	private long count = 0;
	
	@Override
	public void reduce(Text name, Iterable<Links> links, Context context)
	throws IOException, InterruptedException {
		Links linksOut = empty;
		for (Links linksIn : links) {
			if (linksIn.get().length != 0) linksOut = linksIn;
		}
		context.write(name, linksOut);
		count++;
	}
	
	public void cleanup(Context context) {
		Configuration config = context.getConfiguration();
	    String partition = config.get("mapred.task.partition");
		Counter counter = context.getCounter("PageRank", "PART_" + partition + "_SIZE");
		counter.increment(count);
	}
}
