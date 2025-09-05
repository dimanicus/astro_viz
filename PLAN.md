# Project Plan: Solar System Visualization (v3)

This document outlines the development plan for the astrological event visualizer, using pre-calculated data for both events and positions.

## Core Idea

- Use the existing `events_feed.json` and `moon_events_feed.json` as the source for all astrological events.
- A new Python script, `data_generator.py`, will calculate only the positional data of celestial bodies.
- The frontend will load all three JSON files and combine them to create the final interactive visualization.

## Simplified Plan

1.  **Setup:** Initialize project structure and dependencies (`skyfield`, `numpy`).
2.  **Data Generation:** Develop the Python script to generate a JSON file with planetary positions at hybrid intervals.
3.  **Frontend:** Develop a 2D application to load the data files and render an animated, stylized sketch of the solar system and its events.

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

### Phase 2: Frontend Development (2D Sketch)

*   **Task 2.1:** Create `templates/index.html` to serve as the main page.
*   **Task 2.2:** Create `static/main.js`.
*   **Task 2.3:** The frontend will be a 2D or isometric sketch, not a realistic 3D model. We will use Three.js with an OrthographicCamera to achieve a top-down 2D view, as it provides powerful rendering capabilities.
*   **Task 2.4:** In `main.js`, asynchronously load the three data files: `positions.json`, `events_feed.json`, and `moon_events_feed.json`.
*   **Task 2.5:** Set up the basic 2D scene with an OrthographicCamera. No lighting will be used, as the view is a schematic.
*   **Task 2.6:** Create circular representations for the Sun and all planets. The sizes will be normalized for clear visibility of all bodies.
*   **Task 2.7:** Draw circular orbits for each planet. The radius of the orbits will be categorical to represent the relative order of the planets, not their exact scaled distances.
*   **Task 2.8:** Create a timeline slider UI element spanning the date range from the data.
*   **Task 2.9:** Implement the animation loop. When the timeline slider's value changes:
    *   Calculate the angle of the planet on its circular orbit based on its ecliptic longitude from the `positions.json` data.
    *   Update the 2D position of each planet on its circular orbit.

*   **Task 2.11:** Iterate through the events from `events_feed.json` and `moon_events_feed.json`. When the timeline's current time matches an event's time, display a visual marker (e.g., a custom icon or a text label).

### Phase 3: Styling and Refinement

*   **Task 3.1:** Apply a carefully thought-through thematic styling. This includes selecting a color palette, typography, and designing custom icons for events to create a visually appealing and informative interface. The background will not be black.
*   **Task 3.2:** Add interactivity, such as hovering over a planet or an event to display more detailed information in a tooltip or a sidebar.
*   **Task 3.3:** Optimize performance to ensure the animation is smooth and the application is responsive, especially on lower-end devices.