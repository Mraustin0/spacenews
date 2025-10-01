from flask import Flask, render_template, jsonify, request, session, redirect, url_for
import requests
import os
from datetime import datetime
from time import time
import sqlite3
import json
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "supersecretkey"

# Simple in-memory cache for API responses
CACHE_TTL_DEFAULT = 900  # 15 minutes
api_cache = {}


def fetch_with_cache(cache_key, ttl=CACHE_TTL_DEFAULT, fetcher=lambda: None):
    now = time()
    cached = api_cache.get(cache_key)
    if cached and now - cached['time'] < ttl:
        return cached['value']

    value = fetcher()
    if value is not None:
        api_cache[cache_key] = {'value': value, 'time': now}
    return value

# Move mars_perseverance_gallery route and function here
@app.route('/mars_perseverance')
def mars_perseverance_gallery():
    API_KEY = 'Nck2yzPgvBPyrIXPkxS8Q5fos91gn09A2fX3ZsS4'
    mars_images = []
    error_message = None
    rover = 'perseverance'
    sol = None
    max_sol = None
    try:
        # Get rover info to find max_sol
        rover_info_url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}?api_key={API_KEY}"
        rover_info_resp = requests.get(rover_info_url, timeout=10)
        rover_info_resp.raise_for_status()
        rover_info_data = rover_info_resp.json()
        max_sol = rover_info_data['rover']['max_sol']
        # Get sol from request, fallback to max_sol
        sol_arg = request.args.get('sol')
        try:
            sol = int(sol_arg) if sol_arg else max_sol
        except (TypeError, ValueError):
            sol = max_sol
        if sol > max_sol:
            sol = max_sol
        # Try to fetch latest images, fallback to earlier sol if not found
        found_photos = []
        tried_sols = []
        attempt_sol = sol
        for offset in range(0, 10):  # Try up to 10 sols back to find at least 1 photo
            tried_sols.append(attempt_sol)
            url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos"
            params = {'api_key': API_KEY, 'sol': attempt_sol, 'page': 1}
            print(f"[DEBUG] Requesting {url} with params: {params}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            photos = response.json().get('photos', [])
            print(f"[DEBUG] For sol={attempt_sol}, Photos returned: {len(photos)}")
            if photos:
                found_photos = photos
                sol = attempt_sol
                break
            attempt_sol = max(sol - (offset + 1), 0)
            if attempt_sol == 0:
                break
        if found_photos:
            for photo in found_photos[:15]:
                mars_images.append({
                    'id': photo['id'],
                    'url': photo['img_src'],
                    'title': photo['camera']['full_name'],
                    'date': photo['earth_date'],
                    'sol': photo['sol'],
                    'rover': photo['rover']['name'],
                    'camera_code': photo['camera']['name']
                })
        else:
            error_message = "No Perseverance images found for the latest Sol."
    except Exception as e:
        error_message = f"Error fetching Perseverance images: {str(e)}"
        print(error_message)
    # fallback placeholder
    if not mars_images:
        mars_images = [
            {
                'id': f'placeholder_{i}',
                'url': f'https://via.placeholder.com/400x300/444/fff?text=Perseverance+{i+1}',
                'title': f'Perseverance Placeholder {i+1}',
                'date': '2025-01-01',
                'sol': str(sol if sol is not None else (max_sol if max_sol is not None else 1)),
                'rover': 'Perseverance',
                'camera_code': 'NAVCAM'
            } for i in range(15)
        ]
    return render_template('margallery.html', 
                           mars_images=mars_images,
                           rovers=['perseverance'],
                           cameras=[],
                           current_rover='perseverance',
                           current_camera='',
                           current_sol=sol,
                           current_earth_date='',
                           current_page=1,
                           error_message=error_message)

# Database setup
DATABASE = 'users.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_gallery (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item_type TEXT NOT NULL,
            reference TEXT NOT NULL,
            title TEXT,
            description TEXT,
            media_url TEXT,
            metadata TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, item_type, reference)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Context processor to inject current_user into all templates
@app.context_processor
def inject_user():
    user = None
    if 'user_id' in session:
        conn = get_db_connection()
        user_row = conn.execute('SELECT username FROM users WHERE id = ?', (session['user_id'],)).fetchone()
        conn.close()
        if user_row:
            user = {'username': user_row['username']}
    return dict(current_user=user)

# NASA API Configuration
NASA_API_KEY = "Nck2yzPgvBPyrIXPkxS8Q5fos91gn09A2fX3ZsS4"
NASA_BASE_URL = "https://api.nasa.gov"
API_KEY = 'Nck2yzPgvBPyrIXPkxS8Q5fos91gn09A2fX3ZsS4'


def get_apod_json(params, cache_key, ttl=CACHE_TTL_DEFAULT):
    def _fetch():
        try:
            response = requests.get(f'{NASA_BASE_URL}/planetary/apod', params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.RequestException:
            return None

    return fetch_with_cache(cache_key, ttl, _fetch)


def get_apod_by_date(date_str):
    params = {'api_key': API_KEY, 'date': date_str}
    return get_apod_json(params, ('apod-date', date_str))


def get_apod_latest():
    params = {'api_key': API_KEY}
    return get_apod_json(params, ('apod-latest',), ttl=3600)


def get_apod_range(start_date, end_date):
    params = {
        'api_key': API_KEY,
        'start_date': start_date,
        'end_date': end_date
    }
    return get_apod_json(params, ('apod-range', start_date, end_date)) or []

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if not username or not password:
            return render_template('register.html', error="Username and password are required.")
        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, hashed_password))
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template('register.html', error="Username already exists.")
        conn.close()
        return redirect(url_for('login'))
    else:
        return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        conn = get_db_connection()
        user_row = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        if user_row and check_password_hash(user_row['password'], password):
            session['user_id'] = user_row['id']
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error="Invalid username or password.")
    else:
        return render_template('login.html')

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

@app.route('/api/apod')
def get_apod():
    """Get Astronomy Picture of the Day"""
    try:
        url = f"{NASA_BASE_URL}/planetary/apod"
        params = {
            'api_key': NASA_API_KEY,
            'hd': True
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return jsonify({
            'success': True,
            'data': data
        })
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/mars-weather')
def get_mars_weather():
    """Get Mars Weather Data"""
    try:
        url = f"{NASA_BASE_URL}/insight_weather/"
        params = {
            'api_key': NASA_API_KEY,
            'feedtype': 'json',
            'ver': '1.0'
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return jsonify({
            'success': True,
            'data': data
        })
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/earth-imagery')
def get_earth_imagery():
    """Get Earth Imagery"""
    try:
        # Bangkok coordinates
        lat = 13.7563
        lon = 100.5018
        date = "2023-01-01"
        
        url = f"{NASA_BASE_URL}/planetary/earth/imagery"
        params = {
            'lon': lon,
            'lat': lat,
            'date': date,
            'api_key': NASA_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        return jsonify({
            'success': True,
            'image_url': response.url
        })
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/neo')
def get_near_earth_objects():
    """Get Near Earth Objects"""
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        url = f"{NASA_BASE_URL}/neo/rest/v1/feed"
        params = {
            'start_date': today,
            'end_date': today,
            'api_key': NASA_API_KEY
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        
        data = response.json()
        return jsonify({
            'success': True,
            'data': data
        })
    except requests.RequestException as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/apod')
def apod_page():
    """Show only today's APOD image and info"""
    data = get_apod_latest() or {}
    if data.get('media_type') == 'image':
        apod_data = {
            'title': data.get('title').title(),
            'date': data.get('date'),
            'explanation': data.get('explanation'),
            'url': data.get('url')
        }
    else:
        apod_data = None
    return render_template('apod.html', apod_data=apod_data, is_logged_in=('user_id' in session))

@app.route('/apod_gallery')
def apod_gallery_page():
    """
    Show APOD gallery: one entry per day (latest 30 days or filter).
    """
    day = request.args.get('day')
    month = request.args.get('month')
    year = request.args.get('year')
    apod_data = []

    try:
        if day and month and year:
            date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            data = get_apod_by_date(date_str) or {}
            if data.get('media_type') == 'image':
                apod_data = [{
                    'title': data.get('title'),
                    'date': data.get('date'),
                    'explanation': data.get('explanation'),
                    'url': data.get('url')
                }]
        else:
            from datetime import timedelta
            today = datetime.utcnow().date()
            start_date = (today - timedelta(days=30)).strftime('%Y-%m-%d')
            end_date = today.strftime('%Y-%m-%d')
            data = get_apod_range(start_date, end_date)
            if isinstance(data, list):
                # กลุ่มข้อมูลตามวัน (วันละ entry)
                for item in data:
                    if item.get('media_type') == 'image':
                        apod_data.append({
                            'title': item.get('title'),
                            'date': item.get('date'),
                            'explanation': item.get('explanation'),
                            'url': item.get('url')
                        })
    except Exception as e:
        apod_data = []

    years = list(range(1995, datetime.now().year + 1))

    return render_template('apodgallery.html', apod_data=apod_data, day=day, month=month, year=year, years=years)

@app.route('/apod_detail/<date>')
def apod_detail(date):
    """
    Show detail of APOD for a specific date (format YYYY-MM-DD).
    """
    data = get_apod_by_date(date) or {}
    if data.get('media_type') == 'image':
        apod_data = {
            'title': data.get('title'),
            'date': data.get('date'),
            'explanation': data.get('explanation'),
            'url': data.get('url')
        }
    else:
        apod_data = None
    return render_template('apod_detail.html', apod_data=apod_data, is_logged_in=('user_id' in session))

@app.route('/add_to_gallery/<date>', methods=['POST'])
def add_to_gallery(date):
    """
    Add APOD of a specific date to user's favorite gallery stored in session.
    """
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'login_required'}), 401

    user_id = session['user_id']
    apod_info = get_apod_by_date(date) or {}

    if apod_info.get('media_type') != 'image':
        return jsonify({'success': False, 'error': 'invalid_media'}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute(
            'SELECT id FROM user_gallery WHERE user_id = ? AND item_type = ? AND reference = ?',
            (user_id, 'apod', date)
        ).fetchone()
        if existing:
            return jsonify({'success': False, 'error': 'already_saved'})

        metadata = {
            'date': apod_info.get('date'),
            'hdurl': apod_info.get('hdurl'),
            'service_version': apod_info.get('service_version')
        }
        conn.execute(
            '''INSERT INTO user_gallery (user_id, item_type, reference, title, description, media_url, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                user_id,
                'apod',
                date,
                apod_info.get('title'),
                apod_info.get('explanation'),
                apod_info.get('url'),
                json.dumps(metadata)
            )
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'success': False, 'error': 'already_saved'})
    finally:
        conn.close()

    return jsonify({'success': True})

@app.route('/my_gallery')
@app.route('/mygallery')
@app.route('/mygallery.html')
def my_gallery():
    """
    Show user's favorite APOD images stored in session.
    Only accessible if logged in.
    """
    if 'user_id' not in session:
        return redirect(url_for('login'))

    conn = get_db_connection()
    rows = conn.execute(
        '''SELECT item_type, reference, title, description, media_url, metadata
           FROM user_gallery
           WHERE user_id = ?
           ORDER BY datetime(coalesce(created_at, '1970-01-01')) DESC, id DESC''',
        (session['user_id'],)
    ).fetchall()
    conn.close()

    apod_data = []
    mars_data = []

    for row in rows:
        metadata = {}
        if row['metadata']:
            try:
                metadata = json.loads(row['metadata'])
            except (TypeError, json.JSONDecodeError):
                metadata = {}

        if row['item_type'] == 'apod':
            apod_data.append({
                'title': row['title'] or 'Astronomy Picture',
                'date': metadata.get('date') or row['reference'],
                'explanation': row['description'] or '',
                'url': row['media_url']
            })
        elif row['item_type'] == 'mars':
            mars_data.append({
                'title': row['title'] or 'Mars Photo',
                'date': metadata.get('date'),
                'rover': metadata.get('rover'),
                'camera': metadata.get('camera'),
                'url': row['media_url']
            })

    return render_template('mygallery.html', apod_data=apod_data, mars_data=mars_data)

@app.route('/mars_gallery')
def mars_gallery():
    """Show Mars Gallery images using NASA Mars Rover API with fallback"""
    API_KEY = 'Nck2yzPgvBPyrIXPkxS8Q5fos91gn09A2fX3ZsS4'

    rover = request.args.get('rover', 'curiosity').lower()
    page = int(request.args.get('page', 1))
    earth_date = request.args.get('earth_date') or ''
    camera_param = (request.args.get('camera') or '').lower()
    sort = request.args.get('sort', 'desc').lower()
    if sort not in {'asc', 'desc'}:
        sort = 'desc'

    mars_images = []
    error_message = None
    sol = None
    cameras = []

    try:
        rover_info_url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}?api_key={API_KEY}"
        rover_info_resp = requests.get(rover_info_url, timeout=10)
        rover_info_resp.raise_for_status()
        rover_info_data = rover_info_resp.json()
        max_sol = rover_info_data['rover']['max_sol']
        cameras = sorted({cam['name'].lower() for cam in rover_info_data['rover'].get('cameras', [])})

        photos = []

        if earth_date:
            params = {'api_key': API_KEY, 'earth_date': earth_date, 'page': page}
            if camera_param:
                params['camera'] = camera_param
            photos_resp = requests.get(
                f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos",
                params=params,
                timeout=10
            )
            photos_resp.raise_for_status()
            photos = photos_resp.json().get('photos', [])
            if photos:
                sol = photos[0].get('sol')
            else:
                error_message = f"No images found for {rover.title()} on {earth_date}."
        else:
            # ใช้ sol ที่เลือก หรือ max_sol ถ้าไม่มี
            try:
                sol_arg = request.args.get('sol')
                sol = int(sol_arg) if sol_arg else max_sol
            except (TypeError, ValueError):
                sol = max_sol
            if sol > max_sol:
                sol = max_sol

            # ลองหา sol ย้อนหลังสูงสุด 10 วัน
            for offset in range(0, 10):
                attempt_sol = max(sol - offset, 0)
                params = {'api_key': API_KEY, 'sol': attempt_sol, 'page': page}
                if camera_param:
                    params['camera'] = camera_param
                url = f"https://api.nasa.gov/mars-photos/api/v1/rovers/{rover}/photos"
                resp = requests.get(url, params=params, timeout=10)
                resp.raise_for_status()
                photos = resp.json().get('photos', [])
                if photos:
                    sol = attempt_sol
                    break

            if not photos:
                error_message = error_message or "No images found for this rover." 

        if photos:
            def _sort_key(item):
                date_value = item.get('earth_date')
                try:
                    parsed_date = datetime.strptime(date_value, '%Y-%m-%d') if date_value else datetime.min
                except (TypeError, ValueError):
                    parsed_date = datetime.min
                return (parsed_date, item.get('sol') or 0)

            photos.sort(key=_sort_key, reverse=(sort == 'desc'))
            for photo in photos[:15]:
                mars_images.append({
                    'id': photo['id'],
                    'url': photo['img_src'],
                    'title': photo['camera']['full_name'],
                    'date': photo['earth_date'],
                    'sol': photo['sol'],
                    'rover': photo['rover']['name'],
                    'camera_code': photo['camera']['name']
                })
    except Exception as e:
        error_message = f"Error fetching Mars images: {str(e)}"
        print(error_message)

    if not mars_images:
        error_message = error_message or f"No images available for {rover.title()}."
        mars_images = []

    rovers = ['curiosity', 'opportunity', 'spirit', 'perseverance']

    return render_template('margallery.html',
                         mars_images=mars_images,
                         rovers=rovers,
                         cameras=cameras,
                         current_rover=rover,
                         current_camera=camera_param,
                         current_sol=sol,
                         current_earth_date=earth_date,
                         sort=sort,
                         current_page=page,
                         error_message=error_message)


@app.route('/mars_detail')
def mars_detail():
    image_url = request.args.get('url')
    if not image_url:
        return redirect(url_for('mars_gallery'))

    image_data = {
        'url': image_url,
        'title': request.args.get('title', 'Mars Photo'),
        'date': request.args.get('date', ''),
        'rover': request.args.get('rover', ''),
        'camera': request.args.get('camera', '')
    }

    return render_template('margallery_detail.html', image=image_data, is_logged_in=('user_id' in session))


@app.route('/add_mars_favorite', methods=['POST'])
def add_mars_favorite():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'login_required'}), 401

    payload = request.get_json(silent=True) or {}
    image_url = payload.get('url')
    title = payload.get('title')
    date = payload.get('date')
    rover = payload.get('rover')
    camera = payload.get('camera')

    if not image_url:
        return jsonify({'success': False, 'error': 'invalid_payload'}), 400

    conn = get_db_connection()
    try:
        existing = conn.execute(
            'SELECT id FROM user_gallery WHERE user_id = ? AND item_type = ? AND reference = ?',
            (session['user_id'], 'mars', image_url)
        ).fetchone()
        if existing:
            return jsonify({'success': False, 'error': 'already_saved'})

        metadata = {
            'date': date,
            'rover': rover,
            'camera': camera
        }
        conn.execute(
            '''INSERT INTO user_gallery (user_id, item_type, reference, title, description, media_url, metadata)
               VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (
                session['user_id'],
                'mars',
                image_url,
                title or 'Mars Photo',
                None,
                image_url,
                json.dumps(metadata)
            )
        )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        return jsonify({'success': False, 'error': 'already_saved'})
    finally:
        conn.close()

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug=True)
