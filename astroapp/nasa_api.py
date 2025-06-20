import os
import requests
from datetime import date, timedelta

NASA_API_KEY = '8MKAxdeLYjdQNRyrh4r07nm7OPx4Q63lJbDTm3JO'

def get_apod():
    try:
        resp = requests.get(f'https://api.nasa.gov/planetary/apod?api_key={NASA_API_KEY}')
        data = resp.json()
        return {
            'title': data.get('title'),
            'url': data.get('url'),
            'media_type': data.get('media_type'),
            'explanation': data.get('explanation'),
            'copyright': data.get('copyright', ''),
        }
    except Exception:
        return None

def get_neos():
    try:
        today = date.today().isoformat()
        resp = requests.get(f'https://api.nasa.gov/neo/rest/v1/feed?start_date={today}&end_date={today}&api_key={NASA_API_KEY}')
        data = resp.json()
        neos_today = data.get('near_earth_objects', {}).get(today, [])
        neos = []
        for n in neos_today[:5]:
            neos.append({
                'name': n.get('name'),
                'url': n.get('nasa_jpl_url'),
                'hazardous': n.get('is_potentially_hazardous_asteroid'),
                'diameter': n['estimated_diameter']['meters']['estimated_diameter_max'] if 'estimated_diameter' in n else None,
                'velocity': n['close_approach_data'][0]['relative_velocity']['kilometers_per_hour'] if n.get('close_approach_data') else None,
                'distance': n['close_approach_data'][0]['miss_distance']['kilometers'] if n.get('close_approach_data') else None,
            })
        return neos
    except Exception:
        return []

def get_solar_events():
    try:
        today = date.today().isoformat()
        week_ago = (date.today() - timedelta(days=7)).isoformat()
        resp = requests.get(f'https://api.nasa.gov/DONKI/CME?startDate={week_ago}&endDate={today}&api_key={NASA_API_KEY}')
        data = resp.json()
        solar = []
        for s in data[-5:]:
            solar.append({
                'start_time': s.get('startTime'),
                'source_location': s.get('sourceLocation'),
                'active_region_num': s.get('activeRegionNum'),
                'note': s.get('note'),
                'type': 'CME',
            })
        return solar
    except Exception:
        return []

def get_celestial_event_data():
    apod = get_apod()
    neos = get_neos()
    solar = get_solar_events()
    return apod, neos, solar 