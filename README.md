# AstroBuddy

**AstroBuddy** is a location-based astronomy event tracker. Discover celestial events (like meteor showers, ISS passes, and moon phases) visible from your current location. Minimal, responsive, and easy to use.

## Features
- Landing page with location detection or manual city entry
- Dashboard with upcoming celestial events and sky visibility
- Event details modal and save-to-localStorage ("My Events")
- Responsive design (Bootstrap)
- About page with credits
- Mock data for celestial events and weather (easy to swap for real APIs)

## Tech Stack
- Django (Python) for backend
- HTML/CSS/JavaScript for frontend
- Bootstrap for styling
- NASA API + OpenWeatherMap API (mocked for demo)

## Setup Instructions
1. **Clone the repo** and navigate to the project folder:
   ```
   git clone <repo-url>
   cd AstroBuddy
   ```
2. **Install dependencies** (create a virtual environment recommended):
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   pip install django
   ```
3. **Run migrations:**
   ```
   python manage.py migrate
   ```
4. **Start the development server:**
   ```
   python manage.py runserver
   ```
5. **Open your browser:**
   Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

---

- To use real NASA or weather APIs, update the logic in `astroapp/views.py`.
- For questions or contributions, open an issue or PR! 