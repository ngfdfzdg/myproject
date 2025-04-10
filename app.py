from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from googleapiclient.discovery import build
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import requests
import re

# Initialize Flask app and enable CORS
app = Flask(__name__)
CORS(app)

# Configuration
API_KEY = "AIzaSyCGcwwQgk50i8_FAWi670jU3nVlfadXsLA"  # Replace with a valid YouTube API key
COURSE_KEYWORDS = ["course", "tutorial", "learn", "lesson"]

# Initialize VADER sentiment analyzer
analyzer = SentimentIntensityAnalyzer()

# Helper function to check if a query is course-related
def is_course_query(query):
    query_lower = query.lower()
    return any(keyword in query_lower for keyword in COURSE_KEYWORDS)

# Search YouTube for videos
def search_youtube(query, max_results=5):
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.search().list(
            q=query,  # Use query directly without appending extra words
            part="snippet",
            type="video",
            order="relevance",  # Change from "viewCount" to "relevance"
            maxResults=max_results * 2
        )
        response = request.execute()
        video_ids = [item["id"]["videoId"] for item in response.get("items", [])]
        
        details_request = youtube.videos().list(
            part="contentDetails,snippet,statistics",
            id=",".join(video_ids)
        )
        details_response = details_request.execute()
        
        videos = []
        for item in details_response.get("items", []):
            title = item["snippet"]["title"].lower()
            duration = item["contentDetails"]["duration"]
            minutes = parse_duration_to_minutes(duration)
            if minutes > 5:  # Removed excessive keyword filtering
                videos.append({
                    "title": item["snippet"]["title"],
                    "video_id": item["id"],
                    "thumbnail": item["snippet"]["thumbnails"]["default"]["url"],
                    "view_count": int(item["statistics"]["viewCount"]) if "statistics" in item else 0
                })
        return videos[:max_results]
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return []

# Parse duration to minutes
def parse_duration_to_minutes(duration):
    hours = re.search(r'(\d+)H', duration)
    minutes = re.search(r'(\d+)M', duration)
    seconds = re.search(r'(\d+)S', duration)
    total_minutes = 0
    if hours:
        total_minutes += int(hours.group(1)) * 60
    if minutes:
        total_minutes += int(minutes.group(1))
    if seconds:
        total_minutes += int(seconds.group(1)) / 60
    return total_minutes

# Fetch video comments
def get_video_comments(video_id, max_comments=50):
    try:
        youtube = build("youtube", "v3", developerKey=API_KEY)
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=max_comments
        )
        response = request.execute()
        return [
            item["snippet"]["topLevelComment"]["snippet"]["textOriginal"]
            for item in response.get("items", [])
        ]
    except Exception as e:
        print(f"Could not fetch comments for video {video_id}: {e}")
        return []

# Rank videos based on sentiment and view count
def rank_videos(videos):
    k = 5  # Smoothing factor
    for video in videos:
        comments = get_video_comments(video["video_id"])
        if comments:
            sentiments = [analyzer.polarity_scores(c)["compound"] for c in comments]
            sum_sentiments = sum(sentiments)
            num_comments = len(sentiments)
        else:
            sum_sentiments = 0
            num_comments = 0
        smoothed_score = (sum_sentiments + 0 * k) / (num_comments + k) if num_comments + k > 0 else 0
        video["sentiment_score"] = smoothed_score
        video["view_count"] = video.get("view_count", 0)
    
    sorted_videos = sorted(videos, key=lambda x: (x["sentiment_score"], x["view_count"]), reverse=True)
    ranked_videos = [
        {
            "title": video["title"],
            "video_id": video["video_id"],
            "score": round(video["sentiment_score"], 2),
            "url": f"https://www.youtube.com/watch?v={video['video_id']}",
            "thumbnail": video["thumbnail"]
        }
        for video in sorted_videos
    ]
    return ranked_videos

# Get YouTube suggestions
def get_youtube_suggestions(query):
    url = f"https://suggestqueries.google.com/complete/search?client=firefox&ds=yt&q={query}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            suggestions = [sugg for sugg in response.json()[1] if is_course_query(sugg)]
            return suggestions[:10]
        return []
    except Exception as e:
        print(f"Error fetching suggestions: {e}")
        return []



# Recommend endpoint
@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        query = data.get('query', '')
        if not query:
            return jsonify({"error": "No query provided"}), 400
        if is_course_query(query):
            videos = search_youtube(query)
            if not videos:
                return jsonify({"error": "No videos found or API error"}), 500
            ranked_videos = rank_videos(videos)
            return jsonify({"videos": ranked_videos})
        else:
            return jsonify({"error": "Search only courses (e.g., 'Python course')"}), 400
    except Exception as e:
        print(f"Error in recommend endpoint: {e}")
        return jsonify({"error": str(e)}), 500

# Suggestions endpoint
@app.route('/suggestions', methods=['GET'])
def suggestions():
    try:
        query = request.args.get('q', '')
        suggestions = get_youtube_suggestions(query)
        return jsonify(suggestions)
    except Exception as e:
        print(f"Error in suggestions endpoint: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
