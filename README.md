# SpaceNews Web App
      # project log 
   https://docs.google.com/spreadsheets/d/1P1gu9dyhWqUoSbVaSaiTorZLRpspsfxirRoNOp8Q8dk/edit?usp=sharing

SpaceNews is a Flask-based dashboard that curates daily astronomy highlights, Mars rover photography, and live space headlines into a single experience. It combines multiple NASA data services, the Spaceflight News API, and a persistent favourites gallery so users can build their own cosmic collection.

## Table of Contents
- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [APIs Used](#apis-used)
- [Project Layout](#project-layout)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [Usage Guide](#usage-guide)
- [Data Persistence](#data-persistence)
- [Development Notes](#development-notes)
- [Roadmap Ideas](#roadmap-ideas)

## Key Features
- **Daily APOD landing page** that auto-loads NASA’s Astronomy Picture of the Day, complete with modal feedback, downloads, and favourite/save actions.
- **APOD gallery** with date filtering, detailed views, and consistent UI state for saved items.
- **Mars gallery & detail pages** supporting rover/earth-date/camera filters, live API calls, and persistent favourites.
- **Space news dashboard** featuring latest articles from Spaceflight News, NASA InSight weather summaries, and NeoWs near-earth object stats.
- **Authentication** (register, log in/out) and personalised favourite storage using SQLite.
- **Responsive, unified look & feel** across APOD, Mars, and My Gallery pages, including breadcrumb states and nav styling.

## Tech Stack
- **Backend:** Python 3, Flask
- **Frontend:** Jinja2 templates + vanilla HTML/CSS/JavaScript
- **Database:** SQLite (`users.db`)
- **Auth:** Username/password with Werkzeug hashing

## APIs Used
| API | Purpose | Docs |
| --- | --- | --- |
| NASA APOD | Astronomy Picture of the Day metadata & imagery | https://api.nasa.gov/ |
| NASA Mars Rover Photos | Latest rover images with rover/camera info | https://api.nasa.gov/ |
| NASA InSight Weather Service | Mars weather summaries (proxied through backend) | https://api.nasa.gov/ |
| NASA NeoWs | Near-Earth Object counts & closest approach data | https://api.nasa.gov/ |
| Spaceflight News API | Daily space & launch headlines | https://api.spaceflightnewsapi.net |

## Project Layout
```
space/
├─ app.py                # Flask app, routes, NASA API calls, persistence helpers
├─ templates/            # HTML templates (Jinja2)
│  ├─ index.html         # Space news dashboard
│  ├─ apod.html          # Daily APOD view
│  ├─ apod_detail.html   # APOD detail page
│  ├─ apodgallery.html   # APOD gallery with filters
│  ├─ margallery.html    # Mars gallery with filters
│  ├─ margallery_detail.html
│  ├─ mygallery.html     # User favourites overview
│  ├─ login.html / register.html
│  └─ ...
├─ static/               # Placeholder for custom CSS/JS if required
├─ requirements.txt      # Python dependencies
└─ users.db              # SQLite datastore (auto-generated)
```

## Getting Started
1. **Clone and enter the project:**
   ```bash
   git clone <repo-url>
   cd space
   ```

2. **(Optional) Create a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # macOS/Linux
   # venv\Scripts\activate  # Windows
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the development server:**
   ```bash
   flask --app app run --debug
   ```

5. Open the browser at **http://127.0.0.1:5000/**.

The SQLite database and required tables are created automatically on first run. Register a user account to unlock saving/favourite functionality.

## Configuration
- **NASA API Keys:** The project includes demo keys in `app.py` and `templates/apod.html`. Replace them with your own keys from https://api.nasa.gov/ for production use. A simple approach is to set environment variables and read them in `app.py` before requests.
- **Spaceflight News API:** Public and requires no key.
- **Timeouts & caching:** The app performs live fetches. Consider adding caching (e.g., file-based or in-memory) if you expect heavy traffic or want to minimise API calls.

## Usage Guide
- **Home (Dashboard):** Browse featured stories, archived headlines, Mars weather, and NEO stats.
- **APOD:** View today’s image, download, and save it to My Gallery (login required). Favourite icons remain grey until saved; once saved they turn the SpaceNews pink tone.
- **APOD Gallery:** Filter by day/month/year and open detail pages. Saved items display the pink heart immediately.
- **Mars Gallery:** Filter by rover, earth date, camera, and sort order. Any combination that returns no imagery surfaces a status banner. Detail pages share the same modal feedback.
- **My Gallery:** Displays all saved APOD and Mars items with quick access to detail and open-image links.

## Data Persistence
- SQLite database `users.db` contains:
  - `users` table for credentials.
  - `user_gallery` table storing favourites with item type (`apod` / `mars`), reference date or URL, title, media URL, and metadata JSON.
- Favourites are checked on each page load so the heart icon state reflects reality even after logout/login cycles.

## Development Notes
- The frontend is pure templates—no bundler required. Styles are embedded for quick iteration.
- Modal feedback is reused across APOD and Mars detail pages to keep UX consistent.
- Mars filters call NASA APIs live; 401/5xx errors fall back to friendly status messages rather than breaking the page.
- Validation and unit tests are not yet included; consider adding pytest suites for API helpers and route behaviour.

## Roadmap Ideas
- Integrate Hugging Face summarisation for news articles per the final-term project pitch.
- Add bulk management (delete/organise) for favourites.
- Implement caching for NASA responses to reduce latency and API usage.
- Introduce theming (light/dark) or additional NASA endpoints (e.g., EPIC Earth imagery).

---

Happy exploring! Feel free to fork and extend SpaceNews for your own astronomical dashboard projects.


