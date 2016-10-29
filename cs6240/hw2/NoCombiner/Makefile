INPUT = 1991.csv
OUTPUT = output
NUM_REDUCERS = 5

NoCombiner.jar: *.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/NoCombiner-all.jar NoCombiner.jar

run: NoCombiner.jar
	rm -rf ${OUTPUT}
	hadoop jar NoCombiner.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS}

clean:
	rm -rf build NoCombiner.jar ${OUTPUT} .gradle
