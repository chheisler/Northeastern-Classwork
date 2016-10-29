package util;

import java.io.InputStream;
import java.io.FileInputStream;
import java.io.InputStreamReader;
import java.io.BufferedReader;
import java.io.IOException;
import java.io.FileNotFoundException;
import java.util.zip.GZIPInputStream;
import java.util.List;
import java.util.ArrayList;
import util.Datum;
import util.DataIterator;

// A wrapper around the raw data files
public class Data implements Iterable<Datum> {
    // data as raw lines of text
    List<String> lines;

    public Data() {};

    // loads data from zipped CSV file into data
    public void load(String filename) throws IOException {
        InputStream stream = new GZIPInputStream(new FileInputStream(filename));
        BufferedReader reader = new BufferedReader(new InputStreamReader(stream));
        lines = new ArrayList<>();
        String line = reader.readLine();
        while (line != null) {
            lines.add(line);
            line = reader.readLine();
        }
    }

    // return iterator over portion of data
    public DataIterator iterator(int from, int to) {
        return new DataIterator(lines.subList(from, to));
    }

    // return iterator over all data
    public DataIterator iterator() {
        return iterator(0, lines.size());
    }

    // return number of entries in data
    public int size() {
        return lines.size();
    }
}