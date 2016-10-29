INPUT = wikipedia-simple-html.bz2
OUTPUT = output
NUM_REDUCERS = 2

PageRank.jar: *.java mapper/*.java reducer/*.java writable/*.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/PageRank-all.jar PageRank.jar

run: PageRank.jar
	rm -rf iter* ${OUTPUT}
	hadoop jar PageRank.jar ${INPUT} ${OUTPUT} ${NUM_REDUCERS}

clean:
	rm -rf build iter* PageRank.jar ${OUTPUT} .gradle
