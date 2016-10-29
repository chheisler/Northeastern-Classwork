package cs6240;

import java.io.IOException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.Writable;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;

import cs6240.writable.Reading;
import cs6240.writable.Average;
import cs6240.util.Accumulator;

// a mapreduce job which uses no combiner
public class NoCombiner {
	// indices of data fields in CSV lines
	public static final int station_index = 0;
	public static final int type_index = 2;
	public static final int value_index = 3;
	
	public static void main(String[] args)
	throws IOException, InterruptedException, ClassNotFoundException {
		Configuration config = new Configuration();
		
		// create and configure mapreduce job
		Job job = new Job(config, "no combiner");
		job.setJarByClass(NoCombiner.class);
		job.setMapperClass(StationMapper.class);
		job.setReducerClass(StationReducer.class);
		job.setMapOutputValueClass(Reading.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Average.class);

	    // read command line arguments
		String[] otherArgs = new GenericOptionsParser(config, args).getRemainingArgs();
		if (otherArgs.length < 3) System.exit(2);
		for (int i = 0; i < otherArgs.length - 2; i++) {
			FileInputFormat.addInputPath(job, new Path(otherArgs[i]));
		}
		FileOutputFormat.setOutputPath(job, new Path(otherArgs[otherArgs.length - 2]));
		job.setNumReduceTasks(Integer.parseInt(otherArgs[otherArgs.length - 1]));
		
		// run job and wait for completion
		System.exit(job.waitForCompletion(true) ? 0 : 1);
	}
	
	// mapper which emits a type and measurement pair for TMIN and TMAX
	// measurements with the station as the key
	public static class StationMapper extends Mapper<Object, Text, Text, Reading> {
		private Text station = new Text();
		private Reading reading = new Reading();
	
		public void map(Object key, Text value, Context context)
		throws IOException, InterruptedException {
			String[] parts = value.toString().split(",");
			if (parts[type_index].equals("TMAX") || parts[type_index].equals("TMIN")) {
				station.set(parts[station_index]);
				reading.set(parts[type_index], Integer.parseInt(parts[value_index]));
				context.write(station, reading);
			}
		}		
	}
	
	// reducer which combines the readings for a single station into an
	// accumulator and then emits the average minimum and maximum temperatures
	// for the station
	public static class StationReducer extends Reducer<Text, Reading, Text, Average> {
		private Text station = new Text();
		private Average average = new Average();

		@Override
		public void reduce(Text key, Iterable<Reading> values, Context context)
		throws IOException, InterruptedException {
			// initialize accumulators for minimum and maximum temperature measures
			Accumulator minTemp = new Accumulator();
			Accumulator maxTemp = new Accumulator();
			
			// iterate through readings and update accumulators
			for (Reading reading : values) {
				String type = reading.getType();
				int value = reading.getValue();
				if (type.equals("TMIN")) minTemp.add(value);
				else maxTemp.add(value);
			}
			
			// write final average results for station
			average.set(minTemp.average(), maxTemp.average());
			context.write(key, average);
		}
	}
}
