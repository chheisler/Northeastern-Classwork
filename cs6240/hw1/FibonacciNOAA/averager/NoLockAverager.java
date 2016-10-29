package averager;

import averager.Averager;
import util.Data;
import util.DataIterator;
import util.Datum;
import util.Accumulator;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Map;

// an averager which uses a single accumulator map for all threads and which
// does not lock the map when it is updated
public class NoLockAverager extends Averager {
    public NoLockAverager(Data data) { super(data); }
    
    // common accumulator map for worker threads
    private HashMap<String, Accumulator> accumulators;
    
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
        return accumulators;
    }
    
    // directory in which to output the results;
    public String outputDir() { return "no_lock"; }
 	
    // A worker thread which iterates over portion of data and updates a common
    // map of accumulators without taking out a lock
    class Worker extends Thread {
    	// an iterator for the thread's portion of the data
        private DataIterator iter;
        
        public Worker(int from, int to) { iter = data.iterator(from, to); }
        
        // iterate through the data and update the common accumulator map
        // without taking out locks
        @Override
        public void run() {
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