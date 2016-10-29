package cs6240;

import java.io.IOException;
import java.util.HashMap;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;

import cs6240.writable.Accumulator;
import cs6240.writable.Average;

// a mapreduce job which uses an in mapper hashmap to combine records
public class InMapperCombiner {
	// indices of data fields in CSV lines
	public static final int station_index = 0;
	public static final int type_index = 2;
	public static final int value_index = 3;
	
	public static void main(String[] args)
	throws IOException, InterruptedException, ClassNotFoundException {
		Configuration config = new Configuration();
		
		// create and configure mapreduce job
		Job job = new Job(config, "no combiner");
		job.setJarByClass(InMapperCombiner.class);
		job.setMapperClass(StationMapper.class);
		job.setReducerClass(StationReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Average.class);
		job.setMapOutputValueClass(Accumulator.class);
		
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
	
	// mapper which stores local accumulators for each station and emits them
	// on cleanpu
	public static class StationMapper extends Mapper<Object, Text, Text, Accumulator> {
		private Text station = new Text();
		private Accumulator readings = new Accumulator();
		private HashMap<String, Accumulator> accumulators;
		
		// initialize a map from station names to accumulators
		public void setup(Context context) {
			accumulators = new HashMap<>();
		}
		
		public void map(Object key, Text reading, Context context)
		throws IOException, InterruptedException {
			// extract the data from the CSV line
			String[] parts = reading.toString().split(",");
			String station = parts[station_index];
			String type = parts[type_index];
			if (!type.equals("TMIN") && !type.equals("TMAX")) return;
			
			// obtain an accumulator for the station
			Accumulator accumulator;
			if (accumulators.containsKey(station)) accumulator = accumulators.get(station);
			else {
				accumulator = new Accumulator();
				accumulators.put(station, accumulator);
			}
			
			// add the measured value to the accumulator
			int value = Integer.parseInt(parts[value_index]);
			if (type.equals("TMIN")) accumulator.addMinTemp(value);
			else if (type.equals("TMAX")) accumulator.addMaxTemp(value);
		}
		
		// for each station key in the map emit it and its accumulator
		public void cleanup(Context context) throws IOException, InterruptedException {
			for (HashMap.Entry<String, Accumulator> entry : accumulators.entrySet()) {
				String key = entry.getKey();
				Accumulator value = entry.getValue();
				station.set(key);
				readings.set(value);
				context.write(station, readings);
			}
		}
	}
	
	// A combiner which takes a list of accumulators for a station, combines
	// their values into a single accumulator and emits the average minimum
	// and maximum temperatures for the station
	public static class StationReducer extends Reducer<Text, Accumulator, Text, Average> {
		private Average average = new Average();

		public void reduce(Text key, Iterable<Accumulator> values, Context context)
		throws IOException, InterruptedException {
			Accumulator accumulator = new Accumulator();
			for (Accumulator value  : values) accumulator.add(value);
			float minTempAverage = accumulator.averageMinTemp();
			float maxTempAverage = accumulator.averageMaxTemp();
			average.set(minTempAverage, maxTempAverage);
			context.write(key, average);
		}
	}
}
