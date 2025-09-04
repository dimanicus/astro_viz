# Project Plan: Solar System Visualization (v3)

This document outlines the development plan for the astrological event visualizer, using pre-calculated data for both events and positions.

## Core Idea

- Use the existing `events_feed.json` and `moon_events_feed.json` as the source for all astrological events.
- A new Python script, `data_generator.py`, will calculate only the positional data of celestial bodies.
- The frontend will load all three JSON files and combine them to create the final interactive visualization.

## Simplified Plan

1.  **Setup:** Initialize project structure and dependencies (`skyfield`, `numpy`).
2.  **Data Generation:** Develop the Python script to generate a JSON file with planetary positions at hybrid intervals.
3.  **Frontend:** Develop the Three.js application to load the data files and render the animated solar system and its events.

## Detailed Plan

### Phase 1: Project Setup & Data Generation

*   **Task 1.1:** Create `requirements.txt` with `skyfield` and `numpy`.
*   **Task 1.2:** Create the directory structure: `/static` for JavaScript/CSS and `/templates` for the main HTML file.
*   **Task 1.3:** Create the data generation script: `data_generator.py`.
*   **Task 1.4:** Implement the logic in `data_generator.py` to:
    *   Define a start and end date for the data generation (e.g., the year 2024).
    *   For the **Moon, Mercury, and Venus**, calculate the `[x, y, z]` ecliptic coordinates for **every hour**.
    *   For **all other planets (Mars to Pluto) and the Sun**, calculate the `[x, y,z]` ecliptic coordinates for **every day** (at 00:00 UTC).
    *   Structure the output into a single `positions.json` file.
*   **Task 1.5:** Run the script to generate the `positions.json` file.

### Phase 2: Frontend Development

*   **Task 2.1:** Create `templates/index.html` to serve as the main page.
*   **Task 2.2:** Create `static/main.js` which will contain the core Three.js logic.
*   **Task 2.3:** In `main.js`, asynchronously load the three data files: `positions.json`, `events_feed.json`, and `moon_events_feed.json`.
*   **Task 2.4:** Set up the basic Three.js scene: a camera, renderer, and a light source (for the Sun).
*   **Task 2.5:** Create spheres for the Sun and all planets. Store them in an easily accessible way.
*   **Task 2.6:** Create a timeline slider UI element spanning the date range from the data.
*   **Task 2.7:** Implement the animation loop. When the timeline slider's value changes:
    *   Find the two closest position data points (e.g., for Mars, Day 5 and Day 6; for the Moon, Hour 3 and Hour 4).
    *   Use linear interpolation (`lerp`) to calculate the planet's exact position for the given time between those two points.
    *   Update the 3D position of each planet in the scene.
*   **Task 2.8:** Iterate through the events from `events_feed.json` and `moon_events_feed.json`. When the timeline's current time matches an event's time, display a visual marker (e.g., a line for an aspect, an icon for a station).

### Phase 3: Refinement

*   **Task 3.1:** Improve the visual styling. Add orbital lines, planet textures, and better UI elements.
*   **Task 3.2:** Add interactivity, such as clicking on a planet or an event to get more details.
*   **Task 3.3:** Optimize performance and ensure responsiveness.