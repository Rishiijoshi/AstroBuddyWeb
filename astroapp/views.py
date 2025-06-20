from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseRedirect
import datetime
import requests
from timezonefinder import TimezoneFinder
import pytz
import os
from .nasa_api import get_celestial_event_data
from django.contrib.auth.decorators import login_required
from .models import SavedEvent
from django.utils.dateparse import parse_datetime
from django.contrib import messages
from django.urls import reverse
import json
from django.template.loader import render_to_string

# Mock data for celestial events
MOCK_EVENTS = [
    {
        'name': 'Perseid Meteor Shower',
        'datetime': '2024-08-12T22:00:00',
        'visibility': 'Excellent',
        'description': 'Annual meteor shower with up to 100 meteors per hour.'
    },
    {
        'name': 'ISS Pass',
        'datetime': '2024-07-05T19:30:00',
        'visibility': 'Good',
        'description': 'International Space Station visible for 6 minutes.'
    },
    {
        'name': 'Full Moon',
        'datetime': '2024-06-22T21:00:00',
        'visibility': 'Fair',
        'description': 'The moon will be fully illuminated.'
    },
]

# Mock weather data
MOCK_WEATHER = {
    'sky_visibility': 'Good',
    'description': 'Clear skies, perfect for stargazing!'
}

OPENWEATHER_API_KEY = '1df0a608a5c3b6ff0ce36959ae6a8ab4'

# Helper to get weather and astronomy data
def get_weather_and_astronomy(lat, lon):
    weather = None
    astronomy = []
    sky_visibility = 'Unknown'
    weather_desc = ''
    tf = TimezoneFinder()
    try:
        tz_name = tf.timezone_at(lat=float(lat), lng=float(lon))
        tz = pytz.timezone(tz_name) if tz_name else pytz.utc
    except Exception:
        tz = pytz.utc
    def to_local(dtstr):
        try:
            dt_utc = datetime.datetime.fromisoformat(dtstr.replace('Z','+00:00'))
            return dt_utc.astimezone(tz).strftime('%Y-%m-%d %I:%M %p')
        except Exception:
            return dtstr
    try:
        wresp = requests.get(
            f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric'
        ).json()
        if 'weather' in wresp:
            main = wresp['weather'][0]['main']
            desc = wresp['weather'][0]['description']
            weather_desc = desc.capitalize()
            if main in ['Clear']:
                sky_visibility = 'Good'
            elif main in ['Clouds']:
                sky_visibility = 'Cloudy'
            elif main in ['Rain', 'Thunderstorm', 'Drizzle', 'Snow']:
                sky_visibility = 'Poor'
            else:
                sky_visibility = 'Fair'
        weather = {
            'sky_visibility': sky_visibility,
            'description': weather_desc or 'Weather data unavailable.'
        }
    except Exception:
        weather = {'sky_visibility': 'Unknown', 'description': 'Weather unavailable'}
    try:
        sunresp = requests.get(
            f'https://api.sunrise-sunset.org/json?lat={lat}&lng={lon}&formatted=0'
        ).json()
        if sunresp.get('status') == 'OK':
            results = sunresp['results']
            astronomy.append({
                'name': 'Sunrise',
                'datetime': results['sunrise'],
                'localtime': to_local(results['sunrise']),
                'visibility': 'N/A',
                'description': 'The sun rises above the horizon.'
            })
            astronomy.append({
                'name': 'Sunset',
                'datetime': results['sunset'],
                'localtime': to_local(results['sunset']),
                'visibility': 'N/A',
                'description': 'The sun sets below the horizon.'
            })
        moonresp = requests.get(
            f'https://api.openweathermap.org/data/3.0/onecall?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}'
        ).json()
        if 'daily' in moonresp and len(moonresp['daily']) > 0:
            moon_phase = moonresp['daily'][0].get('moon_phase')
            phase_name = 'New Moon'
            if moon_phase is not None:
                if moon_phase == 0 or moon_phase == 1:
                    phase_name = 'New Moon'
                elif 0 < moon_phase < 0.25:
                    phase_name = 'Waxing Crescent'
                elif moon_phase == 0.25:
                    phase_name = 'First Quarter'
                elif 0.25 < moon_phase < 0.5:
                    phase_name = 'Waxing Gibbous'
                elif moon_phase == 0.5:
                    phase_name = 'Full Moon'
                elif 0.5 < moon_phase < 0.75:
                    phase_name = 'Waning Gibbous'
                elif moon_phase == 0.75:
                    phase_name = 'Last Quarter'
                else:
                    phase_name = 'Waning Crescent'
            astronomy.append({
                'name': 'Moon Phase',
                'datetime': '',
                'localtime': '',
                'visibility': 'N/A',
                'description': f'Tonight: {phase_name}'
            })
    except Exception:
        pass
    try:
        issresp = requests.get(
            f'http://api.open-notify.org/iss-pass.json?lat={lat}&lon={lon}'
        ).json()
        if 'response' in issresp:
            for p in issresp['response'][:2]:
                dt = datetime.datetime.utcfromtimestamp(p['risetime']).replace(tzinfo=pytz.utc).isoformat()
                astronomy.append({
                    'name': 'ISS Pass',
                    'datetime': dt,
                    'localtime': to_local(dt),
                    'visibility': 'Good',
                    'description': f'International Space Station visible for {p["duration"]//60} min {p["duration"]%60} sec.'
                })
    except Exception:
        pass
    return weather, astronomy

def landing(request):
    return render(request, 'landing.html')

def get_moon_emoji(phase_name):
    # Unicode moon phase emojis
    mapping = {
        'New Moon': '\U0001F311',
        'Waxing Crescent': '\U0001F312',
        'First Quarter': '\U0001F313',
        'Waxing Gibbous': '\U0001F314',
        'Full Moon': '\U0001F315',
        'Waning Gibbous': '\U0001F316',
        'Last Quarter': '\U0001F317',
        'Waning Crescent': '\U0001F318',
    }
    return mapping.get(phase_name, '\U0001F311')

def get_next_full_moon(now=None):
    # Simple algorithm: next full moon is about every 29.53 days
    # Use OpenWeatherMap moon_phase if available, else estimate
    import math
    if not now:
        now = datetime.datetime.utcnow()
    # Known full moon: 2024-06-22
    last_full = datetime.datetime(2024, 6, 22, 1, 8)
    days_since = (now - last_full).days + (now - last_full).seconds/86400
    cycle = 29.53
    days_to_next = cycle - (days_since % cycle)
    next_full = now + datetime.timedelta(days=days_to_next)
    return next_full

def get_openmeteo_astronomy(lat, lon, tz='auto', date=None):
    """Fetch astronomy data from Open Meteo Astronomy API."""
    if not date:
        date = datetime.date.today().isoformat()
    url = f"https://api.open-meteo.com/v1/astronomy?latitude={lat}&longitude={lon}&timezone={tz}&date={date}"
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def get_moon_details_from_phase(phase_value):
    """Convert moon phase value (0-1) to name and emoji."""
    phase_name = 'New Moon'
    if phase_value is not None:
        if phase_value == 0 or phase_value == 1:
            phase_name = 'New Moon'
        elif 0 < phase_value < 0.25:
            phase_name = 'Waxing Crescent'
        elif phase_value == 0.25:
            phase_name = 'First Quarter'
        elif 0.25 < phase_value < 0.5:
            phase_name = 'Waxing Gibbous'
        elif phase_value == 0.5:
            phase_name = 'Full Moon'
        elif 0.5 < phase_value < 0.75:
            phase_name = 'Waning Gibbous'
        elif phase_value == 0.75:
            phase_name = 'Last Quarter'
        else: # 0.75 < phase_value < 1
            phase_name = 'Waning Crescent'
    return {'name': phase_name, 'emoji': get_moon_emoji(phase_name)}

def dashboard(request):
    lat = request.GET.get('lat')
    lon = request.GET.get('lon')
    city = request.GET.get('city')
    moon_emoji = '\U0001F311'
    moon_phase_name = 'Unknown'
    next_full_moon = None
    stargaze_tip = ''
    countdown = ''
    celestial_apod, celestial_neos, celestial_solar = get_celestial_event_data()
    # If city is missing, reverse geocode
    if (not city or city == 'your location') and lat and lon:
        try:
            geo = requests.get(f'https://api.openweathermap.org/geo/1.0/reverse?lat={lat}&lon={lon}&limit=1&appid={OPENWEATHER_API_KEY}').json()
            if geo and geo[0] and geo[0].get('name'):
                city = geo[0]['name']
            elif geo and geo[0] and geo[0].get('state'):
                city = geo[0]['state']
            elif geo and geo[0] and geo[0].get('country'):
                city = geo[0]['country']
            else:
                city = 'your location'
        except Exception:
            city = 'your location'
    if not city:
        city = 'your location'
    
    events_list = []
    if lat and lon:
        weather, astronomy = get_weather_and_astronomy(lat, lon)
        # Try to get cloud cover from weather API if available
        try:
            wresp = requests.get(
                f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&units=metric'
            ).json()
            if 'clouds' in wresp and 'all' in wresp['clouds']:
                cloud_cover = int(wresp['clouds']['all'])
        except Exception:
            pass
        for event_data in astronomy:
            dt_str = event_data.get('datetime')
            dt_obj = None
            if dt_str:
                try:
                    dt_obj = parse_datetime(dt_str)
                except ValueError:
                    pass
            if dt_obj:
                event_type = event_data['name']
                events_list.append({
                    'id': len(events_list) + 1,
                    'name': event_data['name'],
                    'description': event_data['description'],
                    'datetime': dt_obj,
                    'localtime': event_data.get('localtime', ''),
                    'visibility': event_data.get('visibility', 'Unknown'),
                    'location': city
                })
        # Find moon phase
        for e_data in astronomy:
            if e_data['name'] == 'Moon Phase':
                moon_phase_name = e_data['description'].replace('Tonight: ','')
                moon_emoji = get_moon_emoji(moon_phase_name)
        
        # Next full moon
        next_full = get_next_full_moon()
        next_full_moon = next_full.strftime('%Y-%m-%d %I:%M %p UTC')
        # Countdown
        now = datetime.datetime.utcnow()
        delta = next_full - now
        countdown = f"{delta.days}d {delta.seconds//3600}h {(delta.seconds//60)%60}m"
        # Stargazing tip
        vis = weather.get('sky_visibility','').lower()
        if 'good' in vis:
            stargaze_tip = '🌟 Great night for stargazing!'
        elif 'cloud' in vis:
            stargaze_tip = '☁️ Some clouds, but you might catch a glimpse!'
        elif 'poor' in vis:
            stargaze_tip = '🌧️ Too cloudy for stargazing.'
        else:
            stargaze_tip = '🔭 Check the sky for surprises!'
    else:
        weather = MOCK_WEATHER
        events_list = [] # No mock events from DB for now
        stargaze_tip = '🔭 Enter a location to get real stargazing tips!'
    
    # Initialize saved events variables
    saved_events_qs = []
    saved_events_json = '[]'
    
    if request.user.is_authenticated:
        saved_events_qs = SavedEvent.objects.filter(user=request.user).order_by('event_time')
        saved_events_list = []
        for se in saved_events_qs:
            saved_events_list.append({
                'name': se.event_title,
                'datetime': se.event_time.isoformat()
            })
        saved_events_json = json.dumps(saved_events_list)

    context = {
        'events': events_list,
        'weather': weather,
        'city': city,
        'moon_emoji': moon_emoji,
        'moon_phase_name': moon_phase_name,
        'next_full_moon': next_full_moon,
        'countdown': countdown,
        'stargaze_tip': stargaze_tip,
        'celestial_apod': celestial_apod,
        'celestial_neos': celestial_neos,
        'celestial_solar': celestial_solar,
        'saved_events': saved_events_qs,
        'saved_events_json': saved_events_json,
    }
    return render(request, 'dashboard.html', context)

def about(request):
    return render(request, 'about.html')

@login_required
def save_event(request, event_id):
    if not request.user.is_authenticated:
        messages.info(request, "Sign up to save your events and receive notifications.")
        next_url = request.get_full_path()
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'redirect_url': f"{reverse('users:signup')}?next={next_url}"})
        return redirect(f"{reverse('users:signup')}?next={next_url}")

    event_name = request.GET.get('name', 'Unknown Event')
    event_description = request.GET.get('description', 'No description available')
    event_time_str = request.GET.get('datetime', '')
    location = request.GET.get('location', 'Unknown Location')
    try:
        event_time = parse_datetime(event_time_str) if event_time_str else None
        if not event_time:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'error': 'Invalid event time.'})
            messages.error(request, "Invalid event time.")
            return redirect('astroapp:dashboard')
        saved_event, created = SavedEvent.objects.get_or_create(
            user=request.user,
            event_title=event_name,
            event_time=event_time,
            defaults={
                'event_description': event_description,
                'location': location
            }
        )
        if created:
            msg = "Event saved successfully! You'll be notified 30 minutes before it starts."
        else:
            msg = f"Event '{event_name}' is already saved."
    except Exception as e:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': str(e)})
        messages.error(request, f"Error saving event: {str(e)}")
        next_url = request.GET.get('next')
        if next_url:
            return HttpResponseRedirect(next_url)
        return redirect('astroapp:dashboard')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render the updated saved events sidebar
        saved_events_qs = SavedEvent.objects.filter(user=request.user).order_by('event_time')
        sidebar_html = render_to_string('partials/saved_events_sidebar.html', {'saved_events': saved_events_qs}, request=request)
        return JsonResponse({'success': True, 'message': msg, 'saved_events_html': sidebar_html})

    if created:
        messages.success(request, msg)
    else:
        messages.info(request, msg)
    next_url = request.GET.get('next')
    if next_url:
        return HttpResponseRedirect(next_url)
    return redirect('astroapp:dashboard')

@login_required
def remove_event(request, event_id):
    try:
        event = SavedEvent.objects.get(id=event_id, user=request.user)
        event.delete()
        messages.success(request, "Event removed from your saved list.")
    except SavedEvent.DoesNotExist:
        messages.error(request, "Event not found or you do not have permission to remove it.")
    return redirect('astroapp:dashboard')
