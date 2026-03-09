// config.js
// Supabase client initialization

const SUPABASE_URL = 'https://lqbqtmjzkwmkvwmguyut.supabase.co';
const SUPABASE_ANON_KEY = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImxxYnF0bWp6a3dta3Z3bWd1eXV0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzMwODMxNDIsImV4cCI6MjA4ODY1OTE0Mn0.bbrArxmAU7uzsP_zYwGpBtKsm3yU1SPGM9jH0j28Hes';

// Create Supabase client - use 'db' to avoid name conflict with CDN global
const db = window.supabase.createClient(SUPABASE_URL, SUPABASE_ANON_KEY);

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
