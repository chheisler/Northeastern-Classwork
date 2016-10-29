package cs6240.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.io.NullWritable;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Counter;

import org.xml.sax.Attributes;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.DefaultHandler;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;

import java.net.URLDecoder;
import java.io.StringReader;
import java.io.IOException;
import java.util.LinkedList;
import java.util.List;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import cs6240.writable.Page;

// A mapper which takes in lines representing page names and HTML content,
// and emits the page name as a key and its parsed list of outlinks and
// initial rank as a value.
public class InputMapper extends Mapper<Object, Text, Text, Page> {
	private XMLReader reader;
	private static Pattern namePattern = Pattern.compile("^([^~]+)$");
	private static Pattern linkPattern = Pattern.compile("^\\..*/([^~]+)\\.html$");
	private NullWritable none = NullWritable.get();
	private Text pageName = new Text();
	private Page page = new Page();
	private List<String> linkNames = new LinkedList<>();
	
	public void setup(Context context) {
		try {
			SAXParserFactory factory = SAXParserFactory.newInstance();
			factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
			SAXParser parser = factory.newSAXParser();
			reader = parser.getXMLReader();
			reader.setContentHandler(new WikiParser(linkNames));
		} catch (Exception e) {
			return;
		}
	}
	
	@Override
	public void map(Object key, Text line, Context context)
	throws IOException, InterruptedException {
		// get the page name and content
		String[] parts = line.toString().split(":", 2);
		String name = parts[0];
		String html = parts[1];
		
		// check if valid page name
		Matcher matcher = namePattern.matcher(name);
		if (!matcher.find()) return;
		
		// parse the page and extract links
		linkNames.clear();
		try {
			reader.parse(new InputSource(new StringReader(html)));
		} catch (SAXException e) {
			return;
		}
		
		// write the parsed page with its links and an initial rank
		pageName.set(name);
		String[] linkArray = new String[linkNames.size()];
		linkNames.toArray(linkArray);
		page.set(1.0, linkArray);
		context.write(pageName, page);
		
		// update the total page count and count of dangling pages
		Counter counter = context.getCounter("pagerank", "pages");
		counter.increment(1);
		if (linkNames.size() == 0) {
			counter = context.getCounter("pagerank", "dangling");
			counter.increment(1);
		}
	}
	
	// An XML parser handler for parsing the raw HTML of pages.
	private static class WikiParser extends DefaultHandler {
		public List<String> linkNames;
		private int count = 0; // depth within the bodyContent node of the page
		
		public WikiParser(List<String> linkNames) {
			super();
			this.linkNames = linkNames;
		}
		
		@Override
		public void startElement(String uri, String localName, String qName, Attributes attributes) throws SAXException {
			super.startElement(uri, localName, qName, attributes);
			
			// If inside bodyContent, check if element is valid link and add it if it is
			if (count > 0) {
				count++;
				if (qName.equalsIgnoreCase("a")) {
					String link = attributes.getValue("href");
					if (link == null) return;
					try {
						link = URLDecoder.decode(link, "UTF-8"); 
					} catch (Exception e) {
						// pass
					}
					Matcher matcher = linkPattern.matcher(link);
					if (matcher.find()) linkNames.add(matcher.group(1));
				}
			}
			
			// Else check if this is the start of the bodyContent
			else if (qName.equalsIgnoreCase("div")) {
				String id = attributes.getValue("id");
				if (id != null && id.equalsIgnoreCase("bodyContent")) count = 1;
			}
		}
		
		@Override
		public void endElement(String uri, String localName, String qName) throws SAXException {
			super.endElement(uri, localName, qName);
			if (count > 0) count--;
		}
	}
}

