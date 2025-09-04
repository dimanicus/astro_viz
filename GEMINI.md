# Gemini Project: Astro Viz

## Project Overview

This project is a web-based astrological event visualizer. It renders a schematic 3D model of the solar system and displays astrological events, such as aspects and planetary sign changes, on an interactive timeline.

The architecture is designed for simplicity and performance. A Python script is used as a one-time data generator to pre-calculate all necessary planetary positions. The frontend is a static web application that loads this pre-calculated data, along with existing event data, to render the visualization. This removes the need for a live backend server.

### Key Technologies

-   **Data Generation:** Python, `skyfield`, `numpy`
-   **Frontend:** JavaScript, `Three.js`
-   **Data Files:** The project relies on three key JSON files:
    -   `positions.json`: Contains the calculated [x, y, z] coordinates of celestial bodies.
    -   `events_feed.json`: A list of major astrological events.
    -   `moon_events_feed.json`: A list of lunar-specific events.

## Building and Running

To run this project, you need Python and `pip` installed.

1.  **Set up a virtual environment (optional but recommended):**

    ```bash
    python -m venv venv
    # On Windows, use `venv\Scripts\activate`
    source venv/bin/activate
    ```

2.  **Install the required dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Generate the planetary position data:**

    This script reads the `de442.bsp` ephemeris file and generates the `positions.json` file needed by the frontend. This may take a few moments.

    ```bash
    python data_generator.py
    ```

4.  **Start a local web server:**

    To view the project, you need to run a simple local web server from the project's root directory.

    ```bash
    python -m http.server
    ```

5.  **Access the application:**

    Open your web browser and navigate to the following URL:

    [http://localhost:8000/templates/](http://localhost:8000/templates/)

## Development Conventions

-   **Data-Driven Visualization:** The entire application is driven by the three JSON files (`positions.json`, `events_feed.json`, `moon_events_feed.json`). All rendering logic in the frontend reads from this data.
-   **Data Generation:** The `data_generator.py` script is the sole source for creating the planetary position data. Any changes to the time range or calculation logic should be made here.
-   **Hybrid Time Intervals:** To balance accuracy and performance, the position data is generated at a hybrid interval: **hourly** for fast-moving bodies (Moon, Mercury, Venus) and **daily** for all others.
-   **Frontend Logic:** All visualization and interaction logic is contained within `static/main.js`. This file is responsible for setting up the Three.js scene, loading the data, and animating the objects based on user input from the timeline.
