# data_generator.py

from skyfield.api import load, load_file, utc
from datetime import datetime, timedelta
import json
import numpy as np

# Load ephemeris data
ts = load.timescale()
eph = load_file('de442.bsp')

# Define planets and their properties
PLANETS = {
    'sun': {'id': 'sun', 'color': 0xffff00, 'size': 20},
    'mercury': {'id': 'mercury barycenter', 'color': 0x8c8c8c, 'size': 5},
    'venus': {'id': 'venus barycenter', 'color': 0xffa500, 'size': 8},
    'earth': {'id': 'earth', 'color': 0x0000ff, 'size': 9},
    'moon': {'id': 'moon', 'color': 0xd3d3d3, 'size': 2},
    'mars': {'id': 'mars barycenter', 'color': 0xff4500, 'size': 7},
    'jupiter': {'id': 'jupiter barycenter', 'color': 0xffd700, 'size': 15},
    'saturn': {'id': 'saturn barycenter', 'color': 0xf0e68c, 'size': 13},
    'uranus': {'id': 'uranus barycenter', 'color': 0x00ffff, 'size': 11},
    'neptune': {'id': 'neptune barycenter', 'color': 0x00008b, 'size': 10},
    'pluto': {'id': 'pluto barycenter', 'color': 0xa9a9a9, 'size': 3}
}

FAST_MOVERS = ['moon', 'mercury', 'venus']

def generate_positions(start_date, end_date):
    """
    Generates planetary positions at hybrid intervals.
    - Hourly for fast movers (Moon, Mercury, Venus).
    - Daily for others.
    """
    print("Generating positional data...")
    positions = {}

    # Daily interval for slow movers
    current_date = start_date
    while current_date <= end_date:
        t = ts.utc(current_date)
        date_str = current_date.strftime('%Y-%m-%d')
        positions[date_str] = {}
        for name, planet in PLANETS.items():
            if name not in FAST_MOVERS:
                astro = eph['sun'].at(t).observe(eph[planet['id']])
                x, y, z = astro.ecliptic_xyz().au
                positions[date_str][name] = [round(x, 6), round(y, 6), round(z, 6)]
        current_date += timedelta(days=1)
        print(f"Generated daily positions for {date_str}")

    # Hourly interval for fast movers
    current_date = start_date
    while current_date <= end_date:
        t = ts.utc(current_date)
        date_str = current_date.strftime('%Y-%m-%d %H:%M:%S')
        positions[date_str] = {}
        for name in FAST_MOVERS:
            planet = PLANETS[name]
            astro = eph['sun'].at(t).observe(eph[planet['id']])
            x, y, z = astro.ecliptic_xyz().au
            positions[date_str][name] = [round(x, 6), round(y, 6), round(z, 6)]
        current_date += timedelta(hours=1)
        print(f"Generated hourly positions for {date_str}")

    print("Finished generating positional data.")
    return positions

if __name__ == '__main__':
    start = datetime(2024, 1, 1, tzinfo=utc)
    end = datetime(2024, 12, 31, 23, 59, 59, tzinfo=utc)

    position_data = generate_positions(start, end)

    with open('positions.json', 'w') as f:
        json.dump(position_data, f)

    print("\nSuccessfully saved positions to positions.json")
