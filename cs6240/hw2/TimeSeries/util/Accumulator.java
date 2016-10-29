package cs6240.util;

// a data structure which accumulates the total and counts for TMIN and TMAX
// measurements from a station
public class Accumulator {
	private int minTempTotal = 0;
	private int minTempCount = 0;
	private int maxTempTotal = 0;
	private int maxTempCount = 0;
	
	public void addMinTemp(int value) {
		minTempTotal += value;
		minTempCount++;
	}
	
	public void addMaxTemp(int value) {
		maxTempTotal += value;
		maxTempCount++;
	}

	public float averageMinTemp() {
		return (float) minTempTotal / minTempCount;
	}
	
	public float averageMaxTemp() {
		return (float) maxTempTotal / maxTempCount;
	}
}
