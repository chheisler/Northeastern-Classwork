lazy val root = (project in file(".")).
	settings(
		name := "PageRank",
		version := "1.0",
		mainClass in Compile := Some("cs6240.PageRank"),
		scalaVersion := "2.11.8"
	)

// Spark
libraryDependencies += "org.apache.spark" %% "spark-core" % "2.0.1"
