package averager;

import util.Accumulator;
import util.Datum;
import util.Data;
import util.DataIterator;
import averager.Averager;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

// a temperature average whose workers each have an unshared accumulator
public class NoShareAverager extends Averager {
	public NoShareAverager(Data data) { super(data); }
    
    // the final accumulator for combining the worker results
    private HashMap<String, Accumulator> accumulators;
    
    // find the average TMAX reading for each station
    public Map<String, Accumulator> average() {
        accumulators = new HashMap<>();
        
        // create the worker threads
        ArrayList<Worker> workers = new ArrayList<>();
        int range = data.size() / THREADS;
        range += data.size() % THREADS == 0 ? 0 : 1;
        for (int j = 0; j < THREADS; j++) {
            int from = j * range;
            int to = Math.min(from + range, data.size());
            workers.add(new Worker(from, to));
        }
        
        // run the worker threads and wait for them to complete
        for (Worker worker : workers) worker.start();
        try {
            for (Worker worker : workers) worker.join();
        } catch (InterruptedException e) {
            return accumulators;
        }
        
        // combine the thread outputs and return them
        for (Worker worker : workers) {
        	HashMap<String, Accumulator> worker_accumulators = worker.getAccumulators();
        	for (HashMap.Entry<String, Accumulator> entry: worker_accumulators.entrySet()) {
        		String station = entry.getKey();
        		Accumulator accumulator = accumulators.get(station);
        		if (accumulator == null) {
        			accumulator = new Accumulator(entry.getValue());
        			accumulators.put(station, accumulator);
        		}
        		else accumulator.add(entry.getValue());
        	}
        }
        return accumulators;
    }
    
    // the directory in which to output the results
 	public String outputDir() { return "no_share"; }
     
    // a worker which iterates over a portion of the data and accumulates the
    // results in an unshared data structure
    class Worker extends Thread {
    	// an iterator for the thread's portion of the data
        private DataIterator iter;
        
        // a unshared accumulator for the thread
        private HashMap<String, Accumulator> accumulators;
        
        public Worker(int from, int to) { iter = data.iterator(from, to); }
        
        public HashMap<String, Accumulator> getAccumulators() { return accumulators; }
        
        // iterate through the data and update the accumulator for each entry
        @Override
        public void run() {
        	accumulators = new HashMap<>();
            while (iter.hasNext()) {
                Datum datum = iter.next();
                if (!datum.getType().equals("TMAX")) continue;
                String station = datum.getStation();
                int value = datum.getValue();
                Accumulator accumulator = accumulators.get(station);            
                if (accumulator == null) accumulators.put(station, new Accumulator(value));
                else accumulator.add(value);
            }
        }
    }
}