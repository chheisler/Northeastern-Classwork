package cs6240;

import java.io.IOException;

import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.SequenceFile;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.FileStatus;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.util.GenericOptionsParser;
import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.Counter;
import org.apache.hadoop.mapreduce.Counters;

import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.SequenceFileInputFormat;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.SequenceFileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;

import cs6240.mapper.InputMapper;
import cs6240.mapper.IterateMapper;
import cs6240.mapper.TopMapper;
import cs6240.reducer.IterateReducer;
import cs6240.reducer.TopReducer;
import cs6240.combiner.IterateCombiner;
import cs6240.writable.Page;
import cs6240.writable.NameAndRank;

// A series of MapReduce jobs which implements the PageRank algorithm.
public class PageRank {
	private static int NUM_ITERATIONS = 10;
	private static String[] inputs;
	private static String output;
	private static int num_reducers;
	
	public static void main(String[] args)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Configuration config = new Configuration();
		config.setDouble("alpha", 0.15);
		FileSystem fileSystem = FileSystem.get(config);
		
		// parse and read the arguments
		String[] otherArgs = new GenericOptionsParser(config, args).getRemainingArgs();
		if (otherArgs.length < 3) System.exit(2);
		inputs = new String[args.length - 2];
		for (int i = 0; i < args.length - 2; i++) inputs[i] = otherArgs[i];
		output = otherArgs[otherArgs.length - 2];
		num_reducers = Integer.parseInt(otherArgs[otherArgs.length - 1]);
		
		// run input, iterate and top-hundred jobs
		input(config, otherArgs);
		for (int i = 0; i < NUM_ITERATIONS; i++) iterate(config, i);
		top(config);
	}
	
	
	// Run a job to parse the pages and create an initial graph.
	private static void input(Configuration config, String[] args)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = new Job(config, "input");
		job.setJarByClass(PageRank.class);
		job.setNumReduceTasks(num_reducers);
		job.setMapperClass(InputMapper.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Page.class);
		job.setOutputFormatClass(SequenceFileOutputFormat.class);
		for (String input : inputs) FileInputFormat.addInputPath(job, new Path(input));
		FileOutputFormat.setOutputPath(job, new Path(output + "/iter0"));
		if (!job.waitForCompletion(true)) throw new Exception("Input job failed!");
		
		// configure the number of pages, alpha and an initial delta per page
		Counters counters = job.getCounters();
		long numPages = counters.findCounter("pagerank", "pages").getValue();
		double delta = (double) counters.findCounter("pagerank", "dangling").getValue();
		double alpha = config.getDouble("alpha", 0);
		config.setLong("numPages", numPages);
		config.setDouble("oneMinusAlpha", 1 - alpha);
		config.setDouble("deltaPerPage", delta / numPages);
	}
	
	// Run a job corresponding to one iteration of the PageRank algorithm. In
	// addition to regular output the job also rights the sum of ranks from
	// dangling nodes in each reducer to separate files so that the rank
	// contribution of dangling nodes can be calculated for the next iteration.
	private static void iterate(Configuration config, int i)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = new Job(config, "iterate");
		job.setJarByClass(PageRank.class);
		job.setNumReduceTasks(num_reducers);
		job.setMapperClass(IterateMapper.class);
		job.setCombinerClass(IterateCombiner.class);
		job.setReducerClass(IterateReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Page.class);
		MultipleOutputs.addNamedOutput(job, "delta", SequenceFileOutputFormat.class, 
				NullWritable.class, DoubleWritable.class);
		job.setInputFormatClass(SequenceFileInputFormat.class);
		job.setOutputFormatClass(SequenceFileOutputFormat.class);
		FileInputFormat.addInputPath(job, new Path(output + "/iter" + i + "/part-r-*"));
		FileOutputFormat.setOutputPath(job, new Path(output + "/iter" + (i + 1)));
		if (!job.waitForCompletion(true)) throw new Exception("Iterate job failed!");
		
		// update the rank from dangling pages for the next iteration
		setDelta(config, i  + 1);
	}
	
	// Run a job to find the top 100 ranked pages.
	private static void top(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = new Job(config, "top");
		job.setJarByClass(PageRank.class);
		job.setNumReduceTasks(1);
		job.setMapperClass(TopMapper.class);
		job.setReducerClass(TopReducer.class);
		job.setOutputKeyClass(NullWritable.class);
		job.setOutputValueClass(NameAndRank.class);
		job.setInputFormatClass(SequenceFileInputFormat.class);
		FileInputFormat.addInputPath(job, new Path(output + "/iter" + NUM_ITERATIONS + "/part-r-*"));
		FileOutputFormat.setOutputPath(job, new Path(output + "/top"));
		if (!job.waitForCompletion(true)) throw new Exception("Top job failed!");
	}
	
	// Read the additional delta output files from an iteration and use them
	// to update the rank contribution of dangling nodes for the next iteration.
	private static void setDelta(Configuration config, int i)
	throws IOException {
		Path deltasPath = new Path(output + "/iter" + i + "/delta");
		FileSystem fileSystem = FileSystem.get(deltasPath.toUri(), config);
		FileStatus[] files = fileSystem.listStatus(deltasPath);
		double delta = 0;
		NullWritable key = NullWritable.get();
		DoubleWritable value = new DoubleWritable();
		for (FileStatus file : files) {
			Path filePath = file.getPath();
			SequenceFile.Reader reader = new SequenceFile.Reader(config, SequenceFile.Reader.file(filePath));
			reader.next(key, value);
			delta += value.get();
			reader.close();
		}
		long numPages = config.getLong("numPages", 0);
		config.setDouble("deltaPerPage", delta / numPages);
	}
}
