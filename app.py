from flask import Flask, render_template, request, jsonify, Response
import os, requests, json, re, threading, time, urllib.parse, shutil
from datetime import datetime
from file_to_magnet import torrent_to_magnet
from subtitles2 import subtitles_maneger
from iptv import iptv_class
import subprocess


app = Flask(__name__)
DOWNLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'downloads')

# --- Helper functions for file operations ---
def load_json_file(filename):
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def save_json_file(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/movie.html')
def movie():
    return render_template('movie.html')

@app.route('/download', methods=['POST'])
def download():
    data = request.get_json()
    torrents = data.get('torrents', [])
    results = []
    for torrent in torrents:
        torrent_url = torrent.get('url')
        quality = torrent.get('quality')
        file_name = torrent_url.split("download/")[1]
        video_path = os.path.join(DOWNLOAD_FOLDER, file_name)
        if not os.path.exists(video_path):
            response = requests.get(torrent_url)
            response.raise_for_status()
            with open(video_path, 'wb') as f:
                f.write(response.content)
        file_magnet = torrent_to_magnet(video_path)
        results.append({"url": torrent_url, "quality": quality, "file_magnet": file_magnet})
    return jsonify({"status": "success", "data": results}), 200


@app.route('/saved_movies', methods=['GET', 'POST'])
def saved_movies_handler():
    if request.method == 'POST':
        # Get and parse the movie data.
        movie_data = json.loads(urllib.parse.unquote(request.form.get('movie_data')))
        action = request.form.get('action')
        saved_movies = load_json_file("utilities/saved_movies.txt")

        if action == 'save':
            # Filter the movie data to only keep specific keys.
            keys = ["id", "url", "imdb_code", "title", "background_image",
                    "background_image_original", "small_cover_image", "medium_cover_image", "large_cover_image"]
            filtered_movie = {k: movie_data.get(k) for k in keys}
            saved_movies.append(filtered_movie)
            save_json_file("utilities/saved_movies.txt", saved_movies)

        else:
            new_saved = [m for m in saved_movies if m.get("id") != movie_data.get("id")]
            save_json_file("utilities/saved_movies.txt", new_saved)
        return "0"


    return jsonify(load_json_file("utilities/saved_movies.txt"))



@app.route('/popular_movies')
def popular_movies():
    try:
        with open("utilities/movies_json.txt", "r", encoding="utf-8") as f:
            content = f.read()
    except:
        get_popular_movies()
        with open("utilities/movies_json.txt", "r", encoding="utf-8") as f:
            content = f.read()
    return content

@app.route('/livetv')
def livetv():
    with open("utilities/channels.json", "r", encoding="utf-8") as f:
        content = f.read()
    return content


@app.route('/stream_live')
def stream_live():
    return render_template('stream_live.html', channel_id=request.args.get('channel_id'))



@app.route('/stream_live_source/<channel_id>')
def video(channel_id):
    # Use ffmpeg to convert HLS to mp4 stream
    command = [
        'ffmpeg',
        '-i', iptv.cards_df.loc[iptv.cards_df["index"] == int(channel_id), "stream_url"].iloc[0],
        '-f', 'mp4',  # format
        '-movflags', 'frag_keyframe+empty_moov',  # needed for streaming MP4
        '-preset', 'ultrafast',
        'pipe:1'  # output to stdout
    ]
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)

    def generate():
        try:
            while True:
                data = process.stdout.read(1024)
                if not data:
                    break
                yield data
        finally:
            process.kill()

    return Response(generate(), mimetype='video/mp4')


# --- Helper for scraping popular movies ---
def get_popular_movies():
    url = "https://www.imdb.com/chart/moviemeter/"
    headers = {"User-Agent": "Mozilla/5.0"}  # Shortened header
    response = requests.get(url, headers=headers)
    pattern = r'https://www.imdb.com/title/(tt\d{7,8})/'
    matches = re.findall(pattern, response.text)
    movies = []
    for imdb_id in matches:
        movie_response = requests.get(f"https://yts.mx/api/v2/movie_details.json?imdb_id={imdb_id}")
        movie = movie_response.json().get("data", {}).get("movie", {})
        if movie.get("id"):
            movies.append(movie)
    save_json_file('utilities/movies_json.txt', movies)



@app.route('/subtitles/<movie>')
def download_subtitles(movie):
    subtitles.download(movie)
    return "done"

@app.route('/stream/<movie>')
def stream_movie(movie):
    base_path = os.path.join('static', 'subtitles')
    subtitle_files = []
    for i in range(5):
        path = os.path.join(base_path, f'{movie}{i}.vtt')
        if os.path.exists(path):
            subtitle_files.append(f'{movie}{i}.vtt')
        else:
            break
    return render_template('stream.html', subtitle_files=subtitle_files)



# --- Utility functions ---
def delete_contents(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            os.remove(os.path.join(root, file))
        for d in dirs:
            shutil.rmtree(os.path.join(root, d))


def background_task():
    today = datetime.today().day
    get_popular_movies()
    print("update popular movies")
    while True:
        time.sleep(300)
        if datetime.today().day != today:
            today = datetime.today().day
            get_popular_movies()
            iptv.create_schedule()
            print("update popular movies and schedule")
        iptv.set_titles()




if __name__ == '__main__':
    # Combine deletion calls in a loop.
    for d in [r'media', r'static/subtitles', r'downloads']:
        delete_contents(d)

    subtitles= subtitles_maneger()
    iptv = iptv_class()



    if os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        threading.Thread(target=background_task, daemon=True).start()

    app.run(debug=True,host='0.0.0.0')



