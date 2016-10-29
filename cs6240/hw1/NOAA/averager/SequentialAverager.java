package averager;

import java.util.HashMap;
import util.Datum;
import util.Data;
import util.Accumulator;
import averager.Averager;
import java.util.Map;

// an averager which runs in a single sequential thread
public class SequentialAverager extends Averager {
	
    public SequentialAverager(Data data) { super(data); }
    
    // iterate through all data and calculate average TMAX for each station
    public Map<String, Accumulator> average() {
        HashMap<String, Accumulator> accumulators = new HashMap<>();
        for (Datum datum : data) {
            if (!datum.getType().equals("TMAX")) continue;
            String station = datum.getStation();
            int value = datum.getValue();
            Accumulator accumulator = accumulators.get(station);            
            if (accumulator == null) accumulators.put(station, new Accumulator(value));
            else accumulator.add(value);
        }
        return accumulators;
    }

	// the directory in which to output the results
    public String outputDir() { return "sequential"; }
}