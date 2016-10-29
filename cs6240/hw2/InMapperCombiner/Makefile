INPUT = 1991.csv
OUTPUT = output
NUM_REDUCERS = 5

InMapperCombiner.jar: *.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/InMapperCombiner-all.jar InMapperCombiner.jar

run: InMapperCombiner.jar
	rm -rf ${OUTPUT}
	hadoop jar InMapperCombiner.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS}

clean:
	rm -rf build InMapperCombiner.jar ${OUTPUT} .gradle
