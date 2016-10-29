package cs6240;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Reducer;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.util.GenericOptionsParser;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;

import cs6240.writable.StationYear;
import cs6240.writable.Reading;
import cs6240.writable.Average;
import cs6240.writable.AverageList;
import cs6240.comparator.GroupComparator;
import cs6240.partitioner.StationPartitioner;
import cs6240.util.Accumulator;

import java.io.IOException;

public class TimeSeries {
	// indices of data fields in CSV lines
	public static final int STATION_INDEX = 0;
	public static final int DATE_INDEX = 1;
	public static final int TYPE_INDEX = 2;
	public static final int VALUE_INDEX = 3;
	
	public static void main(String[] args)
	throws IOException, InterruptedException, ClassNotFoundException {
		Configuration config = new Configuration();
		
		// create and configure mapreduce job
		Job job = new Job(config, "time series");
		job.setJarByClass(TimeSeries.class);
		job.setMapperClass(StationMapper.class);
		job.setMapOutputKeyClass(StationYear.class);
		job.setMapOutputValueClass(Reading.class);
		job.setPartitionerClass(StationPartitioner.class);
		job.setReducerClass(StationReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(IntWritable.class);
	    job.setGroupingComparatorClass(GroupComparator.class);
	    
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
	
	// a mapper which emits a the station and year of a measurement as the
	// key and which emits the year, type and value of a reading as value
	public static class StationMapper 
	extends Mapper<Object, Text, StationYear, Reading> {
		private StationYear stationYear = new StationYear();
		private Reading reading = new Reading();
		
		public void map(Object key, Text line, Context context)
		throws IOException, InterruptedException {
			String[] parts = line.toString().split(",");
			String type = parts[TYPE_INDEX];
			if (type.equals("TMIN") || type.equals("TMAX")) {
				String station = parts[STATION_INDEX];
				int year = Integer.parseInt(parts[DATE_INDEX].substring(0,4));
				int value = Integer.parseInt(parts[VALUE_INDEX]);
				stationYear.set(station, year);
				reading.set(type, year, value);
				context.write(stationYear, reading);
			}
		}
	}
	
	// a reducer which groups by station and orders input records by year
	// combines successive input records within a year into an accumulator,
	// calculates averages for each year and outputs the list of averages for
	// each station
	public static class StationReducer
	extends Reducer<StationYear, Reading, Text, AverageList> {
		private Text station = new Text();
		private AverageList averages;
		
		public void reduce(StationYear key, Iterable<Reading> values, Context context)
		throws IOException, InterruptedException {
			averages = new AverageList();
			Accumulator accumulator = new Accumulator();
			int currentYear = key.getYear();
			
			// iterate through the values and for each year find the averages
			for (Reading reading : values) {
				int year = reading.getYear();
				if (year != currentYear) {
					appendAccumulator(currentYear, accumulator);
					accumulator = new Accumulator();
					currentYear = year;
				}
				if (reading.getType().equals("TMIN"))
					accumulator.addMinTemp(reading.getValue());
				else accumulator.addMaxTemp(reading.getValue());
			}
			appendAccumulator(currentYear, accumulator);
			
			// write out the final results for all years
			station.set(key.getStation());
			context.write(station, averages);
		}
		
		// append the averages of an accumulator for a year to the output
		private void appendAccumulator(int year, Accumulator accumulator) {
			Average average = new Average();
			float minTempAvg = accumulator.averageMinTemp();
			float maxTempAvg = accumulator.averageMaxTemp();
			average.set(year, minTempAvg, maxTempAvg);
			averages.add(average);
		}
	}
}