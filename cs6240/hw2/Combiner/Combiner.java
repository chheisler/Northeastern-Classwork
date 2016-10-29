package cs6240;

import java.io.IOException;

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

// a mapreduce job which uses a combiner
public class Combiner {
	// indices of data fields in CSV lines
	public static final int station_index = 0;
	public static final int type_index = 2;
	public static final int value_index = 3;
	
	public static void main(String[] args)
	throws IOException, InterruptedException, ClassNotFoundException {
		Configuration config = new Configuration();
		
		// create and configure map reduce job
		Job job = new Job(config, "no combiner");
		job.setJarByClass(Combiner.class);
		job.setMapperClass(StationMapper.class);
		job.setCombinerClass(StationCombiner.class);
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
	
	// mapper creates an accumulator for a TMIN or TMAX value and emits it
	// with the station as key
	public static class StationMapper extends Mapper<Object, Text, Text, Accumulator> {
		private Text station = new Text();
		private Accumulator readings = new Accumulator();
	
		public void map(Object key, Text reading, Context context)
		throws IOException, InterruptedException {
			// extract the data from the CSV line
			String[] parts = reading.toString().split(",");
			String type = parts[type_index];
			int value = Integer.parseInt(parts[value_index]);
			
			// create a writable accumulator with the data and emit it
			Accumulator accumulator = new Accumulator();
			if (type.equals("TMIN")) accumulator.addMinTemp(value);
			else if (type.equals("TMAX")) accumulator.addMaxTemp(value);
			else return;
			station.set(parts[station_index]);
			readings.set(accumulator);
			context.write(station, readings);
		}		
	}
	
	// A combiner which takes a list of accumulators for a station, combines
	// their values into a single accumulator and emits the average minimum	
	// and maximum temperatures for the station
	public static class StationCombiner
	extends Reducer<Text, Accumulator, Text, Accumulator> {
		private Accumulator readings = new Accumulator();
		
		public void reduce(Text key, Iterable<Accumulator> values, Context context)
		throws IOException, InterruptedException {
			Accumulator accumulator = new Accumulator();
			for (Accumulator value : values) accumulator.add(value);
			readings.set(accumulator);
			context.write(key, readings);
		}
	}
	
	// A reducer which takes a list of accumulators for a station, combines
	// their values into a single accumulator and then emits the average
	// minimum and maximum temperatures for the station
	public static class StationReducer
	extends Reducer<Text, Accumulator, Text, Average> {
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
