MAIN=NOAA

${MAIN}.jar: ${MAIN}.java averager/*.java util/*.java build.gradle Makefile
	gradle build
	gradle shadowJar
	cp build/libs/${MAIN}-all.jar ${MAIN}.jar

run: ${MAIN}.jar
	java -jar ${MAIN}.jar 1912.csv.gz

clean:
	rm -rf build ${MAIN}.jar .gradle output

