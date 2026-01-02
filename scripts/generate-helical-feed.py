#!/usr/bin/env python3
"""
RSS Feed Generator for The Helical Expeditions

Reads helical-feed-data.json and generates an RSS 2.0 feed (feed.xml).
Run this script whenever you add or update adventures.

Usage:
    python generate-helical-feed.py
"""

import json
import xml.etree.ElementTree as ET
from xml.dom import minidom
from datetime import datetime
from pathlib import Path

# Base URL for the site
BASE_URL = "http://its.quagg.studio/the-helical-expeditions"

def load_adventures(json_path: Path) -> dict:
    """Load the adventures manifest."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def format_rfc822_date(date_str: str) -> str:
    """Convert YYYY-MM-DD to RFC 822 format for RSS."""
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    # RSS requires RFC 822 format
    return dt.strftime("%a, %d %b %Y 00:00:00 +0000")

def generate_rss(data: dict) -> str:
    """Generate RSS 2.0 XML from adventure data."""
    feed_info = data["feed"]
    adventures = data["adventures"]
    
    # Sort adventures by publish date (newest first)
    adventures_sorted = sorted(
        adventures, 
        key=lambda x: x["publishDate"], 
        reverse=True
    )
    
    # Create RSS root
    rss = ET.Element("rss", version="2.0")
    rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")
    
    channel = ET.SubElement(rss, "channel")
    
    # Channel metadata
    ET.SubElement(channel, "title").text = feed_info["title"]
    ET.SubElement(channel, "description").text = feed_info["description"]
    ET.SubElement(channel, "link").text = feed_info["link"]
    ET.SubElement(channel, "language").text = "en-us"
    ET.SubElement(channel, "lastBuildDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    
    # Atom self-link (recommended for RSS 2.0)
    atom_link = ET.SubElement(channel, "atom:link")
    atom_link.set("href", f"{BASE_URL}/feed.xml")
    atom_link.set("rel", "self")
    atom_link.set("type", "application/rss+xml")
    
    # Add each adventure as an item
    for adventure in adventures_sorted:
        item = ET.SubElement(channel, "item")
        
        title = f"{adventure['title']} [Rank {adventure['rank']}]"
        ET.SubElement(item, "title").text = title
        
        link = f"{BASE_URL}/{adventure['file']}"
        ET.SubElement(item, "link").text = link
        
        # Build description with location info
        description = f"""<p><strong>{adventure['region']}</strong> — {adventure['sublocation']}</p>
<p><em>Location:</em> {adventure['location']}</p>
<p>{adventure['description']}</p>"""
        ET.SubElement(item, "description").text = description
        
        ET.SubElement(item, "pubDate").text = format_rfc822_date(adventure["publishDate"])
        
        # GUID (use permalink)
        guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "true")
        guid.text = link
        
        # Categories for filtering
        ET.SubElement(item, "category").text = adventure["region"]
        ET.SubElement(item, "category").text = adventure["sublocation"]
        ET.SubElement(item, "category").text = f"Rank {adventure['rank']}"
    
    # Pretty print the XML
    xml_str = ET.tostring(rss, encoding='unicode')
    dom = minidom.parseString(xml_str)
    pretty_xml = dom.toprettyxml(indent="  ", encoding=None)
    
    # Remove the extra XML declaration minidom adds and clean up
    lines = pretty_xml.split('\n')
    # Skip the first line (xml declaration) and rejoin
    clean_xml = '<?xml version="1.0" encoding="UTF-8"?>\n' + '\n'.join(lines[1:])
    
    return clean_xml

def main():
    # Paths relative to repo root (script is in scripts/)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    
    json_path = repo_root / "the-helical-expeditions" / "helical-feed-data.json"
    output_path = repo_root / "the-helical-expeditions" / "feed.xml"
    
    print(f"Loading adventures from {json_path}...")
    data = load_adventures(json_path)
    
    print(f"Found {len(data['adventures'])} adventures")
    
    print("Generating RSS feed...")
    rss_content = generate_rss(data)
    
    print(f"Writing feed to {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(rss_content)
    
    print("✓ RSS feed generated successfully!")
    print(f"\nFeed URL: {BASE_URL}/feed.xml")

if __name__ == "__main__":
    main()
