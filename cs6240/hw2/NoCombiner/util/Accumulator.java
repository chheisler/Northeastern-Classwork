package cs6240.util;

// a data structure which accumulates the total and count of a value
public class Accumulator {
	private int total = 0;
	private int count = 0;

	public int getTotal() { return total; }
	public int getCount() { return count; }

	public void add(int value) {
		total += value;
		count++;
	}

	public float average() {
		return (float) total / count;
	}
}
