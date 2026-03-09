// app.js
// Core clock in/out application logic

// --- State ---
let currentEmployee = null;  // { phone, name, trade }
let jobSites = [];
let currentPosition = null;

// --- DOM References ---
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

// --- Initialize ---
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

// --- Load Job Sites from Supabase ---
async function loadJobSites() {
    try {
        const { data, error } = await db
            .from('job_sites')
            .select('*')
            .eq('is_active', true)
            .order('site_name');

        if (error) throw error;
        jobSites = data || [];
        console.log('Loaded job sites:', jobSites.length, jobSites);

        // Populate dropdown
        if (siteSelect) {
            // Clear and rebuild
            while (siteSelect.options.length > 0) siteSelect.remove(0);
            const defaultOpt = new Option('-- Select Job Site --', '');
            siteSelect.add(defaultOpt);
            jobSites.forEach(site => {
                const opt = new Option(
                    site.site_name + (site.address ? ' - ' + site.address : ''),
                    site.id
                );
                siteSelect.add(opt);
            });
            console.log('Dropdown options:', siteSelect.options.length);
        }
    } catch (error) {
        console.error('Failed to load job sites:', error);
        showStatus('Could not load job sites. Check your connection.', 'error');
    }
}

// --- Event Listeners ---
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

// --- Phone Formatting ---
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

// --- Login Handler ---
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

// --- Show Clock Section ---
function showClockSection() {
    loginSection.classList.add('hidden');
    clockSection.classList.remove('hidden');
    employeeGreeting.textContent = `${currentEmployee.name} (${currentEmployee.trade.toUpperCase()})`;

    // Start acquiring GPS immediately
    acquireGPS();
}

// --- GPS Acquisition ---
async function acquireGPS() {
    gpsStatus.textContent = 'Acquiring GPS...';
    gpsStatus.className = 'gps-status acquiring';

    try {
        currentPosition = await getCurrentPosition();
        gpsStatus.textContent = `GPS Locked (\u00b1${Math.round(currentPosition.accuracy)}m)`;
        gpsStatus.className = 'gps-status locked';
    } catch (error) {
        gpsStatus.textContent = error;
        gpsStatus.className = 'gps-status error';
        currentPosition = null;
    }
}

// --- Check for Open Shift ---
async function checkOpenShift() {
    try {
        const { data, error } = await db
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

// --- Clock In ---
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

        const { data, error } = await db.rpc('clock_in', {
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

// --- Clock Out ---
async function handleClockOut() {
    if (!confirm('Are you sure you want to clock out?')) return;

    showStatus('Verifying your location...', 'info');
    await acquireGPS();

    clockOutBtn.disabled = true;
    clockOutBtn.textContent = 'Clocking Out...';

    try {
        const ip = await getUserIP();

        const { data, error } = await db.rpc('clock_out', {
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

// --- Logout ---
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

// --- Status Message ---
function showStatus(message, type) {
    statusMessage.textContent = message;
    statusMessage.className = `status-message ${type}`;
}

// --- Live Clock ---
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
