package pagerank.combiner;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Reducer;

import java.io.IOException;

import pagerank.writable.Links;

public class ParseCombiner extends Reducer<Text, Links, Text, Links> {
	private Links empty = new Links();
	
	@Override
	public void reduce(Text name, Iterable<Links> links, Context context) 
	throws IOException, InterruptedException {
		Links linksOut = empty;
		for (Links l : links) {
			if (l.get().length > 0) {
				context.write(name, l);
				return;
			}
		}
		context.write(name, empty);
	}
}