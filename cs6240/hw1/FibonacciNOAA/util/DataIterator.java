package util;

import util.Datum;
import java.util.Iterator;
import java.util.List;

// an iterator which produces datum objects from a list of strings
public class DataIterator implements Iterator<Datum> {
    private static final int STATION_INDEX = 0;
    private static final int TYPE_INDEX = 2;
    private static final int VALUE_INDEX = 3;

    private Iterator<String> iterator;

    public DataIterator(List<String> data) {
        iterator = data.iterator();
    }

    public boolean hasNext() { return iterator.hasNext(); }

    // get the next line and create a datum object from it
    public Datum next() {
        String line = iterator.next();
        String[] parts = line.split(",");
        String station = parts[STATION_INDEX];
        String type = parts[TYPE_INDEX];
        String value = parts[VALUE_INDEX];
        return new Datum(station, type, value);
    }

    public void remove() { iterator.remove(); }
}