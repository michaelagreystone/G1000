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

// --- Load Data ---
async function loadSites() {
    const { data } = await db
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
    let query = db
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
    const { data, error } = await db
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

// --- Render Table ---
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
                <td>${entry.employees?.full_name || '\u2014'}</td>
                <td>${entry.employees?.trade?.toUpperCase() || '\u2014'}</td>
                <td>${entry.job_sites?.site_name || '\u2014'}</td>
                <td>${clockIn.toLocaleDateString()}</td>
                <td>${clockIn.toLocaleTimeString()}</td>
                <td>${clockOut ? clockOut.toLocaleTimeString() : '<span class="active-badge">Active</span>'}</td>
                <td>${entry.total_hours ? entry.total_hours + ' hrs' : '\u2014'}</td>
                <td>
                    ${entry.is_flagged
                        ? `<span class="flag-icon" title="${entry.flag_reason || ''}">&#9888;&#65039; ${entry.flag_reason || 'Flagged'}</span>`
                        : '<span class="ok-icon">&#10003;</span>'
                    }
                    <br><small>In: ${entry.clock_in_distance_meters ? Math.round(entry.clock_in_distance_meters) + 'm' : 'N/A'}</small>
                </td>
            </tr>
        `;
    }).join('');
}

// --- Stats ---
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

// --- Filters ---
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

// --- CSV Export ---
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
