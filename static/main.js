import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { SVGLoader } from 'three/addons/loaders/SVGLoader.js';

// Basic Scene Setup
const scene = new THREE.Scene();
const aspect = window.innerWidth / window.innerHeight;
const d = 40; // increased distance to see all orbits
const camera = new THREE.OrthographicCamera(-d * aspect, d * aspect, d, -d, 1, 1000);
const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Controls
const controls = new OrbitControls(camera, renderer.domElement);

// Move camera
camera.position.set(0, 0, 50);
camera.lookAt(scene.position);

// Planet data (from python script)
const PLANETS_DATA = {
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
};

const planets = {};
let sortedTimeKeys = [];
const timelineResolution = 10; // Increase for smoother animation

// Placeholder for data
let positions = {};
let events_feed = [];
let moon_events_feed = [];
let all_events = [];
let eventSprites = [];

let currentDateSpan;

const orbitRadii = {
    'mercury': 5,
    'venus': 8,
    'earth': 11,
    'moon': 2, // relative to earth
    'mars': 14,
    'jupiter': 18,
    'saturn': 22,
    'uranus': 26,
    'neptune': 30,
    'pluto': 34
};

const planetTimeKeys = {};

// Asynchronously load data
async function loadData() {
    const positionsPromise = fetch('../positions.json').then(res => res.json());
    const eventsPromise = fetch('../events_feed.json').then(res => res.json());
    const moonEventsPromise = fetch('../moon_events_feed.json').then(res => res.json());

    [positions, events_feed, moon_events_feed] = await Promise.all([positionsPromise, eventsPromise, moonEventsPromise]);

    // Process and combine events
    const processEvent = e => ({ ...e, date: new Date(e.datetime) });
    all_events = [...events_feed.map(processEvent), ...moon_events_feed.map(processEvent)];
    all_events.sort((a, b) => a.date - b.date);

    sortedTimeKeys = Object.keys(positions).sort();
    for (const planetName in PLANETS_DATA) {
        planetTimeKeys[planetName] = sortedTimeKeys.filter(key => positions[key][planetName]);
    }

    console.log("Data loaded!");
    init();
}

function init() {
    const loader = new SVGLoader();
    const loadPromises = [];

    for (const planetName in PLANETS_DATA) {
        const loadPromise = new Promise((resolve) => {
            loader.load(
                `/static/images/${planetName}.svg`,
                function (data) {
                    const paths = data.paths;
                    const group = new THREE.Group();
                    const planetData = PLANETS_DATA[planetName];

                    for (let i = 0; i < paths.length; i++) {
                        const path = paths[i];
                        const material = new THREE.MeshBasicMaterial({
                            color: path.color,
                            side: THREE.DoubleSide,
                            depthWrite: false
                        });
                        const shapes = SVGLoader.createShapes(path);
                        for (let j = 0; j < shapes.length; j++) {
                            const shape = shapes[j];
                            const geometry = new THREE.ShapeGeometry(shape);
                            const mesh = new THREE.Mesh(geometry, material);
                            group.add(mesh);
                        }
                    }
                    
                    const box = new THREE.Box3().setFromObject(group);
                    const size = new THREE.Vector3();
                    box.getSize(size);
                    const desiredSize = planetData.size / 5;
                    const scale = desiredSize / Math.max(size.x, size.y);
                    const center = new THREE.Vector3();
                    box.getCenter(center);

                    group.children.forEach(child => {
                        child.position.sub(center);
                    });

                    group.scale.set(scale, scale, scale);
                    group.position.set(0, 0, 0);
                    planets[planetName] = group;
                    scene.add(group);
                    resolve();
                },
                function (xhr) {
                    // console.log( ( xhr.loaded / xhr.total * 100 ) + '% loaded' );
                },
                function (error) {
                    console.log(`An error happened with ${planetName}.svg`);
                    const planetData = PLANETS_DATA[planetName];
                    const geometry = new THREE.CircleGeometry(planetData.size / 10, 32);
                    const material = new THREE.MeshBasicMaterial({ color: planetData.color });
                    const circle = new THREE.Mesh(geometry, material);
                    planets[planetName] = circle;
                    scene.add(circle);
                    resolve(); // Resolve even on error to not block the app
                }
            );
        });
        loadPromises.push(loadPromise);
    }

    Promise.all(loadPromises).then(() => {
        // Ensure moon is properly parented to Earth
        if (planets['moon'] && planets['earth']) {
            scene.remove(planets['moon']);
            planets['earth'].add(planets['moon']);
        }

        // Timeline
        const timeline = document.getElementById('timeline');
        currentDateSpan = document.getElementById('current-date');
        timeline.max = (sortedTimeKeys.length - 1) * timelineResolution;

        timeline.addEventListener('input', (e) => {
            updatePlanetPositions(e.target.value);
        });

        // Initial positions
        updatePlanetPositions(0);

        drawOrbits();
    });
}

function drawOrbits() {
    for (const planetName in orbitRadii) {
        const radius = orbitRadii[planetName];
        const geometry = new THREE.CircleGeometry(radius, 64);
        const edges = new THREE.EdgesGeometry(geometry);
        const material = new THREE.LineBasicMaterial({ color: PLANETS_DATA[planetName].color, transparent: true, opacity: 0.3 });
        const orbitLine = new THREE.LineSegments(edges, material);

        if (planetName === 'moon') {
            if (planets['earth']) {
                planets['earth'].add(orbitLine);
            }
        } else {
            scene.add(orbitLine);
        }
    }
}

function makeTextSprite(message, opts) {
    // ... (same as before)
}

function displayEvents(events) {
    // ... (same as before)
}

function getInterpolatedPosition(planetName, currentDate) {
    const keys = planetTimeKeys[planetName];
    if (!keys || keys.length === 0) return null;

    let i = 0;
    while (i < keys.length && new Date(keys[i]) < currentDate) {
        i++;
    }
    const prevIndex = i > 0 ? i - 1 : 0;
    const nextIndex = i < keys.length ? i : keys.length - 1;
    
    const prevKey = keys[prevIndex];
    const nextKey = keys[nextIndex];

    const prevDate = new Date(prevKey);
    const nextDate = new Date(nextKey);
    
    let alpha = 0;
    if (nextDate.getTime() - prevDate.getTime() > 0) {
        alpha = (currentDate.getTime() - prevDate.getTime()) / (nextDate.getTime() - prevDate.getTime());
    }
    
    const prevPos = positions[prevKey][planetName];
    const nextPos = positions[nextKey][planetName];

    if (prevPos && nextPos) {
        const prevVec = new THREE.Vector3(...prevPos);
        const nextVec = new THREE.Vector3(...nextPos);
        return new THREE.Vector3().lerpVectors(prevVec, nextVec, alpha);
    }
    return null;
}

function updatePlanetPositions(timeValue) {
    const ratio = timeValue / ((sortedTimeKeys.length - 1) * timelineResolution);
    const startDate = new Date(sortedTimeKeys[0]);
    const endDate = new Date(sortedTimeKeys[sortedTimeKeys.length - 1]);
    const totalDuration = endDate.getTime() - startDate.getTime();
    const currentDate = new Date(startDate.getTime() + ratio * totalDuration);

    for (const planetName in planets) {
        if (!planets[planetName] || planetName === 'sun' || planetName === 'moon') continue;

        const interpolatedPosition = getInterpolatedPosition(planetName, currentDate);
        if (interpolatedPosition) {
            const radius = orbitRadii[planetName];
            if (radius) {
                const angle = Math.atan2(interpolatedPosition.y, interpolatedPosition.x);
                const x = radius * Math.cos(angle);
                const y = radius * Math.sin(angle);
                planets[planetName].position.set(x, y, 0);
            }
        }
    }

    // Handle moon separately
    if (planets['moon'] && planets['earth']) {
        const earthPosition = getInterpolatedPosition('earth', currentDate);
        const moonPosition = getInterpolatedPosition('moon', currentDate);
        
        if (earthPosition && moonPosition) {
            const moonGeocentric = new THREE.Vector3().subVectors(moonPosition, earthPosition);
            const moonScale = 1;
            planets['moon'].position.set(
                moonGeocentric.x * moonScale,
                moonGeocentric.y * moonScale,
                0
            );
        }
    }
    
    if (currentDateSpan) {
        currentDateSpan.textContent = currentDate.toUTCString();
    }
    
    // ... (event display logic)
}


function animate() {
    requestAnimationFrame(animate);
    if (planets['sun']) {
        planets['sun'].position.set(0, 0, 0);
    }
    controls.update();
    renderer.render(scene, camera);
}

loadData();
animate();