import averager.*;
import util.Data;
import util.Accumulator;
import java.io.IOException;
import java.util.HashMap;

public class NOAA {
    public static void main(String[] args) throws IOException {
        System.out.println("Loading data...");
        Data data = new Data();
        data.load(args[0]);
        
        System.out.println("Running sequential program...");
        new SequentialAverager(data).trial();
        
        System.out.println("Running threaded program without lock...");
        new NoLockAverager(data).trial();
        
        System.out.println("Running threaded program with coarse lock...");
        new CoarseLockAverager(data).trial();
        
        System.out.println("Running threaded program with fine lock...");
        new FineLockAverager(data).trial();
        
        System.out.println("Running threaded program without sharing...");
        new NoShareAverager(data).trial();
        
        System.out.println("Finished. Results written to output/.");
    }
}