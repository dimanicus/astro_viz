// D:\gemini\some_fun\static\main.js

console.log("main.js loaded");

// Basic Three.js setup
const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(75, window.innerWidth / window.innerHeight, 0.1, 1000);
camera.position.set(0, 50, 0);
camera.lookAt(0, 0, 0);

const renderer = new THREE.WebGLRenderer({ antialias: true });
renderer.setSize(window.innerWidth, window.innerHeight);
document.body.appendChild(renderer.domElement);

// Placeholder for data
let positionsData = {};
let eventsData = {};
let moonEventsData = {};

// Placeholder for planets
const planets = {};

// UI Elements
const dateDisplay = document.getElementById('date-display');
const timelineSlider = document.getElementById('timeline-slider');

// --- Main execution ---
async function main() {
    console.log("Fetching data...");
    // We can't use fetch with file:// protocol. We'll need a local server.
    // For now, we will assume the data is loaded.
    console.log("Data loading will be implemented in the next step.");

    // Setup the scene
    setupScene();

    // Start the animation loop
    animate();
}

function setupScene() {
    // Add a sun light
    const sunLight = new THREE.PointLight(0xffffff, 1.5, 2000);
    scene.add(sunLight);

    // Add ambient light
    const ambientLight = new THREE.AmbientLight(0x404040, 0.5);
    scene.add(ambientLight);

    // Add a placeholder sun
    const sunGeometry = new THREE.SphereGeometry(5, 32, 32);
    const sunMaterial = new THREE.MeshBasicMaterial({ color: 0xffff00 });
    const sun = new THREE.Mesh(sunGeometry, sunMaterial);
    scene.add(sun);

    console.log("Scene setup complete.");
}

function animate() {
    requestAnimationFrame(animate);
    renderer.render(scene, camera);
}

main().catch(err => console.error(err));
