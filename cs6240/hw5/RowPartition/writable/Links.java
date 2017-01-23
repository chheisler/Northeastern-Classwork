package pagerank.writable;

import org.apache.hadoop.io.Writable;

import java.io.DataInput;
import java.io.DataOutput;
import java.io.IOException;
import java.util.Set;

// A writable representing a list of page links stored as strings.
public class Links implements Writable {
	private String[] links;
	
	public Links() {
		links = new String[0];
	}
	
	public Links(String[] links) {
		if (links == null) this.links = new String[0];
		else this.links = links;
	}
	
	public void set(Set links) {
		if (links == null) this.links = new String[0];
		else {
			this.links = new String[links.size()];
			links.toArray(this.links);
		}
	}
	
	public String[] get() {
		return links;
	}
	
	@Override
	public void write(DataOutput out) throws IOException {
		out.writeInt(links.length);
		for (String link : links) out.writeUTF(link);
	}
	
	@Override
	public void readFields(DataInput in) throws IOException {
		int length = in.readInt();
		links = new String[length];
		for (int i = 0; i < length; i++) links[i] = in.readUTF();
	}
	
	@Override
	public String toString() {
		if (links == null) return "null";
		else return "[" + String.join(",", links) + "]";
	}
}

