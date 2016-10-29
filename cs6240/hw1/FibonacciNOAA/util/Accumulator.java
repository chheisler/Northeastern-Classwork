package util;

// data structure for accumulating TMAX and number of entries for weather station
public class Accumulator {
    private int total;
    private int count;
    
    public int getTotal() { return total; }
    public int getCount() { return count; }
    
    public Accumulator() {
    	total = 0;
    	count = 0;
    }
    
    public Accumulator(int value) {
    	fibonacci(17);
        total = value;
        count = 1;
    }

	public Accumulator(Accumulator accumulator) {
		total = accumulator.getTotal();
		count = accumulator.getCount();
	}
    
    // add a new value to the accumulator
    public void add(int value) {
    	fibonacci(17);
        total += value;
        count++;
    }
    
    // add another accumulator to this one
    public void add(Accumulator accumulator) {
    	total += accumulator.getTotal();
    	count += accumulator.getCount();
    }
    
    // compute the average of accumulated values
    public float average() {
        return (float) total / count;
    }
    
    private int fibonacci(int x) {
    	if (x <= 1) return x;
    	else return fibonacci(x - 1) + fibonacci(x - 2);
    }
}