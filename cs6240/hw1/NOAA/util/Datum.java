package util;

// class representing data entry for station
public class Datum {
    private String station;
    private String type;
    private int value;

    public Datum(String station, String type, String value) {
        this.station = station;
        this.type = type;
        this.value = Integer.parseInt(value);
    }

    public String getStation() { return station; }
    public String getType() { return type; }
    public int getValue() { return value; }
}