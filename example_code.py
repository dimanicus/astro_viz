# astro_calendar.py:
from datetime import datetime, timedelta
import json
from retrograde import find_retrograde_periods
from signs import get_planet_sign, get_sign_changes
from aspects import find_aspect_periods
from moon import get_moon_events

# Define calendar class
class Calendar:
    def __init__(self, start_date, end_date):
        self.start_date = start_date
        self.end_date = end_date
        self.planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'sun']
        self.aspects = [(0, "Conjunction"), (60, "Sextile"), (90, "Square"), (120, "Trine"), (180, "Opposition")]
        self.events = []
        self.moon_events = []

    def add_retrogrades(self):
        retrogrades = {"Retrograde": []}
        for planet in self.planets:
            retrograde_periods = find_retrograde_periods(planet, self.start_date, self.end_date)
            retrogrades["Retrograde"].extend(retrograde_periods)
        self.events.append(retrogrades)

    def add_sign_changes(self):
        sign_changes = {"Sign Changes": []}
        for planet in self.planets:
            sign_change_points = get_sign_changes(planet, self.start_date, self.end_date)
            sign_changes["Sign Changes"].extend(sign_change_points)
        self.events.append(sign_changes)

    def add_aspects(self):
        aspects_dict = {"Aspects": []}
        for i, planet1 in enumerate(self.planets):
            for planet2 in self.planets[i+1:]:
                for angle, name in self.aspects:
                    aspect_periods = find_aspect_periods(planet1, planet2, angle, 5, self.start_date, self.end_date)
                    for period in aspect_periods:
                        aspects_dict["Aspects"].append({
                            'planet1': planet1,
                            'planet2': planet2,
                            'aspect': period['aspect'],
                            'start_date': period['start_time'],
                            'end_date': period['end_time'],
                            'exact_time_utc': period['exact_time'],
                            'description': f"{planet1.capitalize()} in {period['aspect']} with {planet2.capitalize()}"
                        })
        self.events.append(aspects_dict)

    def add_moon_events(self):
        self.moon_events = {"Moon Events": get_moon_events(self.start_date, self.end_date)}

    # The function, that outputs all events from self.events and moon_events in the format
    # of continuous feed without days separation (only time) in chronological order
    def events_feed(self):
        feed = []
        if len(self.events) == 0:
            return None
        
        sign_changes = []
        aspects = []
        retrogrades = []
        for event_type in self.events:
            sign_changes.extend(event_type.get("Sign Changes", []))
            aspects.extend(event_type.get("Aspects", []))
            retrogrades.extend(event_type.get("Retrograde", []))

        # Adding all events to the feed in unified format
        # {"date": <datetime in format YYYY-MM-DD HH:MM; time is 00:00 if absent>, "description": <description of the event>}
        for event in sign_changes:
            feed.append({
                'type': 'point',
                'datetime': f"{event['datetime']}",
                'description': event['description']
            })
        for event in aspects:
            feed.append({
                'type': 'point',
                'datetime': f"{event['exact_time_utc']}",
                'description': event['description']
            })
        for event in retrogrades:
            if "stationary_point" in event:
                feed.append({
                    'type': 'point',
                    'datetime': f"{event['stationary_point']}",
                    'description': f"{event['description']}"
                })

        # Sorting the feed by date
        feed.sort(key=lambda x: x['datetime'])
        return feed
    
    def moon_events_feed(self):
        feed = []
        if len(self.moon_events) == 0:
            return None
        moon_events = self.moon_events["Moon Events"]
        for day in moon_events:
            current_date = datetime.strptime(day['date'], '%Y-%m-%d')
            next_date = (current_date + timedelta(days=1)).strftime('%Y-%m-%d')
            for lunar_day in day["lunar_days"]:
                end_time = f"{day['date']} {lunar_day['end']}:00+00:00" if lunar_day['end'] else f"{next_date} 00:00:00+00:00"
                feed.append({
                    'type': 'period',
                    'datetime': f"{day['date']} {lunar_day['start'] if lunar_day['start'] else '00:00'}:00+00:00",
                    'datetime_start': f"{day['date']} {lunar_day['start'] if lunar_day['start'] else '00:00'}:00+00:00",
                    'datetime_end': end_time,
                    'description': f"{lunar_day['number']} Moon day"
                })
            for change in day['sign_changes']:
                feed.append({
                    'type': 'point',
                    'datetime': f"{change['exact_time']}:00+00:00",
                    'description': change['description']
                })
            for aspect in day['aspects']:
                feed.append({
                    'type': 'point',
                    'datetime': f"{aspect['exact_time']}",
                    'description': f"{aspect['planet1'].capitalize()} in {aspect['aspect']} with {aspect['planet2'].capitalize()}"
                })
            for phase in day['phases']:
                feed.append({
                    'type': 'point',
                    'datetime': f"{phase['time']}:00+00:00",
                    'description': phase['description']
                })
        # Merging lunar days periods; if two consecutive periods have the same description, merge them, deleting datetimes with None
        feed.sort(key=lambda x: (x['description'], x['datetime']))
        i = 0
        while i < len(feed) - 1:
            if (feed[i]['type'] == 'period' and feed[i+1]['type'] == 'period' and feed[i]['description'] == feed[i+1]['description']):
                # Merge the periods
                if feed[i]['datetime_end'] == feed[i+1]['datetime_start']:
                    feed[i]['datetime_end'] = feed[i+1]['datetime_end']
                    feed.pop(i+1)
                else:
                    i += 1
            else:
                i += 1

        # Sorting the feed by date
        feed.sort(key=lambda x: x['datetime'])
        return feed
        

# --- Main execution ---
start_date = datetime(2024, 12, 1)
end_date = datetime(2026, 2, 1)
calendar = Calendar(start_date, end_date)
calendar.add_moon_events()
calendar.add_retrogrades()
calendar.add_aspects()
calendar.add_sign_changes()

# Save as JSON
#with open('astrological_calendar.json', 'w') as f:
#    json.dump(calendar.events, f, default=str)
with open('events_feed.json', 'w') as f:
    json.dump(calendar.events_feed(), f, default=str)

# Save moon events in separate files
#with open('moon_events.json', 'w') as f:
#    json.dump(calendar.moon_events, f, default=str)
with open('moon_events_feed.json', 'w') as f:
    json.dump(calendar.moon_events_feed(), f, default=str)

# utility.py:
from datetime import datetime, timedelta, time
from skyfield.api import load, load_file, utc
from skyfield.framelib import ICRS, ecliptic_frame
import numpy as np

# Load the ephemeris data
ts = load.timescale()
eph = load_file('de442.bsp')

def format_datetime(dt):
    """Ensure consistent datetime formatting"""
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=utc)
    return dt.strftime('%Y-%m-%d %H:%M')

def ensure_datetime(dt):
    """Convert string to datetime if needed and ensure UTC timezone"""
    if isinstance(dt, str):
        dt = datetime.strptime(dt, '%Y-%m-%d %H:%M')
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=utc)
    return dt

def calculate_ecliptic_velocity(planet_obj, date):
    """Calculate planet's instantaneous ecliptic angular velocity in degrees per day."""
    # Ensure the datetime is timezone-aware (using Skyfield's utc if needed)
    if date.tzinfo is None:
        from skyfield.api import utc
        date = date.replace(tzinfo=utc)
    t = ts.from_datetime(date)
    earth = eph['earth']
    
    # Obtain the ecliptic spherical coordinates and their instantaneous rates.
    # Using the ecliptic_frame ensures that the longitude we get is relative to the ecliptic.
    lat, lon, distance, lat_rate, lon_rate, _ = earth.at(t).observe(planet_obj).apparent().frame_latlon_and_rates(ecliptic_frame)
    
    # The returned lon_rate is an AngleRate, so we can directly obtain its value.
    velocity = lon_rate.degrees.per_day  # This value is positive if the ecliptic longitude is increasing, negative if decreasing.
    return velocity

def calculate_velocity(planet_obj, date, time_window=30):
    """Calculate planet's apparent velocity in degrees per day"""
    earth = eph['earth']
    date = ensure_datetime(date)
    
    # Get position at the current time
    t = ts.from_datetime(date)
    pos_rates = earth.at(t).observe(planet_obj).apparent().frame_latlon_and_rates(ICRS)
    
    ra, dec, distance, ra_rate, dec_rate, distance_rate = pos_rates
    
    # Apply spherical trigonometry correction
    ra_adjusted = ra_rate.degrees.per_day * np.cos(dec.radians)
    
    # Calculate velocity magnitude
    velocity_magnitude = np.sqrt(ra_adjusted**2 + dec_rate.degrees.per_day**2)
    
    # Determine sign based on ecliptic longitude change
    # Check position on consecutive days to determine direction
    t1 = ts.from_datetime(date - timedelta(hours=12))
    t2 = ts.from_datetime(date + timedelta(hours=12))
    
    pos1 = earth.at(t1).observe(planet_obj).ecliptic_latlon()[1].degrees
    pos2 = earth.at(t2).observe(planet_obj).ecliptic_latlon()[1].degrees
    
    # Handle cases where longitude crosses 0/360 degrees
    if pos1 > 270 and pos2 < 90:
        # Crossed from 360 to 0
        pos2 += 360
    elif pos1 < 90 and pos2 > 270:
        # Crossed from 0 to 360
        pos1 += 360
    
    # If longitude is decreasing, planet is retrograde (negative velocity)
    if pos1 > pos2:
        return -velocity_magnitude
    else:
        return velocity_magnitude

# Planet mapping
def get_planet_object(planet_name):
    # Map from lowercase names to proper Skyfield objects
    planet_map = {
        'mercury': eph['mercury barycenter'],
        'venus': eph['venus barycenter'], 
        'mars': eph['mars barycenter'],
        'jupiter': eph['jupiter barycenter'],
        'saturn': eph['saturn barycenter'],
        'uranus': eph['uranus barycenter'],
        'neptune': eph['neptune barycenter'],
        'pluto': eph['pluto barycenter'],
        'moon': eph['moon'],
        'sun': eph['sun']
    }
    
    return planet_map.get(planet_name.lower())


# signs.py:
from skyfield.api import load, load_file, utc
from datetime import datetime, timedelta

# Load the ephemeris data
ts = load.timescale()
eph = load_file('de442.bsp')

from utility import format_datetime, ensure_datetime

PLANET_STEP_SIZES = {
        'mercury': timedelta(days=1),
        'venus': timedelta(days=2),
        'mars': timedelta(days=5),
        'jupiter': timedelta(days=30),
        'saturn': timedelta(days=60),
        'uranus': timedelta(days=120),
        'neptune': timedelta(days=180),
        'pluto': timedelta(days=240),
        'sun': timedelta(days=1),
        'moon': timedelta(hours=6)  # Moon changes signs every 2-3 days
    }
SIGNS = ["Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo", 
             "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"]

# Import utility functions after initializing skyfield
from utility import get_planet_object

# Function to calculate the current sign of the planet
def get_planet_sign(planet, date):
    # Calculate ecliptic longitude
    earth = eph['earth']
    planet_obj = get_planet_object(planet)
    time = ts.utc(date.year, date.month, date.day, date.hour, date.minute)
    
    # Get astrological position
    pos = earth.at(time).observe(planet_obj)
    ecliptic = pos.ecliptic_latlon()
    lon = ecliptic[1].degrees
    
    # Determine zodiac sign (each sign is 30 degrees)
    sign_num = int(lon / 30)
    
    return SIGNS[sign_num]

# Function to get precise sign changes for a planet within a date range
def get_sign_changes(planet, start_date, end_date):
    """
    Find all sign changes for a planet within the given date range with minute precision.
    
    Args:
        planet (str): Name of the planet
        start_date (datetime): Start date for the search
        end_date (datetime): End date for the search
        
    Returns:
        list: List of dictionaries containing datetime, old_sign, new_sign, and description for each sign change
    """
    sign_changes = []
    start_date = ensure_datetime(start_date)
    end_date = ensure_datetime(end_date)
    
    # Get appropriate step size for the planet
    initial_step = PLANET_STEP_SIZES.get(planet.lower(), timedelta(days=1))
    
    # First pass: Check with adaptive step size to find potential sign change days
    current_date = start_date
    previous_sign = get_planet_sign(planet, current_date)
    potential_change_days = []
    
    while current_date <= end_date:
        current_sign = get_planet_sign(planet, current_date)
        
        if current_sign != previous_sign:
            # Found a day with sign change, add the previous date for detailed check
            potential_change_days.append((current_date - initial_step, current_date))
        
        previous_sign = current_sign
        current_date += initial_step
    
    # Second pass: For each potential period, narrow down to day precision
    for start_period, end_period in potential_change_days:
        start_sign = get_planet_sign(planet, start_period)
        end_sign = get_planet_sign(planet, end_period)
        
        if start_sign == end_sign:
            continue  # No sign change in this period
            
        # Binary search to find the exact transition point
        search_start = start_period
        search_end = end_period
        
        # Continue narrowing down until we reach minute precision
        while (search_end - search_start) > timedelta(minutes=1):
            mid_time = search_start + (search_end - search_start) / 2
            mid_time = mid_time.replace(second=0, microsecond=0)  # Round to minute
            
            mid_sign = get_planet_sign(planet, mid_time)
            
            if mid_sign == start_sign:
                search_start = mid_time
            else:
                search_end = mid_time
        
        # At this point, search_start has the last time with start_sign
        # and search_end has the first time with end_sign (within 1 minute)
        
        # Final check to get the exact minute
        transition_time = search_end
        old_sign = start_sign
        new_sign = end_sign
        
        print(transition_time)  # Debug print
        
        sign_changes.append({
            'planet': planet,
            'datetime': format_datetime(transition_time),
            'old_sign': old_sign,
            'new_sign': new_sign,
            'description': f"{planet.capitalize()} enters {new_sign}"
        })
    
    return sign_changes

# aspects.py:
from skyfield.api import load, load_file, utc
from datetime import datetime, timedelta
import numpy as np

# Load the ephemeris data
ts = load.timescale()
eph = load_file('de442.bsp')

# Import utility functions after initializing skyfield
from utility import get_planet_object

# Function to calculate the aspects between two planets
def find_aspect_periods(planet1, planet2, aspect_angle, orb, start_date, end_date):
    """
    Find periods when two planets are in a specific aspect within given orb.
    
    Parameters:
    - planet1, planet2: planet names
    - aspect_angle: desired angle in degrees
    - orb: maximum deviation from exact aspect in degrees
    - start_date, end_date: datetime objects defining the period to check
    
    Returns:
    - List of dictionaries with aspect periods and exact aspect times
    """
    # Get planet objects
    planet1_obj = get_planet_object(planet1)
    planet2_obj = get_planet_object(planet2)
    earth = eph['earth']
    # Debug info
    print(f"Detecting {planet1.capitalize()} and {planet2.capitalize()} aspects within {orb}° of {aspect_angle}°")
    
    # Create timeline with 4-hour intervals
    delta_hours = int((end_date - start_date).total_seconds() / 3600)
    times = []
    angles = []
    
    # Calculate angles throughout the period
    for hour in range(0, delta_hours, 4):
        current_time = start_date + timedelta(hours=hour)
        t = ts.utc(current_time.year, current_time.month, current_time.day, 
                   current_time.hour, current_time.minute)
        
        # Get positions
        pos1 = earth.at(t).observe(planet1_obj).ecliptic_latlon()[1].degrees
        pos2 = earth.at(t).observe(planet2_obj).ecliptic_latlon()[1].degrees
        
        # Calculate angular distance
        angle = (pos1 - pos2) % 360
        if angle > 180:
            angle = 360 - angle
            
        # Store time and angle
        times.append(t)
        angles.append(angle)
    
    # Find periods when planets are within orb of aspect
    aspect_periods = []
    in_aspect = False
    start_idx = None
    # Debug info
    print(f"Finding periods when planets are within orb of aspect...")
    
    for i in range(len(angles)):
        is_in_orb = abs(angles[i] - aspect_angle) <= orb
        
        # Start of a new aspect period
        if is_in_orb and not in_aspect:
            in_aspect = True
            start_idx = i
        
        # End of an aspect period
        elif not is_in_orb and in_aspect:
            in_aspect = False
            
            # Find the exact aspect time within this period
            closest_idx = start_idx + np.argmin([abs(angles[j] - aspect_angle) 
                                               for j in range(start_idx, i)])
            
            # Calculate more precise time for exact aspect
            print(f"Detected end of aspect period for {planet1.capitalize()} and {planet2.capitalize()}, calculating exact time close to {times[closest_idx].utc_strftime('%Y-%m-%d %H:%M:%S')}...")
            exact_time = find_exact_aspect_time(planet1_obj, planet2_obj, 
                                               times[closest_idx], aspect_angle)
            if exact_time is None:
                print(f"Exact aspect time calculation failed for {planet1.capitalize()} and {planet2.capitalize()}, skipping...")
                continue

            aspect_periods.append({
                'start_time': times[start_idx].utc_datetime(),
                'end_time': times[i-1].utc_datetime(),
                'exact_time': exact_time,
                'planet1': planet1,
                'planet2': planet2,
                'aspect': get_aspect_name(aspect_angle)
            })
    
    # Check if we ended the year in an aspect
    if in_aspect:
        closest_idx = start_idx + np.argmin([abs(angles[j] - aspect_angle) 
                                           for j in range(start_idx, len(angles))])
        
        print(f"End of period aspect check...")
        exact_time = find_exact_aspect_time(planet1_obj, planet2_obj, 
                                           times[closest_idx], aspect_angle)
        
        if exact_time:
            aspect_periods.append({
                'start_time': times[start_idx].utc_datetime(),
                'end_time': times[-1].utc_datetime(),
                'exact_time': exact_time,
                'planet1': planet1,
                'planet2': planet2,
                'aspect': get_aspect_name(aspect_angle)
            })
    
    # Remove duplicate aspects (same planets, same aspect, within 24 hours)
    cleaned_periods = []
    seen_aspects = set()
    
    print("Removing potential duplicates...")
    for period in sorted(aspect_periods, key=lambda x: x['exact_time']):
        aspect_key = (period['planet1'], period['planet2'], period['aspect'])
        exact_time = period['exact_time']
        
        # Check if we've seen this aspect recently
        is_duplicate = False
        for prev_time in seen_aspects:
            if (aspect_key == prev_time[0] and 
                abs((exact_time - prev_time[1]).total_seconds()) < 24 * 3600):
                is_duplicate = True
                break
        
        if not is_duplicate:
            cleaned_periods.append(period)
            seen_aspects.add((aspect_key, exact_time))
    
    print("Finished aspect detection!")
    return cleaned_periods

def calculate_optimal_window(planet1_obj, planet2_obj, reference_time):
    """
    Calculate the optimal search window size based on the rate of angle change
    between two planets at a specific time.
    
    Parameters:
    - planet1_obj, planet2_obj: skyfield planet objects
    - reference_time: datetime object for when to measure the rate of change
    
    Returns:
    - window_hours: optimal window size in hours
    """
    earth = eph['earth']
    
    # Convert reference time to skyfield time
    t_ref = ts.utc(reference_time)
    
    # Calculate angle at reference time
    pos1_ref = earth.at(t_ref).observe(planet1_obj).ecliptic_latlon()[1].degrees
    pos2_ref = earth.at(t_ref).observe(planet2_obj).ecliptic_latlon()[1].degrees
    angle_ref = (pos1_ref - pos2_ref) % 360
    if angle_ref > 180:
        angle_ref = 360 - angle_ref
    print(f"Angle at reference time: {angle_ref:.4f}°")
    
    # Calculate angle 1 hour later
    t_later = ts.utc(reference_time + timedelta(hours=1))
    pos1_later = earth.at(t_later).observe(planet1_obj).ecliptic_latlon()[1].degrees
    pos2_later = earth.at(t_later).observe(planet2_obj).ecliptic_latlon()[1].degrees
    angle_later = (pos1_later - pos2_later) % 360
    if angle_later > 180:
        angle_later = 360 - angle_later
    
    # Calculate rate of change in degrees per hour
    rate_of_change = abs(angle_later - angle_ref)
    
    # Handle cases where the angle crosses 0/180 boundary
    if rate_of_change > 180:
        rate_of_change = 360 - rate_of_change
    
    print(f"Rate of angle change: {rate_of_change:.4f}° per hour")
    
    # Determine window size based on rate of change
    # Slower rate = larger window, faster rate = smaller window
    if rate_of_change < 0.01:
        window_hours = 168  # Very slow: 7 days
    elif rate_of_change < 0.05:
        window_hours = 120  # Slow: 5 days
    elif rate_of_change < 0.1:
        window_hours = 96   # Moderately slow: 4 days
    elif rate_of_change < 0.5:
        window_hours = 72   # Medium slow: 3 days
    elif rate_of_change < 1:
        window_hours = 48   # Medium: 2 days
    elif rate_of_change < 5:
        window_hours = 24   # Medium fast: 1 day
    elif rate_of_change < 10:
        window_hours = 12   # Fast: 12 hours
    else:
        window_hours = 6    # Very fast: 6 hours
    
    # Ensure minimum window size
    window_hours = max(window_hours, 6)
    
    print(f"Optimal window size: {window_hours} hours")
    return window_hours

def refine_aspect_time_with_interpolation(planet1_obj, planet2_obj, best_time, aspect_angle, hours_range=3):
    """
    Refine the aspect time using polynomial interpolation.
    
    Parameters:
    - planet1_obj, planet2_obj: skyfield planet objects
    - best_time: best approximation time from binary search
    - aspect_angle: the desired aspect angle in degrees
    - hours_range: range of hours to sample around best_time
    
    Returns:
    - refined datetime object with more precise aspect time
    """
    print(f"Refining aspect time with polynomial interpolation...")
    earth = eph['earth']
    
    # Sample points around the best time
    sample_times = []
    sample_angles = []
    
    # Create 7 sample points centered around best_time
    for hour_offset in [-hours_range, -hours_range/2, -hours_range/4, 0, hours_range/4, hours_range/2, hours_range]:
        sample_datetime = best_time + timedelta(hours=hour_offset)
        t = ts.utc(sample_datetime)
        
        # Get positions
        pos1 = earth.at(t).observe(planet1_obj).ecliptic_latlon()[1].degrees
        pos2 = earth.at(t).observe(planet2_obj).ecliptic_latlon()[1].degrees
        
        # Calculate angular distance
        angle = (pos1 - pos2) % 360
        if angle > 180:
            angle = 360 - angle
            
        sample_times.append(sample_datetime.timestamp())
        sample_angles.append(angle)
    
    # Convert to numpy arrays for interpolation
    x = np.array(sample_times)
    y = np.array(sample_angles)
    
    # Normalize x values for better numerical stability
    x_min = np.min(x)
    x = x - x_min
    
    # Fit a polynomial of degree 3 (cubic)
    coeffs = np.polyfit(x, y, 3)
    poly = np.poly1d(coeffs)
    
    # Find the roots of the derivative to locate extrema
    deriv = poly.deriv()
    critical_points = deriv.roots
    
    # Filter out complex roots and points outside our sample range
    real_critical_points = [point.real for point in critical_points if abs(point.imag) < 1e-10 and 0 <= point <= max(x)]
    
    # Add endpoints to check
    points_to_check = [0, max(x)] + real_critical_points
    
    # Find the point where the polynomial is closest to the aspect angle
    best_x = None
    min_diff = float('inf')
    
    # Check a fine grid of points between min and max x
    grid_points = np.linspace(0, max(x), 1000)
    for point in grid_points:
        angle_at_point = poly(point)
        diff = abs(angle_at_point - aspect_angle)
        if diff < min_diff:
            min_diff = diff
            best_x = point
    
    # Convert back to datetime
    if best_x is not None:
        best_timestamp = best_x + x_min
        refined_time = datetime.utcfromtimestamp(best_timestamp)
        
        # Calculate the actual angle at this time for verification
        t_refined = ts.utc(refined_time.year, refined_time.month, refined_time.day,
                           refined_time.hour, refined_time.minute, refined_time.second)
        pos1 = earth.at(t_refined).observe(planet1_obj).ecliptic_latlon()[1].degrees
        pos2 = earth.at(t_refined).observe(planet2_obj).ecliptic_latlon()[1].degrees
        actual_angle = (pos1 - pos2) % 360
        if actual_angle > 180:
            actual_angle = 360 - actual_angle
            
        print(f"Interpolation found time: {refined_time}")
        print(f"Angle at interpolated time: {actual_angle:.6f}°")
        print(f"Interpolation angle difference: {abs(actual_angle - aspect_angle):.6f}°")
        
        # Round to nearest minute
        refined_time = refined_time.replace(second=0, microsecond=0)
        return refined_time
    else:
        print("Interpolation failed to find a better time")
        return best_time.replace(second=0, microsecond=0)

def find_exact_aspect_time(planet1_obj, planet2_obj, approx_time, aspect_angle):
    """
    Find the exact time when two planets form the specified aspect angle.
    Uses binary search to find the precise time down to the minute.
    
    Parameters:
    - planet1_obj, planet2_obj: skyfield planet objects
    - approx_time: approximate time when the aspect occurs
    - aspect_angle: the desired aspect angle in degrees
    
    Returns:
    - datetime object with the exact aspect time
    """
    print(f"Finding exact aspect time for two planets aspect...")
    print(f"Approximate time: {approx_time.utc_strftime('%Y-%m-%d %H:%M:%S')}, aspect angle: {aspect_angle}")
    earth = eph['earth']

    approx_datetime = approx_time.utc_datetime()
    window_hours = calculate_optimal_window(planet1_obj, planet2_obj, approx_datetime)
    
        # Set up binary search with initial window
    start_time = approx_datetime - timedelta(hours=window_hours/2)
    end_time = approx_datetime + timedelta(hours=window_hours/2)
    
    def get_angle_at_time(t):
        t_sky = ts.utc(t)
        pos1 = earth.at(t_sky).observe(planet1_obj).ecliptic_latlon()[1].degrees
        pos2 = earth.at(t_sky).observe(planet2_obj).ecliptic_latlon()[1].degrees
        angle = (pos1 - pos2) % 360
        return angle if angle <= 180 else 360 - angle
    
    # Calculate angles at window boundaries and midpoint
    angle_start = get_angle_at_time(start_time)
    angle_mid = get_angle_at_time(approx_datetime)
    angle_end = get_angle_at_time(end_time)
    
    # Check if we need to expand the window by looking at angle progression
    if abs(angle_mid - aspect_angle) > abs(angle_start - aspect_angle) and \
       abs(angle_mid - aspect_angle) > abs(angle_end - aspect_angle):
        print(f"Expanding search window as aspect appears to be outside initial window...")
        start_time = approx_datetime - timedelta(hours=window_hours)
        end_time = approx_datetime + timedelta(hours=window_hours)
        # Recalculate boundary angles for expanded window
        angle_start = get_angle_at_time(start_time)
        angle_end = get_angle_at_time(end_time)
    
    # If the initial approximation is extremely close (within 0.001 degrees),
    # still perform binary search but with a smaller window to refine the result
    if abs(angle_mid - aspect_angle) < 0.001:
        print(f"Initial approximation is extremely close to exact aspect ({abs(angle_mid - aspect_angle):.6f}°)")
        # Use a smaller window centered on the approximate time
        start_time = approx_datetime - timedelta(hours=3)
        end_time = approx_datetime + timedelta(hours=3)
        angle_start = get_angle_at_time(start_time)
        angle_end = get_angle_at_time(end_time)
    
    # Track best approximation
    best_time = approx_datetime  # Initialize with approximate time instead of None
    min_angle_diff = abs(angle_mid - aspect_angle)
    
    # Binary search down to minute precision
        # Binary search down to minute precision
    print("Starting binary search phase...")
    
    while (end_time - start_time).total_seconds() > 60:  # Stop at 1-minute precision
        mid_time = start_time + (end_time - start_time) / 2
        t = ts.utc(mid_time)
        
        # Get positions
        pos1 = earth.at(t).observe(planet1_obj).ecliptic_latlon()[1].degrees
        pos2 = earth.at(t).observe(planet2_obj).ecliptic_latlon()[1].degrees
        
        # Calculate angular distance
        angle = (pos1 - pos2) % 360
        if angle > 180:
            angle = 360 - angle
        
        # Track best approximation
        angle_diff = abs(angle - aspect_angle)
        if angle_diff < min_angle_diff:
            min_angle_diff = angle_diff
            best_time = mid_time
        
        # Determine if angles increase or decrease from start to end
        angles_increasing = angle_end > angle_start
        
        if (angles_increasing and angle < aspect_angle) or (not angles_increasing and angle > aspect_angle):
            # If angles increase and current < target, search right half
            # If angles decrease and current > target, search right half
            start_time = mid_time
        else:
            # Otherwise search left half
            end_time = mid_time
    
    print(f"End of binary search, best approximation: {best_time}")
    print(f"Final angle difference: {min_angle_diff:.6f}°")


    refined_time = refine_aspect_time_with_interpolation(planet1_obj, planet2_obj, best_time, aspect_angle)
    refined_time_utc = refined_time.replace(tzinfo=utc)
    refined_angle = get_angle_at_time(refined_time_utc)
    refined_diff = abs(refined_angle - aspect_angle)

    if refined_diff > 1 and min_angle_diff > 1:
        print(f"Aspect rejected: angle difference is too large: {refined_diff:.6f}° > 1°")
        return None

    if refined_diff < min_angle_diff:
        final_time = refined_time
        print(f"Using interpolation refined time: {final_time}")
    else:
        final_time = best_time.replace(second=0, microsecond=0)
        print(f"Using binary search best approximation: {final_time}")
        
    return datetime(final_time.year, final_time.month, final_time.day,
                    final_time.hour, final_time.minute)

def get_aspect_name(angle):
    """Convert aspect angle to named aspect"""
    aspects = {
        0: "Conjunction",
        60: "Sextile",
        90: "Square",
        120: "Trine",
        180: "Opposition"
    }
    
    # Find the closest standard aspect
    closest_aspect = min(aspects.keys(), key=lambda x: abs(x - angle))
    
    # Return the aspect name if it's within 1 degree of standard angle
    if abs(closest_aspect - angle) <= 1:
        return aspects[closest_aspect]
    else:
        return f"{angle}° Aspect"
    
# moon.py:
from datetime import datetime, timedelta
import math
from skyfield.api import load, load_file, utc
from skyfield.almanac import moon_phases, moon_phase
import numpy as np

# Load the ephemeris data
ts = load.timescale()
eph = load_file('de442.bsp')

# Import utility functions
from utility import get_planet_object, format_datetime, ensure_datetime
from signs import get_sign_changes, get_planet_sign
from aspects import find_aspect_periods

def get_lunar_day(t, earth, moon, sun):
    """
    Calculate the lunar day (1-30) for the given time.
    Uses elongation angle and phase information to determine the correct lunar day.
    """
    # Calculate elongation angle
    elong = earth.at(t).observe(moon).separation_from(earth.at(t).observe(sun)).degrees
    
    # Get moon phase information
    phase_angle = moon_phase(eph, t)
    
    # Convert to lunar age (0-29.53 days)
    lunar_age = (elong / 360) * 29.53
    
    # Determine if waxing or waning based on phase_angle
    # Phase angle increases from 0° to 180° (waxing) then decreases from 180° to 360° (waning)
    is_waxing = phase_angle.degrees <= 180
    
    # Calculate lunar day (1-30)
    if is_waxing:
        # Days 1-15 (New Moon to Full Moon)
        lunar_day = 1 + int((phase_angle.degrees / 180) * 15)  # Changed to 15
    else:
        # Days 16-30 (Full Moon to New Moon)
        lunar_day = 16 + int(((phase_angle.degrees - 180) / 180) * 15)  # Changed to 15
    
    # Handle edge cases
    if lunar_day < 1:
        lunar_day = 1
    elif lunar_day > 30:
        lunar_day = 30
        
    return lunar_day

def calculate_lunar_days(start_date, end_date):
    """
    Calculate lunar days for the given period.
    
    Parameters:
    - start_date, end_date: datetime objects defining the period to check
    
    Returns:
    - List of dictionaries with lunar days for each calendar day
    """
    print("Calculating lunar days...") # for debugging
    # Ensure dates are datetime objects with UTC timezone
    start_date = ensure_datetime(start_date)
    end_date = ensure_datetime(end_date)
    delta_days = (end_date - start_date).days + 1
    
    # Initialize result list
    lunar_days_list = []
    
    # Get earth and moon objects
    earth = eph['earth']
    moon = eph['moon']
    sun = eph['sun']
    
    # Process each calendar day
    for day_offset in range(delta_days):
        current_date = start_date + timedelta(days=day_offset)
        day_start = current_date.replace(hour=0, minute=0, second=0)
        day_end = (current_date + timedelta(days=1)).replace(hour=0, minute=0, second=0)
        
        # Sample the day at hourly intervals to catch transitions
        check_times = [day_start + timedelta(hours=h) for h in range(25)]
        
        # Track transitions
        transitions = []
        prev_lunar_day = None
        
        for check_time in check_times:
            t = ts.utc(check_time)
            lunar_day = get_lunar_day(t, earth, moon, sun)
            
            if prev_lunar_day is not None and lunar_day != prev_lunar_day:
                # Found a transition, find the exact time
                transition_time = find_lunar_day_transition(
                    check_time - timedelta(hours=1), 
                    check_time,
                    prev_lunar_day, 
                    lunar_day, 
                    earth, moon, sun
                )
                
                transitions.append({
                    "time": transition_time,
                    "from": prev_lunar_day,
                    "to": lunar_day
                })
            
            prev_lunar_day = lunar_day
        
        # Format the lunar days for this calendar day
        lunar_days = []
        
        # If no transitions, just use the lunar day at noon
        if not transitions:
            noon_time = current_date.replace(hour=12, minute=0, second=0)
            t = ts.utc(noon_time)
            lunar_day = get_lunar_day(t, earth, moon, sun)
            
            lunar_days.append({
                "number": lunar_day,
                "start": None,
                "end": None
            })
        else:
            # Handle multiple transitions within a day
            # First, get the lunar day at the start of the day
            t_start = ts.utc(day_start)
            start_lunar_day = get_lunar_day(t_start, earth, moon, sun)
            
            # Add the first lunar day (from day start to first transition)
            if transitions:
                lunar_days.append({
                    "number": start_lunar_day,
                    "start": None,
                    "end": format_datetime(transitions[0]["time"]).split(' ')[1]
                })
            
            # Add transitions
            for i, transition in enumerate(transitions):
                end_time = None
                if i < len(transitions) - 1:
                    end_time = format_datetime(transitions[i+1]["time"]).split(' ')[1]
                
                lunar_days.append({
                    "number": transition["to"],
                    "start": format_datetime(transition["time"]).split(' ')[1],
                    "end": end_time
                })
        
        # Add to result list
        lunar_days_list.append({
            "date": format_datetime(current_date).split(' ')[0],
            "lunar_days": lunar_days
        })
    
    print("Done calculating lunar days.\n")
    return lunar_days_list

def find_lunar_day_transition(start_time, end_time, from_day, to_day, earth, moon, sun, precision_minutes=1):
    """
    Find the precise time when the lunar day changes using binary search.
    
    Parameters:
    - start_time: datetime before transition
    - end_time: datetime after transition
    - from_day: lunar day before transition
    - to_day: lunar day after transition
    - precision_minutes: precision of search in minutes
    
    Returns:
    - datetime object of the transition
    """
    # Binary search for transition point
    while (end_time - start_time).total_seconds() > precision_minutes * 60:
        mid_time = start_time + (end_time - start_time) / 2
        t_mid = ts.utc(mid_time)
        
        # Calculate lunar day at mid point
        mid_lunar_day = get_lunar_day(t_mid, earth, moon, sun)
        
        # Adjust search window
        if mid_lunar_day == from_day:
            start_time = mid_time
        else:
            end_time = mid_time
    
    # Return the transition time
    return start_time + (end_time - start_time) / 2

def find_sign_change_time(planet, date, hour, old_sign, new_sign, precision_minutes=5):
    """
    Find the precise time when a planet changes signs.
    
    Parameters:
    - planet: planet name
    - date: base date
    - hour: approximate hour of transition
    - old_sign: sign before transition
    - new_sign: sign after transition
    - precision_minutes: precision of search in minutes
    
    Returns:
    - datetime object of the transition
    """
    # Set up search window
    start_time = date.replace(hour=hour, minute=0, second=0)
    end_time = date.replace(hour=hour, minute=59, second=59)
    
    # Binary search for transition point
    while (end_time - start_time).total_seconds() > precision_minutes * 60:
        mid_time = start_time + (end_time - start_time) / 2
        mid_sign = get_planet_sign(planet, mid_time)
        
        # Adjust search window
        if mid_sign == old_sign:
            start_time = mid_time
        else:
            end_time = mid_time
    
    # Return the transition time
    return start_time + (end_time - start_time) / 2

def get_moon_sign_changes(start_date, end_date):
    """
    Get moon sign changes for the given period.
    
    Parameters:
    - start_date, end_date: datetime objects defining the period to check
    
    Returns:
    - List of dictionaries with moon sign changes for each calendar day
    """
    print("Calculating Moon sign changes...") # for debugging
    # Ensure dates are datetime objects with UTC timezone
    start_date = ensure_datetime(start_date)
    end_date = ensure_datetime(end_date)
    
    # Calculate number of days in the period
    delta_days = (end_date - start_date).days + 1
    
    # Initialize result list
    sign_changes_list = []
    sign_changes = get_sign_changes('moon', start_date, end_date)
    
    # Process each calendar day
    for sign_change in sign_changes:
        sign_changes_list.append({
            "date": format_datetime(sign_change['datetime']).split(' ')[0],
            "exact_time": format_datetime(sign_change['datetime']),
            "description": sign_change['description']
        })
    
    print("Done calculating Moon sign changes.\n")
    return sign_changes_list

def get_moon_aspects(start_date, end_date):
    """
    Get moon aspects with other planets for the given period.
    
    Parameters:
    - start_date, end_date: datetime objects defining the period to check
    
    Returns:
    - List of dictionaries with moon aspects for each calendar day
    """
    print("Calculating Moon aspects...") # for debugging
    # Ensure dates are datetime objects with UTC timezone
    start_date = ensure_datetime(start_date)
    end_date = ensure_datetime(end_date)
    
    # Calculate number of days in the period
    delta_days = (end_date - start_date).days + 1
    
    # Initialize result list
    aspects_list = []
    
    # Get list of planets (excluding moon)
    planets = ['mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'pluto', 'sun']
    major_aspects = [0, 60, 90, 120, 180]  # Conjunction, Sextile, Square, Trine, Opposition
    
    # Process each calendar day
    for day_offset in range(delta_days):
        current_date = start_date + timedelta(days=day_offset)
        next_date = current_date + timedelta(days=1)
        
        # Find all aspects for this day
        day_aspects = []
        
        for planet in planets:
            for angle in major_aspects:
                # Find aspects between moon and planet
                aspects = find_aspect_periods('moon', planet, angle, 2, current_date, next_date)
                day_aspects.extend(aspects)
        # Remove cross-day duplicates
        filtered_day_aspects = []
        for aspect in day_aspects:
            exact_time = aspect['exact_time']
            exact_date = exact_time.date()
            current_day = current_date.date()
            if exact_date == current_day:
                filtered_day_aspects.append(aspect)
        
        # Add to result list if there were aspects
        if filtered_day_aspects:
            aspects_list.append({
                "date": format_datetime(current_date).split(' ')[0],
                "aspects": filtered_day_aspects
            })
        else:
            aspects_list.append({
                "date": format_datetime(current_date).split(' ')[0],
                "aspects": []
            })
    
    print("Done calculating Moon aspects.\n")
    return aspects_list

def get_moon_phases(start_date, end_date):
    """
    Get moon phases for the given period.
    
    Parameters:
    - start_date, end_date: datetime objects defining the period to check
    
    Returns:
    - List of dictionaries with moon phases for each calendar day
    """
    print("Calculating Moon phases...") # for debugging
    # Ensure dates are datetime objects with UTC timezone
    start_date = ensure_datetime(start_date)
    end_date = ensure_datetime(end_date)
    
    # Calculate number of days in the period
    delta_days = (end_date - start_date).days + 1
    
    # Initialize result list
    phases_list = []
    
    # Create time range for the period
    t0 = ts.utc(start_date)
    t1 = ts.utc(end_date)
    
    # Create a function that returns the moon phase at a given time
    phase_at = moon_phases(eph)
    
    # Create a time array with 3-hour steps for better detection
    time_array = []
    current = start_date
    while current <= end_date:
        time_array.append(current)
        current += timedelta(hours=3)  # Reduced from 6 to 3 hours for better detection
    
    t = ts.utc(time_array)
    
    # Find phase changes
    phase_changes = []
    prev_phase = None
    prev_time = None
    
    for i, time in enumerate(t):
        phase = phase_at(time)
        if prev_phase is not None and phase != prev_phase:
            # Phase changed, find the exact time
            if i > 0:
                # Binary search between the previous and current time
                t_start = t[i-1]
                t_end = time
                # Improve precision to 1 minute
                while (t_end.tt - t_start.tt) * 24 * 60 > 1:  # 1 minute precision
                    mid_tt = t_start.tt + (t_end.tt - t_start.tt) / 2
                    # Convert to UTC datetime and back to Time object
                    mid_datetime = ts.tt_jd(mid_tt).utc_datetime()
                    t_mid = ts.utc(mid_datetime)
                    mid_phase = phase_at(t_mid)
                    if mid_phase == prev_phase:
                        t_start = t_mid
                    else:
                        t_end = t_mid
                
                # Add the phase change
                phase_names = ['New Moon', 'First Quarter', 'Full Moon', 'Last Quarter']
                phase_changes.append({
                    'time': t_end.utc_datetime(),
                    'phase': phase_names[phase]
                })
        
        prev_phase = phase
        prev_time = time
    
    # Process each calendar day
    for day_offset in range(delta_days):
        current_date = start_date + timedelta(days=day_offset)
        next_date = current_date + timedelta(days=1)
        
        # Find phases that occur on this day
        day_phases = []
        
        for phase_change in phase_changes:
            phase_dt = phase_change['time']
            if current_date <= phase_dt < next_date:
                day_phases.append({
                    "phase": phase_change['phase'],
                    "time": format_datetime(phase_dt),
                    "description": f"Moon is {phase_change['phase']}"
                })
        
        # Remove duplicates (same phase on same day)
        unique_phases = []
        seen_phases = set()
        
        for phase in day_phases:
            phase_key = phase["phase"]
            if phase_key not in seen_phases:
                unique_phases.append(phase)
                seen_phases.add(phase_key)
        
        # Add to result list
        phases_list.append({
            "date": format_datetime(current_date).split(' ')[0],
            "phases": unique_phases
        })
    
    print("Done calculating Moon phases.\n")
    return phases_list

def get_moon_events(start_date, end_date):
    """
    Aggregate all moon-related events for the given period.
    
    Parameters:
    - start_date, end_date: datetime objects defining the period to check
    
    Returns:
    - List of dictionaries with all moon events for each calendar day
    """
    print("Aggregating Moon events...") # for debugging
    # Get all moon data
    lunar_days = calculate_lunar_days(start_date, end_date)
    sign_changes = get_moon_sign_changes(start_date, end_date)
    aspects = get_moon_aspects(start_date, end_date)
    phases = get_moon_phases(start_date, end_date)
    
    # Create a combined dictionary for each day
    combined_events = []
    
    # Calculate number of days in the period
    delta_days = (end_date - start_date).days + 1
    
    # Process each calendar day
    for day_offset in range(delta_days):
        current_date = start_date + timedelta(days=day_offset)
        date_str = format_datetime(current_date).split(' ')[0]
        
        # Find data for this day in each list
        day_lunar = next((day for day in lunar_days if day["date"] == date_str), {"lunar_days": []})
        day_signs = [change for change in sign_changes if change["date"] == date_str]
        day_aspects = next((day for day in aspects if day["date"] == date_str), {"aspects": []})
        day_phases = next((day for day in phases if day["date"] == date_str), {"phases": []})
        
        # Combine all data for this day
        day_events = {
            "date": date_str,
            "lunar_days": day_lunar["lunar_days"],
            "current_sign": get_planet_sign('moon', current_date),
            "sign_changes": day_signs,
            "aspects": day_aspects["aspects"],
            "phases": day_phases["phases"]
        }
        
        combined_events.append(day_events)
    
    print("Done aggregating Moon events.\n")
    return combined_events

# retrograde.py:
from datetime import datetime, timedelta
from skyfield.api import load, load_file, utc

# Load the ephemeris data
ts = load.timescale()
eph = load_file('de442.bsp')

# Import utility functions after initializing skyfield
from utility import format_datetime, ensure_datetime, get_planet_object, calculate_velocity, calculate_ecliptic_velocity

PHASE_TRANSITIONS = {
    'R': {'next': 'S_D', 'threshold': -0.1},
    'S_D': {'next': 'D', 'threshold': 0.1},
    'D': {'next': 'S_R', 'threshold': 0.1},
    'S_R': {'next': 'R', 'threshold': -0.1}
}

PLANET_VELOCITY_THRESHOLDS = {
    'mercury': {'stationary': 0.05, 'exact': 0.005},
    'venus': {'stationary': 0.04, 'exact': 0.004},
    'mars': {'stationary': 0.03, 'exact': 0.003},
    'jupiter': {'stationary': 0.02, 'exact': 0.002},
    'saturn': {'stationary': 0.015, 'exact': 0.0015},
    'uranus': {'stationary': 0.01, 'exact': 0.001},
    'neptune': {'stationary': 0.008, 'exact': 0.0008},
    'pluto': {'stationary': 0.006, 'exact': 0.0006},
    'moon': {'stationary': 0.3, 'exact': 0.03}
}

def find_stationary_interpolation(planet_obj, start_date, end_date, sample_minutes=10):
    """Find stationary point using polynomial interpolation"""
    import numpy as np
    from numpy.polynomial import Polynomial
    
    # Collect data points for interpolation
    sample_times = []
    sample_velocities = []
    
    # Sample velocities at regular intervals
    sample_time = start_date
    while sample_time <= end_date:
        velocity = calculate_ecliptic_velocity(planet_obj, sample_time)
        time_float = (sample_time - datetime(1970, 1, 1, tzinfo=utc)).total_seconds()
        sample_times.append(time_float)
        sample_velocities.append(velocity)
        sample_time += timedelta(minutes=sample_minutes)
    
    if len(sample_times) < 4:
        return None, float('inf')
        
    # Normalize times to avoid numerical issues
    base_time = min(sample_times)
    norm_times = [t - base_time for t in sample_times]
    
    try:
        # Fit cubic polynomial to the velocity data
        poly = Polynomial.fit(norm_times, sample_velocities, 3)
        roots = poly.roots()
        
        # Filter for real roots within our time range
        valid_roots = [r.real for r in roots if abs(r.imag) < 1e-10 and 
                      min(norm_times) <= r.real <= max(norm_times)]
        
        if valid_roots:
            # Find root with velocity closest to zero
            best_root = min(valid_roots, key=lambda r: abs(poly(r)))
            interp_time = datetime.fromtimestamp(base_time + best_root, tz=utc)
            velocity = calculate_ecliptic_velocity(planet_obj, interp_time)
            return interp_time, abs(velocity)
            
    except Exception as e:
        print(f"Interpolation failed: {e}")
    
    return None, float('inf')

def find_stationary_binary(planet_obj, start_date, end_date, precision_minutes=1):
    """Find stationary point using binary search"""
    search_start = start_date
    search_end = end_date
    best_point = None
    min_velocity = float('inf')
    
    while (search_end - search_start) > timedelta(minutes=precision_minutes):
        mid_time = search_start + (search_end - search_start) / 2
        mid_velocity = calculate_ecliptic_velocity(planet_obj, mid_time)
        
        before_velocity = calculate_ecliptic_velocity(planet_obj, search_start)
        after_velocity = calculate_ecliptic_velocity(planet_obj, search_end)
        
        # Track point with minimum absolute velocity
        if abs(mid_velocity) < min_velocity:
            min_velocity = abs(mid_velocity)
            best_point = mid_time
        
        # If we found a sign change, narrow the search to that interval
        if before_velocity * mid_velocity <= 0:
            search_end = mid_time
            continue
        elif mid_velocity * after_velocity <= 0:
            search_start = mid_time
            continue
        
        # Otherwise, move in the direction of decreasing velocity
        if abs(before_velocity) < abs(after_velocity):
            search_end = mid_time
        else:
            search_start = mid_time
    
    return best_point, min_velocity

def find_stationary_point(planet, start_date, end_date, precision_minutes=1):
    """
    Find the exact moment when a planet's apparent motion becomes zero using multiple methods.
    First uses binary search to find an approximate point, then refines with interpolation.
    """
    planet_obj = get_planet_object(planet)
    start_date = ensure_datetime(start_date)
    end_date = ensure_datetime(end_date)
    
    print(f"Searching for stationary point between {format_datetime(start_date)} and {format_datetime(end_date)}")
    
    # First use binary search to find an approximate stationary point
    binary_point, binary_velocity = find_stationary_binary(planet_obj, start_date, end_date, precision_minutes)
    
    if binary_point:
        print(f"Binary search found point at {format_datetime(binary_point)} with velocity {binary_velocity}")
        
        # Now use interpolation in a narrow window around the binary search result
        # Use a window of 12 hours before and after the binary point
        interp_start = binary_point - timedelta(hours=6)
        interp_end = binary_point + timedelta(hours=6)
        
        # Ensure we stay within the original search range
        interp_start = max(interp_start, start_date)
        interp_end = min(interp_end, end_date)
        
        # Run interpolation with a finer sampling interval
        interp_point, interp_velocity = find_stationary_interpolation(
            planet_obj, interp_start, interp_end, sample_minutes=5
        )
        
        if interp_point and abs(interp_velocity) < abs(binary_velocity):
            print(f"Interpolation refined result: velocity = {interp_velocity}")
            return interp_point
        else:
            print(f"Using binary search result: velocity = {binary_velocity}")
            return binary_point
    else:
        print("Binary search failed")
    # If binary search failed, try interpolation on the full range as a fallback
    interp_point, interp_velocity = find_stationary_interpolation(planet_obj, start_date, end_date)
    if interp_point:
        print(f"Using interpolation result: velocity = {interp_velocity}")
        return interp_point
    
    print("No stationary point found")
    return None

# Function to calculate retrograde motion of the planet
def is_retrograde(planet, date):
    # Correct planet name format
    planet_obj = get_planet_object(planet)
    
    # Check position on consecutive days
    t1 = ts.utc(date.year, date.month, date.day)
    t2 = ts.utc(date.year, date.month, date.day + 1)
    
    earth = eph['earth']
    
    # Get ecliptic longitude on both days
    pos1 = earth.at(t1).observe(planet_obj).ecliptic_latlon()[1].degrees
    pos2 = earth.at(t2).observe(planet_obj).ecliptic_latlon()[1].degrees
    
    # If longitude is decreasing, planet is retrograde
    # (Need to handle cases where it crosses 0/360 degrees)
    if pos1 > pos2 and abs(pos1 - pos2) < 350:
        return True
    return False

# Function to find retrograde periods
def find_retrograde_periods(planet, start_date, end_date):
    """
    Find stationary points for a planet within a date range.
    Returns a list of events with stationary points.
    """
    planet_obj = get_planet_object(planet)
    periods = []
    
    # Skip Sun as it doesn't have retrograde motion from Earth's perspective
    if planet.lower() == 'sun':
        return periods
    
    # Get planet-specific thresholds
    thresholds = PLANET_VELOCITY_THRESHOLDS.get(
        planet.lower(), 
        {'stationary': 0.1, 'exact': 0.01}  # Default values
    )
    stationary_threshold = thresholds['stationary']
    
    # Adapt step size based on planet
    planet_step_sizes = {
        'mercury': timedelta(days=10),
        'venus': timedelta(days=30),
        'mars': timedelta(days=30),
        'jupiter': timedelta(days=60),
        'saturn': timedelta(days=90),
        'uranus': timedelta(days=120),
        'neptune': timedelta(days=150),
        'pluto': timedelta(days=180),
        'moon': timedelta(days=3)  # Moon doesn't really go retrograde but included for completeness
    }
    
    step_size = planet_step_sizes.get(planet.lower(), timedelta(days=30))
    
    # Scan through the date range with large steps to find velocity sign changes
    current_date = start_date
    last_velocity = calculate_ecliptic_velocity(planet_obj, current_date)
    
    print(f"Starting search for {planet} stationary points from {format_datetime(start_date)} to {format_datetime(end_date)}")
    print(f"Initial velocity: {last_velocity}")
    
    while current_date < end_date:
        print((f"Search loop: {format_datetime(current_date)} - {format_datetime(end_date)}"))
        next_date = current_date + step_size
        if next_date > end_date:
            next_date = end_date
            
        velocity = calculate_ecliptic_velocity(planet_obj, next_date)
        
        # Check if velocity changed sign - indicates a stationary point between
        if last_velocity * velocity <= 0 and last_velocity != 0:
            print(f"Velocity sign change detected between {format_datetime(current_date)} ({last_velocity}) and {format_datetime(next_date)} ({velocity})")
            
            # Find the exact stationary point in this interval
            search_start = current_date - step_size/4  # Look a bit before
            search_end = next_date + step_size/4  # Look a bit after
            
            # Ensure search boundaries are within original range
            search_start = max(search_start, start_date)
            search_end = min(search_end, end_date)
            
            stationary_point = find_stationary_point(planet, search_start, search_end)
            
            if stationary_point:
                # Determine if this is turning retrograde or direct
                before_vel = calculate_ecliptic_velocity(planet_obj, stationary_point - timedelta(days=1))
                after_vel = calculate_ecliptic_velocity(planet_obj, stationary_point + timedelta(days=1))
                
                phase = 'S_R' if before_vel > after_vel else 'S_D'
                description = 'turns retrograde' if phase == 'S_R' else 'turns direct'
                
                periods.append({
                    'planet': planet,
                    'phase': phase,
                    'stationary_point': format_datetime(stationary_point),
                    'description': f"{planet.capitalize()} {description}"
                })
        
        last_velocity = velocity
        current_date = next_date
    
    print(f"Finished search for {planet} stationary points.")
    return periods

# Function to get phase description
def get_phase_description(phase):
    descriptions = {
        'D': 'Direct Motion',
        'S_R': 'Stationary Retrograde',
        'R': 'Retrograde Motion',
        'S_D': 'Stationary Direct'
    }
    return descriptions.get(phase, 'Unknown Phase')

# angular_velocity.py:
from skyfield.api import load, load_file, wgs84
from skyfield.framelib import ICRS, itrs
import numpy as np
from utility import calculate_velocity, format_datetime, calculate_ecliptic_velocity
from datetime import datetime, timezone

# Load ephemeris and create time object
ts = load.timescale()
t = ts.utc(2025, 3, 5)
eph = load_file('de442.bsp')
earth = eph['earth']
jupiter = eph['moon']

# Get Jupiter's position relative to Earth
position = earth.at(t).observe(jupiter).apparent()

# Calculate rates in equatorial frame
ra, dec, distance, ra_rate, dec_rate, distance_rate = position.frame_latlon_and_rates(ICRS)

# Apply spherical trigonometry correction
# Multiply right ascension rate by cosine of declination to account for convergence of longitude lines
ra_adjusted = ra_rate.degrees.per_day * np.cos(dec.radians)
angular_velocity = np.sqrt(ra_adjusted**2 + dec_rate.degrees.per_day**2)

print(f"Jupiter's angular velocity: {angular_velocity:.15f}° per day")

dt = datetime(2025, 3, 5, tzinfo=timezone.utc)
print(f"Angular velocity with adaptable time windows: {calculate_ecliptic_velocity(jupiter, dt):.15f}° per day")

# json_converter.py:
import json

with open('astrological_calendar.json', 'r') as f:
    data = json.load(f)

# Convert data to daily feed format
daily_feed = []
retrogrades = data[0]["Retrograde"]
aspects = data[1]["Aspects"]
sign_changes = data[2]["Sign Changes"]

if len(retrogrades) > 0:
    # filter events in retrograde, leaving only those with phase S_D and S_R
    retrogrades = [event for event in retrogrades if 'stationary_point' in event]
    for event in retrogrades:
        daily_feed.append({
            "type": "point",
            "datetime": event["stationary_point"],
            "description": f"{event['planet'].capitalize()} turns {'retrograde' if event['phase'] == 'S_R' else 'direct'}"
        })
if len(aspects) > 0:
    for event in aspects:
        daily_feed.append({
            "type": "point",
            "datetime": event["exact_time_utc"],
            "description": f"{event['planet1'].capitalize()} in {event['aspect']} with {event['planet2'].capitalize()}"
        })
if len(sign_changes) > 0:
    for event in sign_changes:
        daily_feed.append({
            "type": "point",
            "datetime": event["datetime"],
            "description": event["description"]
        })

# Sort the feed by datetime
daily_feed.sort(key=lambda x: x["datetime"])

# Save the feed to a JSON file
with open('events_feed.json', 'w') as f:
    json.dump(daily_feed, f, default=str)