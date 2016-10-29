package averager;

import util.Data;
import util.Accumulator;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.io.PrintWriter;
import java.io.FileNotFoundException;
import java.io.UnsupportedEncodingException;
import java.io.File;
 	
public abstract class Averager {
	// the data to be averaged
    protected Data data;
    
    public Averager(Data data) { this.data = data; }
    
    public static final int TRIALS = 10;
    public static final int THREADS = 4;
    
    public void trial() {
        long min = Long.MAX_VALUE; 
        long max = 0;
        float average = 0;
        Map<String, Accumulator> accumulators = new HashMap<>();
        
        // run the trials
        for (int i = 0; i < TRIALS; i++) {
            long start = System.currentTimeMillis();
            accumulators = average();
            long end = System.currentTimeMillis();
            long time = end - start;
            min = Math.min(min, time);
            max = Math.max(max, time);
            average += (float) time / TRIALS;
            
            // print out the results
            try {
                String filename = "output/" + outputDir() + "/trial" + (i + 1) + ".txt";
                File file = new File(filename);
                file.getParentFile().mkdirs();
            	PrintWriter writer = new PrintWriter(file);
            	writer.println("time\t" + time + "ms");
            	for (Map.Entry<String, Accumulator> entry : accumulators.entrySet()) {
            		String station = entry.getKey();
            		Accumulator accumulator = entry.getValue();
            		writer.println(station + "\t" + accumulator.average());
            	}
            	writer.close();
            } catch (FileNotFoundException e) {
            	continue;
            }
        }        

        // output the final results of all trials
        try {
        	File file = new File("output/" + outputDir() + "/final.txt");
        	file.getParentFile().mkdirs();
        	PrintWriter writer = new PrintWriter(file);
	        writer.println("min\t" + min + "ms");
	        writer.println("max\t" + max + "ms");
	        writer.println("average\t " + average + "ms");
	        writer.close();
        } catch (FileNotFoundException e) {
        	return;
        }
    }
    
    public abstract Map<String, Accumulator> average();
    
    // directory in which to put results
    public abstract String outputDir();
}