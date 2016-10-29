INPUT = 1991.csv
OUTPUT = output
NUM_REDUCERS = 5

Combiner.jar: *.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/Combiner-all.jar Combiner.jar

run: Combiner.jar
	rm -rf ${OUTPUT}
	hadoop jar Combiner.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS}

clean:
	rm -rf build Combiner.jar ${OUTPUT} .gradle
