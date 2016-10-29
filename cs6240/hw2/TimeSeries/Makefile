INPUT = 1880.csv 1881.csv 1882.csv 1883.csv 1884.csv 1885.csv 1886.csv 1887.csv 1888.csv 1889.csv
OUTPUT = output
NUM_REDUCERS = 5

TimeSeries.jar: *.java writable/*.java comparator/*.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/TimeSeries-all.jar TimeSeries.jar

run: TimeSeries.jar
	rm -rf ${OUTPUT}
	hadoop jar TimeSeries.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS}

clean:
	rm -rf build TimeSeries.jar ${OUTPUT} .gradle
