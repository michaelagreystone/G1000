// geo.js
// GPS location services and geofence calculations

/**
 * Get the user's current GPS position.
 * Returns a Promise that resolves to {latitude, longitude, accuracy}.
 * Rejects with a descriptive error message if location access fails.
 */
function getCurrentPosition() {
    return new Promise((resolve, reject) => {
        if (!navigator.geolocation) {
            reject('Geolocation is not supported by your browser. Please use a modern browser.');
            return;
        }

        navigator.geolocation.getCurrentPosition(
            (position) => {
                resolve({
                    latitude: position.coords.latitude,
                    longitude: position.coords.longitude,
                    accuracy: position.coords.accuracy
                });
            },
            (error) => {
                switch (error.code) {
                    case error.PERMISSION_DENIED:
                        reject('Location permission denied. GPS is REQUIRED to clock in. Please enable location services and reload.');
                        break;
                    case error.POSITION_UNAVAILABLE:
                        reject('Location unavailable. Please ensure GPS is enabled on your device.');
                        break;
                    case error.TIMEOUT:
                        reject('Location request timed out. Please try again.');
                        break;
                    default:
                        reject('Unable to determine your location. Please try again.');
                }
            },
            {
                enableHighAccuracy: true,  // Use GPS, not just network
                timeout: 15000,            // 15 second timeout
                maximumAge: 0              // Force fresh reading
            }
        );
    });
}

/**
 * Haversine formula: calculate distance in meters between two GPS points.
 */
function calculateDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000; // Earth radius in meters
    const phi1 = (lat1 * Math.PI) / 180;
    const phi2 = (lat2 * Math.PI) / 180;
    const deltaPhi = ((lat2 - lat1) * Math.PI) / 180;
    const deltaLambda = ((lon2 - lon1) * Math.PI) / 180;

    const a =
        Math.sin(deltaPhi / 2) * Math.sin(deltaPhi / 2) +
        Math.cos(phi1) * Math.cos(phi2) *
        Math.sin(deltaLambda / 2) * Math.sin(deltaLambda / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));

    return Math.round(R * c);
}

/**
 * Check if coordinates are within a job site's geofence.
 * Returns { within: boolean, distance: number (meters) }
 */
function checkGeofence(userLat, userLon, siteLat, siteLon, radiusMeters) {
    const distance = calculateDistance(userLat, userLon, siteLat, siteLon);
    return {
        within: distance <= radiusMeters,
        distance: distance
    };
}
