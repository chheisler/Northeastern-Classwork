package pagerank;

import java.io.IOException;
import java.text.DecimalFormat;
import java.net.URI;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.IntWritable;
import org.apache.hadoop.io.DoubleWritable;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.io.SequenceFile;
import org.apache.hadoop.conf.Configuration;
import org.apache.hadoop.fs.FileSystem;
import org.apache.hadoop.fs.Path;
import org.apache.hadoop.util.GenericOptionsParser;

import org.apache.hadoop.mapreduce.Job;
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.SequenceFileInputFormat;
import org.apache.hadoop.mapreduce.lib.input.MultipleInputs;
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.TextOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.SequenceFileOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.NullOutputFormat;
import org.apache.hadoop.mapreduce.lib.output.MultipleOutputs;
import org.apache.hadoop.mapreduce.Counters;
import org.apache.hadoop.mapreduce.CounterGroup;
import org.apache.hadoop.mapreduce.Counter;

import pagerank.mapper.*;
import pagerank.combiner.*;
import pagerank.reducer.*;
import pagerank.writable.*;
import pagerank.partitioner.*;
import pagerank.comparator.*;

// A series of MapReduce jobs which implements the PageRank algorithm.
public class PageRank {
	// indices of arguments
	private static int INPUT_INDEX = 0;
	private static int OUTPUT_INDEX = 1;
	private static int NUM_REDUCERS_INDEX = 2;
	
	// number of iterations to run
	private static int NUM_ITERATIONS = 10;
	
	// parsed argument values
	private static String input;
	private static String output;
	private static int numReducers;
	
	// format for retrieving part files
	private static DecimalFormat partFormat = new DecimalFormat("part-r-00000");
	
	public static void main(String[] args)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Configuration config = new Configuration();
		config.setDouble("ALPHA", 0.15);
		FileSystem fileSystem = FileSystem.get(config);
		
		// parse and read the arguments
		String[] otherArgs = new GenericOptionsParser(config, args).getRemainingArgs();
		if (otherArgs.length < 3) System.exit(2);
		input = otherArgs[INPUT_INDEX];
		output = otherArgs[OUTPUT_INDEX];
		numReducers = Integer.parseInt(otherArgs[NUM_REDUCERS_INDEX]);
		
		// run the jobs for PageRank
		parse(config);
		index(config);
		link(config);
		build(config);
		dangling(config, "matrices/ranks", "delta0");
		iterate(config, "matrices/ranks", "iter1");
		for (int i = 1; i < NUM_ITERATIONS; i++) {
			dangling(config, "iter" + i, "delta" + i);
			iterate(config, "iter" + i, "iter" + (i + 1));
		}
		recover(config);
		top(config);
	}
	
	// run a job to parse the pages
	private static void parse(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "PARSE", false, true);
		job.setMapperClass(ParseMapper.class);
		job.setCombinerClass(ParseCombiner.class);
		job.setReducerClass(ParseReducer.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(Links.class);
		FileInputFormat.addInputPath(job, new Path(input));
		FileOutputFormat.setOutputPath(job, new Path(output + "/parsed"));
		if (!job.waitForCompletion(true)) throw new Exception("Parse job failed!");
		
		// counter nonsense
		Counters counters = job.getCounters();
		int numPages = 0;
		for (int i = 0; i < numReducers; i++) {
			String name = "PART_" + i + "_SIZE";
			Counter counter = counters.findCounter("PageRank", name);
			config.setLong(name, counter.getValue());
			numPages += (int) counter.getValue();
		}
		config.setInt("NUM_PAGES", numPages);
	}
	
	// run a job to index the pages
	private static void index(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "INDEX");
		job.setReducerClass(IndexReducer.class);
		job.setMapOutputKeyClass(Text.class);
		job.setMapOutputValueClass(Links.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(IntWritable.class);
		FileInputFormat.addInputPath(job, new Path(output + "/parsed"));
		FileOutputFormat.setOutputPath(job, new Path(output + "/indices"));
		if (!job.waitForCompletion(true)) throw new Exception("Index job failed!");
	}
	
	// run job to link pages to other page indices
	private static void link(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "LINK");
		job.setReducerClass(LinkReducer.class);
		job.setPartitionerClass(LinkPartitioner.class);
		job.setSortComparatorClass(PageSortComparator.class);
		job.setGroupingComparatorClass(PageIndexComparator.class);
		job.setMapOutputKeyClass(PageIndex.class);
		job.setMapOutputValueClass(Text.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(IntWritable.class);
		MultipleInputs.addInputPath(job, new Path(output + "/parsed"),
				SequenceFileInputFormat.class, LinkMapper.class);
		MultipleInputs.addInputPath(job, new Path(output + "/indices"),
				SequenceFileInputFormat.class, LinkIndexMapper.class);
		FileOutputFormat.setOutputPath(job, new Path(output + "/links"));
		if (!job.waitForCompletion(true)) throw new Exception("Link job failed!");
	}
	
	// run job to build matrices
	private static void build(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "BUILD");
		job.setReducerClass(BuildReducer.class);
		job.setMapOutputKeyClass(PageIndex.class);
		job.setMapOutputValueClass(IntWritable.class);
		job.setPartitionerClass(BuildPartitioner.class);
		job.setSortComparatorClass(PageSortComparator.class);
		job.setGroupingComparatorClass(PageIndexComparator.class);
		MultipleInputs.addInputPath(job, new Path(output + "/indices"),
				SequenceFileInputFormat.class, BuildIndexMapper.class);
		MultipleInputs.addInputPath(job, new Path(output + "/links"),
				SequenceFileInputFormat.class, BuildLinkMapper.class);
		MultipleOutputs.addNamedOutput(job, "RANKS", SequenceFileOutputFormat.class,
				IntWritable.class, DoubleWritable.class);
		MultipleOutputs.addNamedOutput(job, "ADJACENT", SequenceFileOutputFormat.class,
				IntWritable.class, Indices.class);
		MultipleOutputs.addNamedOutput(job, "DANGLING", SequenceFileOutputFormat.class,
				IntWritable.class, NullWritable.class);
		FileOutputFormat.setOutputPath(job, new Path(output + "/matrices"));
		if (!job.waitForCompletion(true)) throw new Exception("Build job failed!");
	}
	
	// run job to calculate dangling contribution
	private static void dangling(Configuration config, String rankDir, String danglingDir)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "DANGLING");
		job.setReducerClass(DanglingReducer.class);
		job.setMapOutputKeyClass(IntWritable.class);
		job.setMapOutputValueClass(DoubleWritable.class);
		job.setOutputKeyClass(NullWritable.class);
		job.setOutputValueClass(DoubleWritable.class);
		job.setMapperClass(DanglingMapper.class);
		job.setOutputFormatClass(SequenceFileOutputFormat.class);
		MultipleInputs.addInputPath(job, new Path(output + "/" + rankDir),
				SequenceFileInputFormat.class, RankMapper.class);
		MultipleInputs.addInputPath(job, new Path(output + "/matrices/dangling"),
				SequenceFileInputFormat.class, DanglingMapper.class);
		FileOutputFormat.setOutputPath(job, new Path(output + "/" + danglingDir));
		if (!job.waitForCompletion(true)) throw new Exception("Update dangling failed!");
		
		// update the dangling probability mass per page
		double delta = 0;
		for (int i = 0; i < numReducers; i++) {
			String filename = output + "/" + danglingDir + "/" + partFormat.format(i);
			Path path = new Path(filename);
			FileSystem fs = FileSystem.get(path.toUri(), config);
			SequenceFile.Reader reader = new SequenceFile.Reader(fs, path, config);
			NullWritable none = NullWritable.get();
			DoubleWritable rank = new DoubleWritable();
			while (reader.next(none, rank)) delta += rank.get();
			reader.close();
		}
		config.setDouble("DELTA", delta);
	}
	
	// update ranks
	private static void iterate(Configuration config, String rankDir, String outDir)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		// run job to calculate outer products for column, row pairs
		Job job = makeJob(config, "ITERATE_PRODUCT");
		job.setReducerClass(IterateProductReducer.class);
		job.setMapOutputKeyClass(MatrixIndex.class);
		job.setMapOutputValueClass(VectorItem.class);
		job.setOutputKeyClass(IntWritable.class);
		job.setOutputValueClass(DoubleWritable.class);
		job.setPartitionerClass(IteratePartitioner.class);
		job.setGroupingComparatorClass(IterateGroupComparator.class);
		MultipleInputs.addInputPath(job, new Path(output + "/" + rankDir),
				SequenceFileInputFormat.class, IterateRankMapper.class);
		MultipleInputs.addInputPath(job, new Path(output + "/matrices/adjacent"),
				SequenceFileInputFormat.class, IterateMapper.class);
		FileOutputFormat.setOutputPath(job, new Path(output + "/outer-" + outDir));	
		if (!job.waitForCompletion(true)) throw new Exception("Update rank failed!");
		
		// run job to sum up outer products
		job = makeJob(config, "ITERATE_SUM");
		job.setReducerClass(IterateSumReducer.class);
		job.setOutputKeyClass(IntWritable.class);
		job.setOutputValueClass(DoubleWritable.class);
		FileInputFormat.addInputPath(job, new Path(output + "/outer-" + outDir));
		FileOutputFormat.setOutputPath(job, new Path(output + "/" + outDir));
		if (!job.waitForCompletion(true)) throw new Exception("Update rank failed!");
	}
	
	// recover the names of ranked pages
	private static void recover(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "RECOVER");
		job.setReducerClass(RecoverReducer.class);
		job.setMapOutputKeyClass(PageIndex.class);
		job.setMapOutputValueClass(DoubleWritable.class);
		job.setOutputKeyClass(Text.class);
		job.setOutputValueClass(DoubleWritable.class);
		job.setPartitionerClass(RecoverPartitioner.class);
		job.setSortComparatorClass(IndexSortComparator.class);
		job.setGroupingComparatorClass(PageIndexComparator.class);
		MultipleInputs.addInputPath(job, new Path(output + "/iter" + NUM_ITERATIONS),
				SequenceFileInputFormat.class, RecoverRankMapper.class);
		MultipleInputs.addInputPath(job, new Path(output + "/indices"),
				SequenceFileInputFormat.class, RecoverIndexMapper.class);
		FileOutputFormat.setOutputPath(job, new Path(output + "/ranks"));
		if (!job.waitForCompletion(true)) throw new Exception("Recover job failed!");
	}
	
	// find the top 100 pages
	private static void top(Configuration config)
	throws Exception, IOException, InterruptedException, ClassNotFoundException {
		Job job = makeJob(config, "TOP", 1, true, false);
		job.setMapperClass(TopMapper.class);
		job.setReducerClass(TopReducer.class);
		job.setOutputKeyClass(PageAndRank.class);
		job.setOutputValueClass(NullWritable.class);
		job.setSortComparatorClass(TopSortComparator.class);
		FileInputFormat.addInputPath(job, new Path(output + "/ranks"));
		FileOutputFormat.setOutputPath(job, new Path(output + "/top"));
		if (!job.waitForCompletion(true)) throw new Exception("Top job failed!");
	}
	
	// helpers to create job
	private static Job makeJob(Configuration config, String name, int parts, boolean seqIn, boolean seqOut)
	throws IOException {
		Job job = new Job(config, name);
		job.setJarByClass(PageRank.class);
		job.setNumReduceTasks(parts);
		if (seqIn) job.setInputFormatClass(SequenceFileInputFormat.class);
		if (seqOut) job.setOutputFormatClass(SequenceFileOutputFormat.class);
		return job;
	}
	
	private static Job makeJob(Configuration config, String name, boolean seqIn, boolean seqOut)
	throws IOException {
		return makeJob(config, name, numReducers, seqIn, seqOut);
	}
	
	private static Job makeJob(Configuration config, String name)
	throws IOException {
		return makeJob(config, name, true, true);
	}
}
