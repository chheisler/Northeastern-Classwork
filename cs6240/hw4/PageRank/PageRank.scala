package cs6240

import org.apache.hadoop.fs.Path
import org.apache.hadoop.io.Text
import org.apache.hadoop.mapreduce.Job
import org.apache.hadoop.mapreduce.Counters
import org.apache.hadoop.mapreduce.lib.input.FileInputFormat
import org.apache.hadoop.mapreduce.lib.output.FileOutputFormat
import org.apache.hadoop.mapreduce.lib.output.SequenceFileOutputFormat

import org.apache.spark.SparkConf
import org.apache.spark.SparkContext
import org.apache.spark.rdd.RDD
import org.apache.spark.storage.StorageLevel
import org.apache.spark.util.DoubleAccumulator

import scala.collection.mutable.PriorityQueue

import cs6240.parser.WikiParser

object PageRank {	
	// argument indices
	private val MASTER_INDEX = 0
	private val PARALLELISM_INDEX = 1
	private val PERSIST_INDEX = 2
	private val INPUT_INDEX = 3
	private val OUTPUT_INDEX = 4

	// common Spark context
	private var sc: SparkContext = null

	// RDD's of page ranks and links
	private var pageRanks: RDD[(String, Double)] = null
	private var pageLinks: RDD[(String, Array[String])] = null

	// number of pages in data set
	private var numPages: Long = 0

	// alpha parameter and associated values
	private var alpha: Double = 0.15
	private var oneMinusAlpha: Double = 1 - alpha
	private var alphaPerPage: Double = 0
	
	// delta value per page
	private var deltaPerPage: Double  = 0

	// run PageRank on data set and write top 100
	def main(args: Array[String]) {
		// parse the arguments
		val master = args(MASTER_INDEX)
		val parallelism = args(PARALLELISM_INDEX)
		val persist = args(PERSIST_INDEX).toBoolean
		val input = args(INPUT_INDEX)
		val output = args(OUTPUT_INDEX)

		// initialize the Spark context	and delta accumulator
		val conf = new SparkConf()
			.setAppName("PageRank")
			.setMaster(master)
			.set("spark.default.parallelism", parallelism)	
		sc = new SparkContext(conf)

		// parse the input and initialize ranks and links
		pageLinks = sc.textFile(input, parallelism.toInt)
			.mapPartitions(lines => new WikiParser(lines).iterator)
		numPages = pageLinks.count()
		val rank = 1.0 / numPages
		if (persist) pageLinks.persist(StorageLevel.MEMORY_AND_DISK)
		pageRanks = pageLinks.map({case (name, _) => (name, rank)})
		if (persist) pageRanks.cache()
	
		// set alpha per page and broadcast variables
		alphaPerPage = alpha / numPages
		sc.broadcast(alphaPerPage)
		sc.broadcast(oneMinusAlpha)
		
		// run 10 iterations of page rank
		for(i <- 1 to 10) {
			val pages = pageRanks.join(pageLinks)

			// update delta and deltaPerPage
			val delta = pages.filter({case (_, (rank, links)) => links.isEmpty})
				.map({case (_, (rank, _)) => rank})
				.reduce(_+_)
			deltaPerPage = delta / numPages
			sc.broadcast(deltaPerPage)
	
			// calculate new ranks for pages
			pageRanks = pages.flatMap({case (name, (rank, links)) =>
				val rankPerLink = rank / links.length
				val ranks = links.map(link => (link, rankPerLink))
				Array((name, deltaPerPage)) ++ ranks
			})
			.reduceByKey(_+_)
			.map({case (name, rank) => 
				(name, alphaPerPage + oneMinusAlpha * rank)
			})	
		}

		// find top 100 ranked pages
		val sorted = pageRanks.mapPartitions(findTop)
			.coalesce(1)
			.mapPartitions(findTop)
			.sortBy({case (_, rank) => -rank})
		sc.parallelize(sorted.take(100), 1)
			.saveAsTextFile(output)

		// clean up the Spark context
		sc.stop()
	}

	// ordering for top ranks
	val order = Ordering.by[(String, Double), (Double, String)]({
		case (name, rank) => (-rank, name)
	})

	// find the top 100 pages within a partition
	def findTop(ranks: Iterator[(String, Double)]): Iterator[(String, Double)] = {
		val top = new PriorityQueue()(order)
		for ((name, rank) <- ranks) {
			if (top.size < 100) top.enqueue((name, rank))
			else {
				val (_, low) = top.head
				if (rank > low) {
					top.dequeue()
					top.enqueue((name, rank))
				}
			}
		}
		return top.iterator
	}
}
