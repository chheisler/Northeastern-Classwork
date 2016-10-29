package averager;

import util.Accumulator;
import util.Datum;
import util.Data;
import util.DataIterator;
import averager.Averager;
import java.util.HashMap;
import java.util.ArrayList;
import java.util.Map;

// an averager which uses a shared accumulator data structure controlled by a
// single lock for the entire structure
public class CoarseLockAverager extends Averager {
	public CoarseLockAverager(Data data) { super(data); }
    
    // common accumulator for worker threads
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
    // the directory in which to output the results
 	public String outputDir() { return "coarse_lock"; }
     
    // a worker which shares a common accumulator data structure with other
    // workers and locks the entire structure to update it
    class Worker extends Thread {
    	// an iterator for this thread's portion of the data
        private DataIterator iter;
        
        public Worker(int from, int to) { iter = data.iterator(from, to); }
        
        // iterate through the data and lock and update the common accumulator
        // data structure for each entry
        @Override
        public void run() {
            while (iter.hasNext()) {
                Datum datum = iter.next();
                if (!datum.getType().equals("TMAX")) continue;
                String station = datum.getStation();
                int value = datum.getValue();
                synchronized (accumulators) {
                    Accumulator accumulator = accumulators.get(station);            
                    if (accumulator == null) accumulators.put(station, new Accumulator(value));
                    else accumulator.add(value);
                }
            }
        }
    }
}