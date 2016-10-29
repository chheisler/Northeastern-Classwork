package averager;

import util.Accumulator;
import util.Datum;
import util.Data;
import util.DataIterator;
import averager.Averager;
import java.util.ArrayList;
import java.util.concurrent.ConcurrentHashMap;
import java.util.Map;

// an averager which uses a common concurrent accumulator map and whose
// threads lock individual accumulators within the map
public class FineLockAverager extends Averager {
	public FineLockAverager(Data data) { super(data); }
    
    // common accumulator map for worker threads
    private ConcurrentHashMap<String, Accumulator> accumulators;
    
    public Map<String, Accumulator> average() {
        accumulators = new ConcurrentHashMap<>();
        
        // create the workers
        ArrayList<Worker> workers = new ArrayList<>();
        int range = data.size() / THREADS;
        range += data.size() % THREADS == 0 ? 0 : 1;
        for (int j = 0; j < THREADS; j++) {
            int from = j * range;
            int to = Math.min(from + range, data.size());
            workers.add(new Worker(from, to));
        }
        
        // run the workers and wait for them to complete
        for (Worker worker : workers) worker.start();
        try {
            for (Worker worker : workers) worker.join();
        } catch (InterruptedException e) {
            return accumulators;
        }
        return accumulators;
    }
    
    // directory in which to output the results
 	public String outputDir() { return "fine_lock"; }
     
    // a worker which iterates over a portion of the data and updates the
    // shared accumulator map by locking individual accumulators
    class Worker extends Thread {
    	// iterator for the worker's portion of the data
        private DataIterator iter;
        
        public Worker(int from, int to) { iter = data.iterator(from, to); }
        
        // iterate through the data and update the accumulator map by locking
        // only the accumulator being updated
        @Override
        public void run() {
            while (iter.hasNext()) {
                Datum datum = iter.next();
                if (!datum.getType().equals("TMAX")) continue;
                String station = datum.getStation();
                int value = datum.getValue();
                Accumulator accumulator = accumulators.get(station);            
                if (accumulator == null) {
                	accumulators.putIfAbsent(station, new Accumulator());
                	accumulator = accumulators.get(station);
                }
                synchronized (accumulator) { accumulator.add(value); }
            }
        }
    }
}