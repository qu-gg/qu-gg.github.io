#!/usr/bin/env python3
"""
Art Inspiration Feed Aggregator for Quagg Studios
Fetches posts from Bluesky (AT Protocol) and ArtStation (RSS)
"""

import json
import urllib.request
import urllib.error
import xml.etree.ElementTree as ET
import re
import html
from datetime import datetime
from pathlib import Path

BLUESKY_API = "https://public.api.bsky.app/xrpc"

# ============== HTTP Helpers ==============

def fetch_url(url, accept='application/json'):
    """Fetch content from URL"""
    req = urllib.request.Request(url, headers={
        'User-Agent': 'QuaggStudios-ArtFeed/1.0',
        'Accept': accept
    })
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode('utf-8')

def fetch_json(url):
    """Fetch JSON from URL"""
    return json.loads(fetch_url(url, 'application/json'))

# ============== Bluesky Functions ==============

def fetch_bluesky_profile(handle):
    """Fetch Bluesky user profile"""
    url = f"{BLUESKY_API}/app.bsky.actor.getProfile?actor={handle}"
    try:
        profile = fetch_json(url)
        return {
            'handle': profile.get('handle'),
            'displayName': profile.get('displayName'),
            'avatar': profile.get('avatar'),
            'source': 'bluesky'
        }
    except Exception as e:
        print(f"    Error fetching profile: {e}")
        return {'handle': handle, 'displayName': None, 'avatar': None, 'source': 'bluesky'}

def fetch_bluesky_feed(handle, limit=50, filter_replies=True):
    """Fetch Bluesky user's feed"""
    filter_param = "posts_no_replies" if filter_replies else "posts_and_author_threads"
    url = f"{BLUESKY_API}/app.bsky.feed.getAuthorFeed?actor={handle}&limit={limit}&filter={filter_param}"
    try:
        data = fetch_json(url)
        return data.get('feed', [])
    except Exception as e:
        print(f"    Error fetching feed: {e}")
        return []

def process_bluesky_post(item):
    """Process a single Bluesky post"""
    post = item.get('post', {})
    author = post.get('author', {})
    record = post.get('record', {})
    
    # Check if this is a repost
    reason = item.get('reason')
    repost_info = None
    if reason and reason.get('$type') == 'app.bsky.feed.defs#reasonRepost':
        repost_by = reason.get('by', {})
        repost_info = {
            'handle': repost_by.get('handle'),
            'displayName': repost_by.get('displayName'),
            'avatar': repost_by.get('avatar')
        }
    
    # Process embed
    embed = post.get('embed')
    embed_data = None
    if embed:
        embed_data = process_bluesky_embed(embed)
    
    return {
        'uri': post.get('uri'),
        'source': 'bluesky',
        'author': {
            'handle': author.get('handle'),
            'displayName': author.get('displayName'),
            'avatar': author.get('avatar')
        },
        'record': {
            'text': record.get('text', ''),
            'createdAt': record.get('createdAt')
        },
        'indexedAt': post.get('indexedAt'),
        'replyCount': post.get('replyCount', 0),
        'repostCount': post.get('repostCount', 0),
        'likeCount': post.get('likeCount', 0),
        'embed': embed_data,
        'repostBy': repost_info
    }

def process_bluesky_embed(embed):
    """Process Bluesky embedded content"""
    embed_type = embed.get('$type')
    
    if embed_type == 'app.bsky.embed.images#view':
        return {
            'type': 'images',
            'images': [{
                'thumb': img.get('thumb'),
                'fullsize': img.get('fullsize'),
                'alt': img.get('alt', '')
            } for img in embed.get('images', [])]
        }
    
    if embed_type == 'app.bsky.embed.external#view':
        ext = embed.get('external', {})
        return {
            'type': 'external',
            'uri': ext.get('uri'),
            'title': ext.get('title'),
            'description': ext.get('description'),
            'thumb': ext.get('thumb')
        }
    
    if embed_type == 'app.bsky.embed.record#view':
        record = embed.get('record', {})
        if record.get('$type') == 'app.bsky.embed.record#viewRecord':
            author = record.get('author', {})
            value = record.get('value', {})
            return {
                'type': 'quote',
                'author': {
                    'handle': author.get('handle'),
                    'displayName': author.get('displayName'),
                    'avatar': author.get('avatar')
                },
                'text': value.get('text', '')
            }
    
    if embed_type == 'app.bsky.embed.recordWithMedia#view':
        result = {'type': 'recordWithMedia'}
        if embed.get('media'):
            result['media'] = process_bluesky_embed(embed['media'])
        if embed.get('record'):
            result['record'] = process_bluesky_embed(embed['record'])
        return result
    
    return None

# ============== ArtStation Functions ==============

def fetch_artstation_feed(username):
    """Fetch ArtStation RSS feed"""
    url = f"https://www.artstation.com/{username}.rss"
    try:
        xml_content = fetch_url(url, 'application/rss+xml')
        return parse_artstation_rss(xml_content, username)
    except Exception as e:
        print(f"    Error fetching ArtStation feed: {e}")
        return [], None

def parse_artstation_rss(xml_content, username):
    """Parse ArtStation RSS feed"""
    root = ET.fromstring(xml_content)
    channel = root.find('channel')
    
    # Extract profile info from channel
    profile = {
        'handle': username,
        'displayName': channel.findtext('title', '').replace(' on ArtStation', ''),
        'avatar': None,  # RSS doesn't include avatar
        'source': 'artstation'
    }
    
    posts = []
    for item in channel.findall('item'):
        post = process_artstation_item(item, username, profile)
        if post:
            posts.append(post)
    
    return posts, profile

def process_artstation_item(item, username, profile):
    """Process a single ArtStation RSS item"""
    title = item.findtext('title', '')
    link = item.findtext('link', '')
    guid = item.findtext('guid', '')
    pub_date = item.findtext('pubDate', '')
    description = item.findtext('description', '')
    
    # Get content:encoded for images
    content_encoded = item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded', '')
    
    # Extract images from content
    images = extract_artstation_images(content_encoded)
    
    if not images:
        return None  # Skip posts without images
    
    # Parse date
    indexed_at = None
    if pub_date:
        try:
            # Parse RSS date format: "Mon, 24 Nov 2025 10:14:00 -0600"
            from email.utils import parsedate_to_datetime
            dt = parsedate_to_datetime(pub_date)
            indexed_at = dt.isoformat()
        except:
            indexed_at = pub_date
    
    # Clean up description (remove CDATA, HTML)
    clean_desc = html.unescape(description)
    clean_desc = re.sub(r'<[^>]+>', '', clean_desc).strip()
    
    # Extract artist name from title (format: "Title by Artist Name")
    display_name = profile['displayName']
    if ' by ' in title:
        title = title.rsplit(' by ', 1)[0]
    
    return {
        'uri': guid or link,
        'source': 'artstation',
        'author': {
            'handle': username,
            'displayName': display_name,
            'avatar': None
        },
        'record': {
            'text': f"{title}\n\n{clean_desc}" if clean_desc else title,
            'createdAt': indexed_at
        },
        'indexedAt': indexed_at,
        'replyCount': 0,
        'repostCount': 0,
        'likeCount': 0,
        'embed': {
            'type': 'images',
            'images': images
        },
        'repostBy': None,
        'link': link
    }

def extract_artstation_images(content):
    """Extract image URLs from ArtStation content:encoded"""
    images = []
    # Find all img tags
    img_pattern = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']')
    
    for match in img_pattern.finditer(content):
        url = match.group(1)
        # Only include artstation CDN images
        if 'artstation.com' in url:
            images.append({
                'thumb': url,
                'fullsize': url,
                'alt': ''
            })
    
    return images

# ============== Filtering Functions ==============

def filter_cross_reposts(posts, bluesky_following):
    """Remove reposts of Bluesky authors we already follow"""
    following_set = set(bluesky_following)
    filtered = []
    for post in posts:
        if post['repostBy'] is None:
            filtered.append(post)
        elif post['author']['handle'] not in following_set:
            filtered.append(post)
    return filtered

def filter_media_only(posts):
    """Keep only posts with images OR pure reposts with links"""
    filtered = []
    for post in posts:
        embed = post.get('embed')
        
        # Keep posts with images
        if embed and embed.get('type') == 'images':
            filtered.append(post)
            continue
        
        # Keep pure reposts with external links
        if post.get('repostBy') and embed and embed.get('type') == 'external':
            filtered.append(post)
            continue
    
    return filtered

def filter_duplicates(posts):
    """Remove duplicate posts by URI"""
    seen_uris = set()
    filtered = []
    
    for post in posts:
        uri = post.get('uri')
        if uri in seen_uris:
            continue
        seen_uris.add(uri)
        filtered.append(post)
    
    return filtered

# ============== Main ==============

def main():
    config_path = Path('art-feed-config.json')
    output_path = Path('art-feed-data.json')
    
    # Load configuration
    with open(config_path, 'r') as f:
        config = json.load(f)
    
    profiles = {}
    all_posts = []
    
    # ---- Fetch Bluesky ----
    bluesky_config = config.get('bluesky', {})
    bluesky_following = bluesky_config.get('following', [])
    posts_per_user = bluesky_config.get('postsPerUser', 50)
    filter_replies = bluesky_config.get('filterReplies', True)
    
    if bluesky_following:
        print(f"Fetching Bluesky feeds for {len(bluesky_following)} accounts...")
        
        for handle in bluesky_following:
            print(f"  Bluesky: {handle}")
            
            profile = fetch_bluesky_profile(handle)
            profiles[f"bluesky:{handle}"] = profile
            
            feed = fetch_bluesky_feed(handle, limit=posts_per_user, filter_replies=filter_replies)
            print(f"    Found {len(feed)} posts")
            
            for item in feed:
                processed = process_bluesky_post(item)
                all_posts.append(processed)
    
    # ---- Fetch ArtStation ----
    artstation_config = config.get('artstation', {})
    artstation_following = artstation_config.get('following', [])
    
    if artstation_following:
        print(f"Fetching ArtStation feeds for {len(artstation_following)} accounts...")
        
        for username in artstation_following:
            print(f"  ArtStation: {username}")
            
            posts, profile = fetch_artstation_feed(username)
            if profile:
                profiles[f"artstation:{username}"] = profile
            
            print(f"    Found {len(posts)} posts with images")
            all_posts.extend(posts)
    
    # ---- Process & Filter ----
    print(f"\nTotal posts collected: {len(all_posts)}")
    
    # Sort by date (newest first)
    all_posts.sort(key=lambda p: p['indexedAt'] or '', reverse=True)
    
    # Filter out cross-reposts (Bluesky only)
    all_posts = filter_cross_reposts(all_posts, bluesky_following)
    print(f"After cross-repost filter: {len(all_posts)}")
    
    # Filter to media-only posts
    all_posts = filter_media_only(all_posts)
    print(f"After media filter: {len(all_posts)}")
    
    # Remove duplicates
    all_posts = filter_duplicates(all_posts)
    print(f"After duplicate filter: {len(all_posts)}")
    
    # Build output
    output = {
        'lastUpdated': datetime.utcnow().isoformat() + 'Z',
        'profiles': profiles,
        'posts': all_posts
    }
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nWrote {len(all_posts)} posts to {output_path}")

if __name__ == '__main__':
    main()
