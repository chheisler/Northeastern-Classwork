package pagerank.mapper;

import org.apache.hadoop.io.Text;
import org.apache.hadoop.mapreduce.Mapper;
import org.apache.hadoop.mapreduce.Counter;

import org.xml.sax.Attributes;
import org.xml.sax.InputSource;
import org.xml.sax.SAXException;
import org.xml.sax.XMLReader;
import org.xml.sax.helpers.DefaultHandler;

import javax.xml.parsers.SAXParser;
import javax.xml.parsers.SAXParserFactory;
import javax.xml.parsers.ParserConfigurationException;

import java.net.URLDecoder;
import java.io.StringReader;
import java.io.IOException;
import java.util.Set;
import java.util.HashSet;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

import pagerank.writable.Links;


// The mapper for the parse job. The Input is one line of the input file as
// text. If the page's name is valid, its contents are parsed and a list of
// valid links is extracted. The page's name is written as the key and the
// page's links are written as the value. For each parsed link, the link's
// name is also written with a dummy empty list of links so that any linked
// pages not in the data set become dangling pages.
public class ParseMapper extends Mapper<Object, Text, Text, Links> {

	// patterns for matching in parser
	private static Pattern namePattern = Pattern.compile("^([^~]+)$");
	private static Pattern linkPattern = Pattern.compile("^\\..*/([^~]+)\\.html$");
	
	// reader for parsing XML
	private XMLReader reader;
		
	// output writables
	private Text nameWritable = new Text();
	private Links linksWritable = new Links();
	private Links empty = new Links();
	
	// set of unique parsed links
	private Set<String> links = new HashSet<>();
	
	public void setup(Context context) {
		try {
			SAXParserFactory factory = SAXParserFactory.newInstance();
			factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false);
			SAXParser parser = factory.newSAXParser();
			reader = parser.getXMLReader();
			reader.setContentHandler(new WikiParser(links));
		} catch (SAXException e) {
			return;
		} catch (ParserConfigurationException e) {
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
		links.clear();
		try {
			reader.parse(new InputSource(new StringReader(html)));
		} catch (SAXException e) {
			return;
		}
		
		// write parsed links for page
		nameWritable.set(name);
		linksWritable.set(links);
		context.write(nameWritable, linksWritable);
		
		// write links as pages to handle missing data
		for (String link : links) {
			nameWritable.set(link);
			context.write(nameWritable, empty);
		}
	}
	
	// An XML parser handler for parsing the raw HTML of pages.
	private static class WikiParser extends DefaultHandler {
		private Set<String> links;
		private int count = 0; // depth within the bodyContent node of the page
		
		public WikiParser(Set<String> links) {
			super();
			this.links = links;
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
					if (matcher.find()) links.add(matcher.group(1));
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

