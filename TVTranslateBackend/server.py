from flask import Flask, request, jsonify
import os
import urllib.parse
import urllib.request
import json

app = Flask(__name__)

YOUTUBE_API_KEY = os.environ.get("YOUTUBE_API_KEY")
FREETRANSCRIPT_API_KEY = os.environ.get("FREETRANSCRIPT_API_KEY")

ALLOWED_LANGUAGES = {
    "hi": "Hindi",
    "ta": "Tamil",
    "ml": "Malayalam",
    "te": "Telugu",
    "en": "English"
}


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    return response


@app.route("/api")
def home():
    return jsonify({
        "status": "TV Translate backend is running"
    })


@app.route("/api/transcript")
def transcript():
    video_id = request.args.get("videoId", "").strip()
    language = request.args.get("lang", "hi").strip().lower()

    if not video_id:
        return jsonify({
            "error": "Missing videoId"
        }), 400

    if language not in ALLOWED_LANGUAGES:
        return jsonify({
            "error": "Unsupported language",
            "supported": list(ALLOWED_LANGUAGES.keys())
        }), 400
    try:
        url = (
            "https://api.freetranscriptapi.com/v1/transcript?"
            + urllib.parse.urlencode({
                "video_url": "https://www.youtube.com/watch?v=" + video_id,
                "lang": language
            })
        )

               req = urllib.request.Request(
                   url,
                   headers={
                       "Authorization": "Bearer " + FREETRANSCRIPT_API_KEY
                   }
               )

               with urllib.request.urlopen(req, timeout=30) as response:
                   data = response.read().decode("utf-8")
            data = response.read().decode("utf-8")

        transcript_data = json.loads(data)

        if not transcript_data.get("transcript"):
            return jsonify({
                "error": "No transcript found"
            }), 404

        segments = transcript_data["transcript"]
        return jsonify({
            "videoId": video_id,
            "language": language,
            "languageName": ALLOWED_LANGUAGES[language],
            "count": len(segments),
            "segments": segments
        })

    except Exception as error:
        return jsonify({
            "error": "Could not get transcript",
            "details": str(error)
        }), 500

@app.route("/api/search")
def search():
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Missing search query"}), 400

    if not YOUTUBE_API_KEY:
        return jsonify({"error": "YouTube API key is not configured"}), 500

    params = {
        "part": "snippet",
        "q": query,
        "type": "video",
        "maxResults": 10,
        "videoEmbeddable": "true",
        "key": YOUTUBE_API_KEY
    }

    url = (
        "https://www.googleapis.com/youtube/v3/search?"
        + urllib.parse.urlencode(params)
    )

    try:
        with urllib.request.urlopen(url, timeout=15) as response:
            data = response.read().decode("utf-8")

        youtube_data = json.loads(data)

        results = []

        for item in youtube_data.get("items", []):
            results.append({
                "videoId": item["id"]["videoId"],
                "title": item["snippet"]["title"],
                "channel": item["snippet"]["channelTitle"],
                "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"]
            })

        return jsonify({
            "query": query,
            "results": results
        })

    except Exception as error:
        return jsonify({
            "error": "YouTube search failed",
            "details": str(error)
        }), 500

if __name__ == "__main__":
    print("===================================")
    print("       TV Translate Backend")
    print("===================================")
    print("Server running on port 8080")
    print("")

    app.run(
        host="0.0.0.0",
        port=8080,
        debug=False
    )
