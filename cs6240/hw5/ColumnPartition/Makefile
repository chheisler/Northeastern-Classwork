INPUT = input
OUTPUT = output
NUM_REDUCERS = 2

RowPartition.jar: *.java mapper/*.java reducer/*.java writable/*.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/ColumnPartition-all.jar ColumnPartition.jar

run: RowPartition.jar
	rm -rf iter* ${OUTPUT}
	hadoop jar ColumnPartition.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS}

clean:
	rm -rf build ColumnPartition.jar ${OUTPUT} .gradle
