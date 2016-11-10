package cs6240.parser

import org.xml.sax.Attributes
import org.xml.sax.InputSource
import org.xml.sax.SAXException
import org.xml.sax.XMLReader
import org.xml.sax.helpers.DefaultHandler

import javax.xml.parsers.SAXParser
import javax.xml.parsers.SAXParserFactory

import java.net.URLDecoder
import java.io.StringReader
import java.io.IOException
import java.util.LinkedList
import java.util.List
import java.util.regex.Matcher
import java.util.regex.Pattern

object WikiParser {
	private val namePattern = Pattern.compile("^([^~]+)$")
	private val linkPattern = Pattern.compile("^\\..*/([^~]+)\\.html$")
}

// a parser which finds the links in the HTML of an input line
// returns the page's name and links as a tuple
class WikiParser(lines: Iterator[String]) {
	private val linkNames: List[String] = new LinkedList[String]()
	val factory = SAXParserFactory.newInstance()
	factory.setFeature("http://apache.org/xml/features/nonvalidating/load-external-dtd", false)
	val parser = factory.newSAXParser()
	private var reader = parser.getXMLReader()
	reader.setContentHandler(new WikiHandler(linkNames))
	
	// iterator for valid parsed pages
	def iterator = new Iterator[(String, Array[String])] {
		var parsed: (String, Array[String]) = null

		def hasNext = {
			if (parsed == null && lines.hasNext) findNext()
			parsed != null
		}

		def next = {
			if (parsed == null) findNext()
			val elem = parsed
			parsed = null
			elem
		}

		def findNext() = {
			while (parsed == null && lines.hasNext) parsed = parse(lines.next)
		}
	}

	// parse a single input record
	def parse(line: String): (String, Array[String]) = {
		// get the page name and content
		val parts = line.split(":", 2)
		val name = parts(0)
		val html = parts(1)
		
		// check if valid page name
		val matcher = WikiParser.namePattern.matcher(name)
		if (!matcher.find()) return null
		
		// parse the page and extract links
		linkNames.clear()
		try {
			reader.parse(new InputSource(new StringReader(html)))
			val links = new Array[String](linkNames.size())
			linkNames.toArray(links)
			return (name, links)
		} catch {
			case e: SAXException => return null
		}
	}
	
	// An XML parser handler for parsing the raw HTML of pages.
	class WikiHandler(linkNames: List[String]) extends DefaultHandler {
		private var count: Long = 0 // depth within the bodyContent node of the page
		
		override def startElement(uri: String, localName: String, qName: String, attributes: Attributes) {
			super.startElement(uri, localName, qName, attributes)
			
			//if inside bodyContent, check if element is valid link and add if so
			if (count > 0) {
				count += 1
				if (qName.equalsIgnoreCase("a")) {
					var link = attributes.getValue("href")
					if (link == null) return
					try {
						link = URLDecoder.decode(link, "UTF-8")
					} catch {
						case e: Exception =>
					}
					val matcher = WikiParser.linkPattern.matcher(link)
					if (matcher.find()) linkNames.add(matcher.group(1))
				}
			}
			
			// else check if start of bodyContent
			else if (qName.equalsIgnoreCase("div")) {
				val id = attributes.getValue("id")
				if (id != null && id.equalsIgnoreCase("bodyContent")) count = 1
			}
		}
		
		override def endElement(uri: String, localName: String, qName: String) {
			super.endElement(uri, localName, qName)
			if (count > 0) count -= 1
		}
	}
}

