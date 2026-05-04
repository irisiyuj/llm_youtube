
import sqlite3
import requests
import json
import time
from datetime import datetime
from youtube_transcript_api import YouTubeTranscriptApi
from zhipuai import ZhipuAI

import os
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY', '')
ZHIPU_API_KEY = os.environ.get('ZHIPU_API_KEY', '')

CHANNELS = {
    "Andrej Karpathy": "UCXUPKJO5MZQN11PqgIvyuvQ",
    "Matthew Berman": "UCawZsQWqfGSbCI5yjkdVkTA",
    "Matt Wolfe": "UChpleBmo18P08aKCIgti38g"
}


def init_db():
    conn = sqlite3.connect('llm_watcher.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            video_id TEXT PRIMARY KEY,
            channel_name TEXT,
            title TEXT,
            published_at TEXT,
            transcript TEXT,
            topics TEXT,
            relation TEXT,
            summary TEXT,
            processed_at TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print("Database initialized")

def fetch_youtube_videos(channel_id, max_results=2):
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "channelId": channel_id,
        "maxResults": max_results,
        "order": "date",
        "type": "video",
        "key": YOUTUBE_API_KEY
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    if "error" in data:
        print(f"   YouTube API Error: {data['error']['message']}")
        return []
    
    videos = []
    for item in data.get("items", []):
        video_id = item["id"]["videoId"]
        title = item["snippet"]["title"]
        published_at = item["snippet"]["publishedAt"]
        videos.append({
            "id": video_id,
            "title": title,
            "published_at": published_at
        })
    return videos

def get_transcript(video_id):
    """Get video transcript"""
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript_list = ytt_api.list(video_id)
        for transcript in transcript_list:
            if transcript.language_code == 'en':
                transcript_data = transcript.fetch()
                full_text = " ".join([t.text for t in transcript_data])
                print(f"   Got captions! ({len(full_text)} chars)")
                return full_text
        return None
    except Exception as e:
        print(f"   No captions: {e}")
        return None

def analyze_with_zhipu(transcript, channel_name, video_title, other_channels):
    """Analyze transcript using ZhipuAI"""
    
    transcript_short = transcript[:3000]
    
    prompt = f"""Analyze this YouTube video. Return ONLY valid JSON, no explanation.

Channel: {channel_name}
Title: {video_title}
Other channels: {', '.join(other_channels)}

Transcript excerpt: {transcript_short}

Valid JSON format:
{{"topics": ["topic1", "topic2"], "relation": "relationship description", "summary": "one sentence summary"}}"""
    
    try:
        response = zhipu_client.chat.completions.create(
            model="glm-4-flash",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=500
        )
        
        result_text = response.choices[0].message.content
        print(f"   AI Response: {result_text[:200]}...")  # 打印前200字符用于调试
        
        # 尝试提取JSON（处理可能的多余文字）
        import re
        json_match = re.search(r'\{[^{}]*"topics"[^{}]*\}', result_text, re.DOTALL)
        if json_match:
            result = json.loads(json_match.group())
        else:
            # 尝试直接解析
            result = json.loads(result_text)
        
        # 验证必要字段
        if "topics" not in result:
            result["topics"] = ["LLM", "AI"]
        if "relation" not in result:
            result["relation"] = f"{channel_name} discusses AI topics"
        if "summary" not in result:
            result["summary"] = f"Video about {video_title[:40]}"
        
        return result
    except Exception as e:
        print(f"   ZhipuAI failed: {e}")
        print(f"   Raw response: {result_text if 'result_text' in locals() else 'No response'}")
        return {
            "topics": ["LLM", "Deep Learning"],
            "relation": f"{channel_name} focuses on AI and language models",
            "summary": f"{channel_name} discusses {video_title[:50]}"
        }

def is_processed(video_id):
    conn = sqlite3.connect('llm_watcher.db')
    c = conn.cursor()
    c.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
    result = c.fetchone()
    conn.close()
    return result is not None

def save_to_db(video_id, channel_name, title, published_at, transcript, analysis):
    conn = sqlite3.connect('llm_watcher.db')
    c = conn.cursor()
    c.execute('''
        INSERT OR REPLACE INTO videos 
        (video_id, channel_name, title, published_at, transcript, topics, relation, summary, processed_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        video_id, channel_name, title, published_at, transcript,
        json.dumps(analysis['topics']), analysis['relation'], analysis['summary'],
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

def generate_html():
    conn = sqlite3.connect('llm_watcher.db')
    c = conn.cursor()
    c.execute('''
        SELECT channel_name, title, topics, relation, summary, published_at 
        FROM videos 
        ORDER BY published_at DESC 
        LIMIT 30
    ''')
    videos = c.fetchall()
    conn.close()
    
    if not videos:
        print("Database is empty, no video data yet")
        return
    
    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>LLM YouTube Monitor</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        h1 {{ color: #333; }}
        table {{ border-collapse: collapse; width: 100%; background: white; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; vertical-align: top; }}
        th {{ background-color: #4CAF50; color: white; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        .timestamp {{ color: #666; margin: 20px 0; }}
        .channel-name {{ font-weight: bold; }}
        .date {{ font-size: 12px; color: #888; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>LLM YouTube Channel Monitor</h1>
    <div class="timestamp">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
    <p>Tracking: Andrej Karpathy | Yannic Kilcher | Matt Wolfe</p>
    <table>
        <tr>
            <th>Channel</th>
            <th>Video Title</th>
            <th>LLM Topics</th>
            <th>Relation to Other Channels</th>
            <th>Summary</th>
        </tr>
"""
    
    for v in videos:
        channel, title, topics_json, relation, summary, published = v
        try:
            topics = ", ".join(json.loads(topics_json))
        except:
            topics = topics_json
        
        pub_date = published[:10] if published else "Unknown"
        
        html += f"""
        <tr>
            <td>
                <div class="channel-name">{channel}</div>
                <div class="date">{pub_date}</div>
            </td>
            <td>{title[:100]}</td>
            <td>{topics}</td>
            <td>{relation}</td>
            <td>{summary}</td>
        </tr>
"""
    
    html += """
    </table>
    <p><small>Data source: YouTube API + ZhipuAI (GLM-4-Flash)</small></p>
</body>
</html>
"""
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("HTML table generated: index.html")

def main():
    print(f"\nStarting update - {datetime.now()}")
    print("=" * 50)
    
    init_db()
    other_channels = list(CHANNELS.keys())
    
    for channel_name, channel_id in CHANNELS.items():
        print(f"\nProcessing: {channel_name}")
        
        videos = fetch_youtube_videos(channel_id, max_results=5)
        
        for video in videos:
            video_id = video['id']
            
            if is_processed(video_id):
                print(f"   Skip: {video['title'][:40]}...")
                continue
            
            print(f"   Processing: {video['title'][:50]}...")
            
            transcript = get_transcript(video_id)
            if not transcript:
                print(f"   Skipping (no captions)")
                continue
            
            analysis = analyze_with_zhipu(transcript, channel_name, video['title'], other_channels)
            save_to_db(video_id, channel_name, video['title'], video['published_at'], transcript, analysis)
            
            print(f"   Done - Topics: {', '.join(analysis.get('topics', [])[:2])}")
            time.sleep(2)
    
    print("\n" + "=" * 50)
    print("Update complete!")
    generate_html()

if __name__ == "__main__":
    main()
