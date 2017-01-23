INPUT = input
OUTPUT = output
NUM_REDUCERS = 2
ABSOLUTE = true

RowPartition.jar: *.java mapper/*.java reducer/*.java writable/*.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/RowPartition-all.jar RowPartition.jar

run: RowPartition.jar
	rm -rf iter* ${OUTPUT}
	hadoop jar RowPartition.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS} ${ABSOLUTE}

clean:
	rm -rf build RowPartition.jar ${OUTPUT} .gradle
