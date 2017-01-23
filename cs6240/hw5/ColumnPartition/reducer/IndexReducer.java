package pagerank.reducer;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.Counter;

import java.io.IOException;

import pagerank.writable.Links;

// The reducer for the index job. In the setup the number of elements sent
// to previous partitions in the parse job is recovered from the configuration
// and summed to create an offset. The parsed pages passed into the reducer
// are then assigned sequential numerical indices starting from this offset.
public class IndexReducer extends Reducer<Text, Links, Text, IntWritable> {
	private int index = 0;
	private IntWritable indexWritable = new IntWritable();
	
	@Override
	public void setup(Context context) {
		Configuration config = context.getConfiguration();
	    int partition = Integer.parseInt(config.get("mapred.task.partition"));
	    for (int i = 0; i < partition; i++) {
	    	index += config.getLong("PART_" + i + "_SIZE", 0);
	    }
	}
	
	@Override
	public void reduce(Text name, Iterable<Links> links, Context context)
	throws IOException, InterruptedException {
		indexWritable.set(index);
		context.write(name, indexWritable);
		index++;
	}
}
