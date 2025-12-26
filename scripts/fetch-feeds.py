#!/usr/bin/env python3
"""
RSS Feed Aggregator for Quagg Studios
Fetches RSS feeds defined in feeds.json and outputs aggregated feed-data.json
"""

import json
import feedparser
from datetime import datetime
from pathlib import Path
import html
import re

def clean_html(raw_html):
    """Remove HTML tags and decode entities"""
    if not raw_html:
        return ""
    # Remove HTML tags
    clean = re.sub(r'<[^>]+>', '', raw_html)
    # Decode HTML entities
    clean = html.unescape(clean)
    # Normalize whitespace
    clean = ' '.join(clean.split())
    return clean

def truncate(text, length=200):
    """Truncate text to specified length with ellipsis"""
    if len(text) <= length:
        return text
    return text[:length].rsplit(' ', 1)[0] + '...'

def parse_date(entry):
    """Extract and normalize date from feed entry"""
    date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
    
    for field in date_fields:
        if hasattr(entry, field) and getattr(entry, field):
            try:
                dt = datetime(*getattr(entry, field)[:6])
                return dt.isoformat()
            except:
                pass
    
    # Try string parsing as fallback
    date_strings = ['published', 'updated', 'created']
    for field in date_strings:
        if hasattr(entry, field) and getattr(entry, field):
            try:
                # Common date formats
                for fmt in ['%a, %d %b %Y %H:%M:%S %z', '%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%d']:
                    try:
                        dt = datetime.strptime(getattr(entry, field)[:25], fmt)
                        return dt.isoformat()
                    except:
                        continue
            except:
                pass
    
    return datetime.now().isoformat()

def fetch_feeds(config_path='feeds.json'):
    """Fetch all feeds from config and aggregate posts"""
    
    # Load feed configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    all_posts = []
    authors = set()
    
    for feed_config in config['feeds']:
        name = feed_config['name']
        url = feed_config['url']
        
        print(f"Fetching: {name}")
        
        try:
            feed = feedparser.parse(url)
            
            if feed.bozo and not feed.entries:
                print(f"  Warning: Error parsing {name}: {feed.bozo_exception}")
                continue
            
            authors.add(name)
            
            for entry in feed.entries[:20]:  # Limit to 20 most recent per feed
                # Get summary/description
                summary = ''
                if hasattr(entry, 'summary'):
                    summary = clean_html(entry.summary)
                elif hasattr(entry, 'description'):
                    summary = clean_html(entry.description)
                elif hasattr(entry, 'content') and entry.content:
                    summary = clean_html(entry.content[0].get('value', ''))
                
                post = {
                    'title': entry.get('title', 'Untitled'),
                    'author': name,
                    'date': parse_date(entry),
                    'link': entry.get('link', ''),
                    'summary': truncate(summary, 250)
                }
                
                all_posts.append(post)
                
            print(f"  Found {len(feed.entries)} entries")
            
        except Exception as e:
            print(f"  Error fetching {name}: {e}")
    
    # Sort by date (newest first)
    all_posts.sort(key=lambda x: x['date'], reverse=True)
    
    # Build output
    output = {
        'lastUpdated': datetime.now().isoformat(),
        'authors': sorted(list(authors)),
        'posts': all_posts[:100]  # Keep top 100 posts
    }
    
    return output

def main():
    output = fetch_feeds()
    
    # Write output
    output_path = Path('feed-data.json')
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nGenerated {output_path} with {len(output['posts'])} posts from {len(output['authors'])} authors")

if __name__ == '__main__':
    main()
