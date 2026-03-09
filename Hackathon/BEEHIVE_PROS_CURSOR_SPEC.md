# Beehive Pro's Time Card - Cursor Build Specification

## Project Overview

**Beehive Pro's Time Card** is a minimalistic, mobile-first web application for Ferris Development Group. It allows hourly trades workers (electricians, plumbers, HVAC technicians) to clock in and clock out of job sites with GPS verification. The system geofences each job site and flags entries where the worker is outside the acceptable radius, preventing hour inflation from workers clocking in while still in transit.

**Tech Stack**: Plain HTML + CSS + Vanilla JavaScript. No frameworks, no build tools. Supabase for backend (database + RPC functions). The Supabase API keys are already set as environment variables.

---

## Environment Variables (Already Configured)

The following should be available in your environment. Reference them in a `config.js` file:

```
SUPABASE_URL=your_supabase_project_url
SUPABASE_ANON_KEY=your_supabase_anon_key
```

---

## Project Structure

```
beehive-pros-timecard/
├── index.html          # Main worker-facing clock in/out page
├── admin.html          # Admin dashboard for reviewing entries
├── css/
│   └── styles.css      # All styles (single file)
├── js/
│   ├── config.js       # Supabase client initialization
│   ├── app.js          # Main clock in/out logic
│   ├── geo.js          # GPS and geofencing utilities
│   └── admin.js        # Admin dashboard logic
└── README.md           # Setup instructions
```

---

## File 1: `config.js` - Supabase Client

```javascript
// config.js
// Supabase client initialization
// IMPORTANT: Replace these with your actual Supabase credentials
// or load from environment variables in your deployment

const SUPABASE_URL = 'YOUR_SUPABASE_URL';       // e.g. https://xxxx.supabase.co
const SUPABASE_ANON_KEY = 'YOUR_SUPABASE_ANON_KEY';

// Import Supabase client from CDN (loaded in HTML <script> tag)
const supabase = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

// Utility: Get user's IP address (using free API)
async function getUserIP() {
    try {
        const response = await fetch('https://api.ipify.org?format=json');
        const data = await response.json();
        return data.ip;
    } catch (error) {
        console.warn('Could not fetch IP address:', error);
        return null;
    }
}
```

---

## File 2: `geo.js` - GPS and Geofencing

```javascript
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
```

---

## File 3: `app.js` - Main Application Logic

```javascript
// app.js
// Core clock in/out application logic

// ─── State ───────────────────────────────────────────────────────────
let currentEmployee = null;  // { phone, name, trade }
let jobSites = [];
let currentPosition = null;

// ─── DOM References ──────────────────────────────────────────────────
const loginSection = document.getElementById('login-section');
const clockSection = document.getElementById('clock-section');
const statusMessage = document.getElementById('status-message');
const employeeNameInput = document.getElementById('employee-name');
const employeePhoneInput = document.getElementById('employee-phone');
const tradeSelect = document.getElementById('employee-trade');
const siteSelect = document.getElementById('job-site-select');
const clockInBtn = document.getElementById('clock-in-btn');
const clockOutBtn = document.getElementById('clock-out-btn');
const gpsStatus = document.getElementById('gps-status');
const employeeGreeting = document.getElementById('employee-greeting');
const currentTime = document.getElementById('current-time');
const shiftInfo = document.getElementById('shift-info');

// ─── Initialize ──────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
    await loadJobSites();
    startClock();
    setupEventListeners();

    // Check if employee info is stored in session
    const savedPhone = sessionStorage.getItem('bh_phone');
    const savedName = sessionStorage.getItem('bh_name');
    const savedTrade = sessionStorage.getItem('bh_trade');
    if (savedPhone && savedName) {
        currentEmployee = { phone: savedPhone, name: savedName, trade: savedTrade || 'general' };
        showClockSection();
        await checkOpenShift();
    }
});

// ─── Load Job Sites from Supabase ────────────────────────────────────
async function loadJobSites() {
    try {
        const { data, error } = await supabase
            .from('job_sites')
            .select('*')
            .eq('is_active', true)
            .order('site_name');

        if (error) throw error;
        jobSites = data || [];

        // Populate dropdown
        if (siteSelect) {
            siteSelect.innerHTML = '<option value="">-- Select Job Site --</option>';
            jobSites.forEach(site => {
                const opt = document.createElement('option');
                opt.value = site.id;
                opt.textContent = `${site.site_name}${site.address ? ' - ' + site.address : ''}`;
                siteSelect.appendChild(opt);
            });
        }
    } catch (error) {
        console.error('Failed to load job sites:', error);
        showStatus('Could not load job sites. Check your connection.', 'error');
    }
}

// ─── Event Listeners ─────────────────────────────────────────────────
function setupEventListeners() {
    // Login form
    document.getElementById('login-form').addEventListener('submit', handleLogin);

    // Clock buttons
    clockInBtn.addEventListener('click', handleClockIn);
    clockOutBtn.addEventListener('click', handleClockOut);

    // Logout
    document.getElementById('logout-btn').addEventListener('click', handleLogout);

    // Format phone number as user types
    employeePhoneInput.addEventListener('input', formatPhoneInput);
}

// ─── Phone Formatting ────────────────────────────────────────────────
function formatPhoneInput(e) {
    let value = e.target.value.replace(/\D/g, '');
    if (value.length > 10) value = value.substring(0, 10);

    if (value.length >= 7) {
        e.target.value = `(${value.slice(0,3)}) ${value.slice(3,6)}-${value.slice(6)}`;
    } else if (value.length >= 4) {
        e.target.value = `(${value.slice(0,3)}) ${value.slice(3)}`;
    } else if (value.length >= 1) {
        e.target.value = `(${value}`;
    }
}

function normalizePhone(input) {
    const digits = input.replace(/\D/g, '');
    if (digits.length === 10) return '+1' + digits;
    if (digits.length === 11 && digits.startsWith('1')) return '+' + digits;
    return '+1' + digits;  // assume US
}

// ─── Login Handler ───────────────────────────────────────────────────
async function handleLogin(e) {
    e.preventDefault();

    const name = employeeNameInput.value.trim();
    const phone = normalizePhone(employeePhoneInput.value);
    const trade = tradeSelect.value;

    if (!name || phone.length < 12) {
        showStatus('Please enter your full name and 10-digit phone number.', 'error');
        return;
    }

    currentEmployee = { phone, name, trade };

    // Save to session (persists across page reloads within same tab)
    sessionStorage.setItem('bh_phone', phone);
    sessionStorage.setItem('bh_name', name);
    sessionStorage.setItem('bh_trade', trade);

    showClockSection();
    await checkOpenShift();
}

// ─── Show Clock Section ──────────────────────────────────────────────
function showClockSection() {
    loginSection.classList.add('hidden');
    clockSection.classList.remove('hidden');
    employeeGreeting.textContent = `${currentEmployee.name} (${currentEmployee.trade.toUpperCase()})`;

    // Start acquiring GPS immediately
    acquireGPS();
}

// ─── GPS Acquisition ─────────────────────────────────────────────────
async function acquireGPS() {
    gpsStatus.textContent = 'Acquiring GPS...';
    gpsStatus.className = 'gps-status acquiring';

    try {
        currentPosition = await getCurrentPosition();
        gpsStatus.textContent = `GPS Locked (±${Math.round(currentPosition.accuracy)}m)`;
        gpsStatus.className = 'gps-status locked';
    } catch (error) {
        gpsStatus.textContent = error;
        gpsStatus.className = 'gps-status error';
        currentPosition = null;
    }
}

// ─── Check for Open Shift ────────────────────────────────────────────
async function checkOpenShift() {
    try {
        const { data, error } = await supabase
            .from('time_entries')
            .select('*, job_sites(site_name)')
            .eq('employee_phone', currentEmployee.phone)
            .is('clock_out_at', null)
            .order('clock_in_at', { ascending: false })
            .limit(1);

        if (error) throw error;

        if (data && data.length > 0) {
            const entry = data[0];
            const clockInTime = new Date(entry.clock_in_at);
            const hoursElapsed = ((Date.now() - clockInTime.getTime()) / 3600000).toFixed(2);

            clockInBtn.disabled = true;
            clockInBtn.classList.add('disabled');
            clockOutBtn.disabled = false;
            clockOutBtn.classList.remove('disabled');

            const siteName = entry.job_sites ? entry.job_sites.site_name : 'Unknown Site';
            shiftInfo.innerHTML = `
                <div class="shift-active">
                    <strong>Active Shift</strong><br>
                    Site: ${siteName}<br>
                    Clocked in: ${clockInTime.toLocaleTimeString()}<br>
                    Hours so far: <span id="running-hours">${hoursElapsed}</span>
                </div>
            `;

            // Update running hours every minute
            setInterval(() => {
                const hrs = ((Date.now() - clockInTime.getTime()) / 3600000).toFixed(2);
                const el = document.getElementById('running-hours');
                if (el) el.textContent = hrs;
            }, 60000);
        } else {
            clockInBtn.disabled = false;
            clockInBtn.classList.remove('disabled');
            clockOutBtn.disabled = true;
            clockOutBtn.classList.add('disabled');
            shiftInfo.innerHTML = '<p class="no-shift">No active shift</p>';
        }
    } catch (error) {
        console.error('Error checking open shift:', error);
    }
}

// ─── Clock In ────────────────────────────────────────────────────────
async function handleClockIn() {
    const siteId = siteSelect.value;
    if (!siteId) {
        showStatus('Please select a job site.', 'error');
        return;
    }

    // Re-acquire GPS for fresh reading
    showStatus('Verifying your location...', 'info');
    await acquireGPS();

    if (!currentPosition) {
        showStatus('Cannot clock in without GPS. Please enable location services and try again.', 'error');
        return;
    }

    // Check geofence client-side for immediate feedback
    const site = jobSites.find(s => s.id === siteId);
    if (site) {
        const fence = checkGeofence(
            currentPosition.latitude, currentPosition.longitude,
            site.latitude, site.longitude,
            site.radius_meters
        );

        if (!fence.within) {
            const confirmProceed = confirm(
                `WARNING: You are ${fence.distance}m from ${site.site_name} ` +
                `(limit: ${site.radius_meters}m).\n\n` +
                `This clock-in will be FLAGGED for review.\n\n` +
                `Do you still want to proceed?`
            );
            if (!confirmProceed) return;
        }
    }

    clockInBtn.disabled = true;
    clockInBtn.textContent = 'Clocking In...';

    try {
        const ip = await getUserIP();

        const { data, error } = await supabase.rpc('clock_in', {
            p_phone: currentEmployee.phone,
            p_name: currentEmployee.name,
            p_trade: currentEmployee.trade,
            p_job_site_id: siteId,
            p_latitude: currentPosition.latitude,
            p_longitude: currentPosition.longitude,
            p_ip: ip
        });

        if (error) throw error;

        if (data.success) {
            const msg = data.within_geofence
                ? `Clocked in at ${new Date().toLocaleTimeString()}. You are on site.`
                : `Clocked in at ${new Date().toLocaleTimeString()}. WARNING: You are ${Math.round(data.distance_meters)}m from site. This entry has been flagged.`;

            showStatus(msg, data.within_geofence ? 'success' : 'warning');
            await checkOpenShift();
        } else {
            showStatus(data.message || 'Clock-in failed.', 'error');
            clockInBtn.disabled = false;
        }
    } catch (error) {
        console.error('Clock-in error:', error);
        showStatus('Clock-in failed. Please check your connection and try again.', 'error');
        clockInBtn.disabled = false;
    }

    clockInBtn.textContent = 'CLOCK IN';
}

// ─── Clock Out ───────────────────────────────────────────────────────
async function handleClockOut() {
    if (!confirm('Are you sure you want to clock out?')) return;

    showStatus('Verifying your location...', 'info');
    await acquireGPS();

    clockOutBtn.disabled = true;
    clockOutBtn.textContent = 'Clocking Out...';

    try {
        const ip = await getUserIP();

        const { data, error } = await supabase.rpc('clock_out', {
            p_phone: currentEmployee.phone,
            p_latitude: currentPosition ? currentPosition.latitude : null,
            p_longitude: currentPosition ? currentPosition.longitude : null,
            p_ip: ip
        });

        if (error) throw error;

        if (data.success) {
            showStatus(
                `Clocked out at ${new Date().toLocaleTimeString()}. Total hours: ${data.total_hours}`,
                data.is_flagged ? 'warning' : 'success'
            );
            await checkOpenShift();
        } else {
            showStatus(data.message || 'Clock-out failed.', 'error');
            clockOutBtn.disabled = false;
        }
    } catch (error) {
        console.error('Clock-out error:', error);
        showStatus('Clock-out failed. Please check your connection and try again.', 'error');
        clockOutBtn.disabled = false;
    }

    clockOutBtn.textContent = 'CLOCK OUT';
}

// ─── Logout ──────────────────────────────────────────────────────────
function handleLogout() {
    sessionStorage.clear();
    currentEmployee = null;
    currentPosition = null;
    clockSection.classList.add('hidden');
    loginSection.classList.remove('hidden');
    employeeNameInput.value = '';
    employeePhoneInput.value = '';
    shiftInfo.innerHTML = '';
    showStatus('', 'info');
}

// ─── Status Message ──────────────────────────────────────────────────
function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
}

// ─── Live Clock ──────────────────────────────────────────────────────
function startClock() {
    function updateClock() {
        if (currentTime) {
            const now = new Date();
            currentTime.textContent = now.toLocaleTimeString('en-US', {
                hour: '2-digit',
                minute: '2-digit',
                second: '2-digit'
            });
        }
    }
    updateClock();
    setInterval(updateClock, 1000);
}
```

---

## File 4: `admin.js` - Admin Dashboard Logic

```javascript
// admin.js
// Admin dashboard for reviewing time entries

let allEntries = [];
let allSites = [];

document.addEventListener('DOMContentLoaded', async () => {
    await loadSites();
    await loadEntries();
    await loadActiveShifts();
    setupFilters();
});

// ─── Load Data ───────────────────────────────────────────────────────
async function loadSites() {
    const { data } = await supabase
        .from('job_sites')
        .select('*')
        .order('site_name');
    allSites = data || [];

    const siteFilter = document.getElementById('filter-site');
    allSites.forEach(site => {
        const opt = document.createElement('option');
        opt.value = site.id;
        opt.textContent = site.site_name;
        siteFilter.appendChild(opt);
    });
}

async function loadEntries(filters = {}) {
    let query = supabase
        .from('time_entries')
        .select('*, employees(full_name, trade), job_sites(site_name)')
        .order('clock_in_at', { ascending: false })
        .limit(100);

    if (filters.site) query = query.eq('job_site_id', filters.site);
    if (filters.flaggedOnly) query = query.eq('is_flagged', true);
    if (filters.dateFrom) query = query.gte('clock_in_at', filters.dateFrom);
    if (filters.dateTo) query = query.lte('clock_in_at', filters.dateTo + 'T23:59:59');

    const { data, error } = await query;
    if (error) {
        console.error('Error loading entries:', error);
        return;
    }

    allEntries = data || [];
    renderEntries(allEntries);
    updateStats(allEntries);
}

async function loadActiveShifts() {
    const { data, error } = await supabase
        .from('time_entries')
        .select('*, employees(full_name, trade), job_sites(site_name)')
        .is('clock_out_at', null)
        .order('clock_in_at', { ascending: false });

    if (error) {
        console.error('Error loading active shifts:', error);
        return;
    }

    const container = document.getElementById('active-shifts');
    if (!data || data.length === 0) {
        container.innerHTML = '<p class="empty-state">No one is currently clocked in.</p>';
        return;
    }

    container.innerHTML = data.map(entry => {
        const clockIn = new Date(entry.clock_in_at);
        const hours = ((Date.now() - clockIn.getTime()) / 3600000).toFixed(2);
        const flagClass = entry.is_flagged ? 'flagged' : '';

        return `
            <div class="active-card ${flagClass}">
                <div class="active-name">${entry.employees?.full_name || 'Unknown'}</div>
                <div class="active-detail">${entry.employees?.trade?.toUpperCase() || ''} | ${entry.job_sites?.site_name || 'Unknown Site'}</div>
                <div class="active-time">In: ${clockIn.toLocaleTimeString()} | ${hours} hrs</div>
                ${entry.is_flagged ? `<div class="flag-badge">FLAGGED: ${entry.flag_reason}</div>` : ''}
            </div>
        `;
    }).join('');
}

// ─── Render Table ────────────────────────────────────────────────────
function renderEntries(entries) {
    const tbody = document.getElementById('entries-tbody');

    if (!entries || entries.length === 0) {
        tbody.innerHTML = '<tr><td colspan="8" class="empty-state">No entries found.</td></tr>';
        return;
    }

    tbody.innerHTML = entries.map(entry => {
        const clockIn = new Date(entry.clock_in_at);
        const clockOut = entry.clock_out_at ? new Date(entry.clock_out_at) : null;
        const flagClass = entry.is_flagged ? 'row-flagged' : '';

        return `
            <tr class="${flagClass}">
                <td>${entry.employees?.full_name || '—'}</td>
                <td>${entry.employees?.trade?.toUpperCase() || '—'}</td>
                <td>${entry.job_sites?.site_name || '—'}</td>
                <td>${clockIn.toLocaleDateString()}</td>
                <td>${clockIn.toLocaleTimeString()}</td>
                <td>${clockOut ? clockOut.toLocaleTimeString() : '<span class="active-badge">Active</span>'}</td>
                <td>${entry.total_hours ? entry.total_hours + ' hrs' : '—'}</td>
                <td>
                    ${entry.is_flagged
                        ? `<span class="flag-icon" title="${entry.flag_reason || ''}">⚠️ ${entry.flag_reason || 'Flagged'}</span>`
                        : '<span class="ok-icon">✓</span>'
                    }
                    <br><small>In: ${entry.clock_in_distance_meters ? Math.round(entry.clock_in_distance_meters) + 'm' : 'N/A'}</small>
                </td>
            </tr>
        `;
    }).join('');
}

// ─── Stats ───────────────────────────────────────────────────────────
function updateStats(entries) {
    const total = entries.length;
    const flagged = entries.filter(e => e.is_flagged).length;
    const totalHours = entries.reduce((sum, e) => sum + (parseFloat(e.total_hours) || 0), 0);

    document.getElementById('stat-total').textContent = total;
    document.getElementById('stat-flagged').textContent = flagged;
    document.getElementById('stat-hours').textContent = totalHours.toFixed(1);
    document.getElementById('stat-flagged-pct').textContent =
        total > 0 ? ((flagged / total) * 100).toFixed(1) + '%' : '0%';
}

// ─── Filters ─────────────────────────────────────────────────────────
function setupFilters() {
    document.getElementById('apply-filters').addEventListener('click', () => {
        const filters = {
            site: document.getElementById('filter-site').value,
            flaggedOnly: document.getElementById('filter-flagged').checked,
            dateFrom: document.getElementById('filter-date-from').value,
            dateTo: document.getElementById('filter-date-to').value,
        };
        loadEntries(filters);
    });

    document.getElementById('clear-filters').addEventListener('click', () => {
        document.getElementById('filter-site').value = '';
        document.getElementById('filter-flagged').checked = false;
        document.getElementById('filter-date-from').value = '';
        document.getElementById('filter-date-to').value = '';
        loadEntries();
    });

    document.getElementById('refresh-btn').addEventListener('click', () => {
        loadEntries();
        loadActiveShifts();
    });

    // CSV Export
    document.getElementById('export-csv').addEventListener('click', exportCSV);
}

// ─── CSV Export ──────────────────────────────────────────────────────
function exportCSV() {
    if (!allEntries.length) return;

    const headers = ['Name', 'Trade', 'Site', 'Date', 'Clock In', 'Clock Out', 'Total Hours', 'Flagged', 'Flag Reason', 'Clock In Distance (m)'];
    const rows = allEntries.map(e => [
        e.employees?.full_name || '',
        e.employees?.trade || '',
        e.job_sites?.site_name || '',
        new Date(e.clock_in_at).toLocaleDateString(),
        new Date(e.clock_in_at).toLocaleTimeString(),
        e.clock_out_at ? new Date(e.clock_out_at).toLocaleTimeString() : 'Active',
        e.total_hours || '',
        e.is_flagged ? 'YES' : 'NO',
        e.flag_reason || '',
        e.clock_in_distance_meters ? Math.round(e.clock_in_distance_meters) : 'N/A'
    ]);

    const csv = [headers, ...rows].map(row =>
        row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(',')
    ).join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `beehive-timecard-export-${new Date().toISOString().slice(0,10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
}
```

---

## File 5: `styles.css` - Complete Stylesheet

```css
/* ══════════════════════════════════════════════════════════════════════
   BEEHIVE PRO'S TIME CARD - Ferris Development Group
   Minimalistic, mobile-first design for trades workers
   ══════════════════════════════════════════════════════════════════════ */

:root {
    --bg: #0C0C0C;
    --surface: #161616;
    --surface-raised: #1E1E1E;
    --border: #2A2A2A;
    --text-primary: #E8E8E8;
    --text-secondary: #888888;
    --accent: #F5A623;          /* Beehive gold */
    --accent-dim: #A06E15;
    --success: #34C759;
    --error: #FF3B30;
    --warning: #FFD60A;
    --flag-bg: #3A1A1A;
    --flag-border: #FF3B30;
    --font-body: 'IBM Plex Mono', 'Courier New', monospace;
    --font-display: 'IBM Plex Sans', -apple-system, sans-serif;
    --radius: 6px;
}

* { margin: 0; padding: 0; box-sizing: border-box; }

body {
    font-family: var(--font-body);
    background: var(--bg);
    color: var(--text-primary);
    min-height: 100vh;
    line-height: 1.5;
    -webkit-font-smoothing: antialiased;
}

/* ── Layout ────────────────────────────────────────────────────────── */
.container {
    max-width: 480px;
    margin: 0 auto;
    padding: 20px 16px;
}

.admin-container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 20px 24px;
}

.hidden { display: none !important; }

/* ── Header ────────────────────────────────────────────────────────── */
.header {
    text-align: center;
    padding: 24px 0 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}

.header h1 {
    font-family: var(--font-display);
    font-size: 20px;
    font-weight: 700;
    letter-spacing: 1.5px;
    text-transform: uppercase;
    color: var(--accent);
}

.header .subtitle {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
    letter-spacing: 2px;
    text-transform: uppercase;
}

.live-clock {
    font-size: 32px;
    font-weight: 300;
    color: var(--text-primary);
    margin-top: 12px;
    letter-spacing: 2px;
}

/* ── Forms / Inputs ────────────────────────────────────────────────── */
.form-group {
    margin-bottom: 16px;
}

.form-group label {
    display: block;
    font-size: 11px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}

.form-group input,
.form-group select {
    width: 100%;
    padding: 12px 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    color: var(--text-primary);
    font-family: var(--font-body);
    font-size: 16px;                  /* prevents iOS zoom */
    transition: border-color 0.2s;
}

.form-group input:focus,
.form-group select:focus {
    outline: none;
    border-color: var(--accent);
}

.form-group select {
    cursor: pointer;
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='%23888' d='M6 8L1 3h10z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right 14px center;
}

/* ── Buttons ───────────────────────────────────────────────────────── */
.btn {
    width: 100%;
    padding: 16px;
    border: none;
    border-radius: var(--radius);
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-primary {
    background: var(--accent);
    color: #000;
}
.btn-primary:hover { background: #FFBA42; }
.btn-primary:active { transform: scale(0.98); }

.btn-clock-in {
    background: var(--success);
    color: #000;
    font-size: 20px;
    padding: 20px;
    margin-bottom: 12px;
}
.btn-clock-in:hover { background: #3DD968; }

.btn-clock-out {
    background: var(--error);
    color: #fff;
    font-size: 20px;
    padding: 20px;
    margin-bottom: 12px;
}
.btn-clock-out:hover { background: #FF5147; }

.btn.disabled,
.btn:disabled {
    opacity: 0.3;
    cursor: not-allowed;
    pointer-events: none;
}

.btn-secondary {
    background: var(--surface);
    color: var(--text-secondary);
    border: 1px solid var(--border);
    font-size: 12px;
    padding: 10px;
}
.btn-secondary:hover { color: var(--text-primary); border-color: var(--text-secondary); }

/* ── GPS Status ────────────────────────────────────────────────────── */
.gps-status {
    text-align: center;
    font-size: 12px;
    padding: 8px;
    border-radius: var(--radius);
    margin-bottom: 16px;
}
.gps-status.acquiring { color: var(--accent); background: rgba(245, 166, 35, 0.1); }
.gps-status.locked { color: var(--success); background: rgba(52, 199, 89, 0.1); }
.gps-status.error { color: var(--error); background: rgba(255, 59, 48, 0.1); }

/* ── Status Messages ──────────────────────────────────────────────── */
.status-message {
    text-align: center;
    padding: 12px;
    border-radius: var(--radius);
    font-size: 13px;
    margin-bottom: 16px;
    min-height: 20px;
}
.status-message.success { color: var(--success); background: rgba(52, 199, 89, 0.1); }
.status-message.error { color: var(--error); background: rgba(255, 59, 48, 0.1); }
.status-message.warning { color: var(--warning); background: rgba(255, 214, 10, 0.1); }
.status-message.info { color: var(--text-secondary); }

/* ── Shift Info ────────────────────────────────────────────────────── */
.shift-active {
    background: rgba(52, 199, 89, 0.1);
    border: 1px solid rgba(52, 199, 89, 0.3);
    border-radius: var(--radius);
    padding: 14px;
    font-size: 13px;
    line-height: 1.8;
    margin-bottom: 16px;
}

.no-shift {
    text-align: center;
    color: var(--text-secondary);
    font-size: 13px;
    padding: 12px;
}

/* ── Employee Greeting ─────────────────────────────────────────────── */
#employee-greeting {
    font-family: var(--font-display);
    font-size: 16px;
    font-weight: 600;
    text-align: center;
    margin-bottom: 16px;
    color: var(--text-primary);
}

/* ═══════════ ADMIN DASHBOARD ═══════════════════════════════════════ */

.admin-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 16px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 20px;
    flex-wrap: wrap;
    gap: 12px;
}

.admin-header h1 {
    font-family: var(--font-display);
    font-size: 18px;
    color: var(--accent);
    letter-spacing: 1px;
}

.admin-actions {
    display: flex;
    gap: 8px;
}

.admin-actions .btn {
    width: auto;
    padding: 8px 16px;
    font-size: 12px;
}

/* ── Stats Bar ─────────────────────────────────────────────────────── */
.stats-bar {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 20px;
}

.stat-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px;
    text-align: center;
}

.stat-card .stat-value {
    font-size: 24px;
    font-weight: 700;
    color: var(--accent);
}

.stat-card .stat-label {
    font-size: 10px;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-top: 4px;
}

/* ── Filters ───────────────────────────────────────────────────────── */
.filters {
    display: flex;
    gap: 12px;
    flex-wrap: wrap;
    align-items: end;
    margin-bottom: 20px;
    padding: 14px;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

.filters .form-group {
    margin-bottom: 0;
    flex: 1;
    min-width: 140px;
}

.filters .form-group input,
.filters .form-group select {
    padding: 8px 10px;
    font-size: 13px;
}

.filter-check {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    color: var(--text-secondary);
    cursor: pointer;
    padding-top: 22px;
}

.filter-check input[type="checkbox"] { cursor: pointer; }

.filter-actions {
    display: flex;
    gap: 8px;
    padding-top: 22px;
}

.filter-actions .btn {
    width: auto;
    padding: 8px 16px;
    font-size: 11px;
}

/* ── Active Shifts Section ─────────────────────────────────────────── */
.section-title {
    font-family: var(--font-display);
    font-size: 14px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 12px;
}

.active-shifts-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 10px;
    margin-bottom: 24px;
}

.active-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 12px;
}
.active-card.flagged { border-color: var(--flag-border); background: var(--flag-bg); }

.active-name { font-weight: 700; font-size: 14px; }
.active-detail { font-size: 11px; color: var(--text-secondary); margin: 4px 0; }
.active-time { font-size: 12px; color: var(--accent); }

.flag-badge {
    font-size: 10px;
    color: var(--error);
    margin-top: 6px;
    padding: 4px 6px;
    background: rgba(255, 59, 48, 0.1);
    border-radius: 3px;
}

/* ── Table ─────────────────────────────────────────────────────────── */
.table-wrapper {
    overflow-x: auto;
    border: 1px solid var(--border);
    border-radius: var(--radius);
}

table {
    width: 100%;
    border-collapse: collapse;
    font-size: 12px;
}

thead th {
    background: var(--surface);
    padding: 10px 12px;
    text-align: left;
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: var(--text-secondary);
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}

tbody td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--border);
    white-space: nowrap;
}

tbody tr:hover { background: var(--surface); }
tbody tr.row-flagged { background: var(--flag-bg); }
tbody tr.row-flagged:hover { background: #4A1F1F; }

.active-badge {
    background: var(--success);
    color: #000;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 10px;
    font-weight: 700;
}

.flag-icon { color: var(--error); font-size: 11px; }
.ok-icon { color: var(--success); }

.empty-state {
    text-align: center;
    color: var(--text-secondary);
    padding: 24px;
    font-size: 13px;
}

/* ── Responsive ────────────────────────────────────────────────────── */
@media (max-width: 600px) {
    .stats-bar { grid-template-columns: repeat(2, 1fr); }
    .filters { flex-direction: column; }
    .admin-header { flex-direction: column; align-items: flex-start; }
}
```

---

## File 6: `index.html` - Worker Clock In/Out Page

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Beehive Pro's Time Card</title>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;700&family=IBM+Plex+Sans:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <!-- Header -->
        <div class="header">
            <h1>Beehive Pro's Time Card</h1>
            <p class="subtitle">Ferris Development Group</p>
            <div class="live-clock" id="current-time">--:--:--</div>
        </div>

        <!-- Status Message -->
        <div id="status-message" class="status-message"></div>

        <!-- Login Section -->
        <div id="login-section">
            <form id="login-form">
                <div class="form-group">
                    <label for="employee-name">Full Name</label>
                    <input type="text" id="employee-name" placeholder="John Smith" required autocomplete="name">
                </div>
                <div class="form-group">
                    <label for="employee-phone">Phone Number</label>
                    <input type="tel" id="employee-phone" placeholder="(617) 555-1234" required autocomplete="tel">
                </div>
                <div class="form-group">
                    <label for="employee-trade">Trade</label>
                    <select id="employee-trade">
                        <option value="electrician">Electrician</option>
                        <option value="plumber">Plumber</option>
                        <option value="hvac">HVAC Technician</option>
                        <option value="general">General</option>
                    </select>
                </div>
                <button type="submit" class="btn btn-primary">Continue</button>
            </form>
        </div>

        <!-- Clock In/Out Section -->
        <div id="clock-section" class="hidden">
            <div id="employee-greeting"></div>
            <div id="gps-status" class="gps-status acquiring">Acquiring GPS...</div>

            <div class="form-group">
                <label for="job-site-select">Job Site</label>
                <select id="job-site-select">
                    <option value="">-- Select Job Site --</option>
                </select>
            </div>

            <div id="shift-info"></div>

            <button id="clock-in-btn" class="btn btn-clock-in">CLOCK IN</button>
            <button id="clock-out-btn" class="btn btn-clock-out disabled" disabled>CLOCK OUT</button>

            <button id="logout-btn" class="btn btn-secondary" style="margin-top: 16px;">Switch Employee</button>
        </div>
    </div>

    <!-- Supabase CDN -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>
    <!-- App Scripts -->
    <script src="js/config.js"></script>
    <script src="js/geo.js"></script>
    <script src="js/app.js"></script>
</body>
</html>
```

---

## File 7: `admin.html` - Admin Dashboard

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Beehive Pro's - Admin Dashboard</title>
    <link rel="stylesheet" href="css/styles.css">
    <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@300;400;700&family=IBM+Plex+Sans:wght@400;600;700&display=swap" rel="stylesheet">
</head>
<body>
    <div class="admin-container">
        <!-- Header -->
        <div class="admin-header">
            <div>
                <h1>Beehive Pro's — Admin Dashboard</h1>
                <p class="subtitle" style="font-size:11px; color: var(--text-secondary); margin-top:4px;">Ferris Development Group Time Tracking</p>
            </div>
            <div class="admin-actions">
                <button id="refresh-btn" class="btn btn-secondary">Refresh</button>
                <button id="export-csv" class="btn btn-primary" style="width:auto; padding:8px 16px; font-size:12px;">Export CSV</button>
                <a href="index.html" class="btn btn-secondary" style="text-decoration:none; text-align:center;">Worker View</a>
            </div>
        </div>

        <!-- Stats -->
        <div class="stats-bar">
            <div class="stat-card">
                <div class="stat-value" id="stat-total">—</div>
                <div class="stat-label">Total Entries</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-hours">—</div>
                <div class="stat-label">Total Hours</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-flagged">—</div>
                <div class="stat-label">Flagged</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-flagged-pct">—</div>
                <div class="stat-label">Flag Rate</div>
            </div>
        </div>

        <!-- Active Shifts -->
        <h3 class="section-title">Currently Clocked In</h3>
        <div class="active-shifts-grid" id="active-shifts">
            <p class="empty-state">Loading...</p>
        </div>

        <!-- Filters -->
        <div class="filters">
            <div class="form-group">
                <label>Job Site</label>
                <select id="filter-site"><option value="">All Sites</option></select>
            </div>
            <div class="form-group">
                <label>Date From</label>
                <input type="date" id="filter-date-from">
            </div>
            <div class="form-group">
                <label>Date To</label>
                <input type="date" id="filter-date-to">
            </div>
            <label class="filter-check">
                <input type="checkbox" id="filter-flagged"> Flagged Only
            </label>
            <div class="filter-actions">
                <button id="apply-filters" class="btn btn-primary">Filter</button>
                <button id="clear-filters" class="btn btn-secondary">Clear</button>
            </div>
        </div>

        <!-- Entries Table -->
        <h3 class="section-title">Time Entries</h3>
        <div class="table-wrapper">
            <table>
                <thead>
                    <tr>
                        <th>Name</th>
                        <th>Trade</th>
                        <th>Site</th>
                        <th>Date</th>
                        <th>Clock In</th>
                        <th>Clock Out</th>
                        <th>Hours</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody id="entries-tbody">
                    <tr><td colspan="8" class="empty-state">Loading...</td></tr>
                </tbody>
            </table>
        </div>
    </div>

    <!-- Supabase CDN -->
    <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>
    <!-- App Scripts -->
    <script src="js/config.js"></script>
    <script src="js/admin.js"></script>
</body>
</html>
```

---

## Deployment Checklist

### Step 1: Supabase Setup
1. Create a Supabase project at [supabase.com](https://supabase.com)
2. Go to SQL Editor
3. Run the migration script (`beehive_pros_supabase_migration.py` output, or paste the SQL directly)
4. Verify tables created: `employees`, `job_sites`, `time_entries`
5. Verify functions created: `clock_in`, `clock_out`, `calculate_distance_meters`
6. Note your **Project URL** and **anon/public key** from Settings > API

### Step 2: Update Config
1. Open `js/config.js`
2. Replace `YOUR_SUPABASE_URL` with your project URL
3. Replace `YOUR_SUPABASE_ANON_KEY` with your anon key

### Step 3: Update Job Sites
1. In Supabase Table Editor, open `job_sites`
2. Update the seed data with accurate GPS coordinates for each Ferris site
3. Adjust `radius_meters` per site (default is 150-250m)
4. To get GPS coords: Google Maps > right-click location > copy coordinates

### Step 4: Serve Locally
```bash
# From the project root directory
npx serve .
# or
python3 -m http.server 8000
```

### Step 5: Test
1. Open `localhost:8000` on your phone (same wifi network)
2. Enter a name, phone number, select trade
3. Select a job site and clock in
4. Verify in Supabase Table Editor that the entry appears with GPS data
5. Check `admin.html` to see the dashboard view

---

## Key Design Decisions

- **Phone as ID**: Simplest possible auth. Workers just enter name + phone. No passwords, no accounts. Phone number is normalized to E.164 format (+1XXXXXXXXXX).
- **GPS mandatory for clock-in**: If GPS fails or is denied, clock-in is blocked. This is the core anti-fraud mechanism.
- **Client + server geofencing**: Distance is checked client-side for immediate UX feedback AND server-side in the `clock_in` RPC function for tamper resistance.
- **Flagging, not blocking**: Workers outside the geofence CAN still clock in, but the entry is automatically flagged with the distance and reason. This prevents legitimate edge cases (GPS drift, working across the street) from blocking workers while still surfacing suspicious activity.
- **Session persistence**: Worker identity is stored in `sessionStorage` so a page reload doesn't require re-login, but closing the tab/browser clears it. No sensitive data persists.

---

## Production Hardening (Post-MVP)

These are out of scope for the prototype but should be addressed before full deployment:

1. **Auth**: Add Supabase Auth with phone OTP verification so workers authenticate properly
2. **RLS tightening**: Replace the open anon policies with role-based policies (worker vs admin)
3. **Admin auth**: Protect `admin.html` behind login (currently open)
4. **HTTPS**: Required for GPS API in production. Deploy to Vercel/Netlify/Cloudflare Pages
5. **Offline support**: Add a service worker to queue clock-in/out when offline and sync when back online
6. **Photo verification**: Optional selfie at clock-in stored in Supabase Storage
7. **Push notifications**: Remind workers to clock out if shift exceeds expected hours
