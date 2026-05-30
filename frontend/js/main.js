/**
 * SafePath - Main JavaScript
 * Handles real-time updates and UI interactions
 */

// Configuration
const UPDATE_INTERVAL = 250; // Update every 250ms
const API_BASE_URL = window.location.origin;

// State
let updateTimer = null;
let audioUnlocked = false;
let alarmActive = false;

// DOM Elements
const elements = {
    statusBadge: document.getElementById('status-badge'),
    statusCircle: document.getElementById('status-circle'),
    statusIcon: document.getElementById('status-icon'),
    statusLevel: document.getElementById('status-level'),
    statusDescription: document.getElementById('status-description'),
    drowsinessMeter: document.getElementById('drowsiness-meter'),
    drowsinessValue: document.getElementById('drowsiness-value'),
    blinkCount: document.getElementById('blink-count'),
    yawnCount: document.getElementById('yawn-count'),
    earValue: document.getElementById('ear-value'),
    marValue: document.getElementById('mar-value'),
    totalAlerts: document.getElementById('total-alerts'),
    lastAlert: document.getElementById('last-alert'),
    alertOverlay: document.getElementById('alert-overlay'),
    alertSound: document.getElementById('alert-sound'),
    connectionDot: document.getElementById('connection-dot'),
    audioPrompt: document.getElementById('audio-prompt')
};

/**
 * Initialize the application
 */
function init() {
    console.log('[SafePath] Initializing...');

    // Initialize chart
    initializeChart();

    // Browsers require a user gesture before playing alarm audio
    setupAudioUnlock();

    // Start update loop
    startUpdates();

    // Handle visibility change (pause when tab is hidden)
    document.addEventListener('visibilitychange', handleVisibilityChange);

    console.log('[SafePath] Initialized successfully');
}

/**
 * Start periodic updates
 */
function startUpdates() {
    if (updateTimer) clearInterval(updateTimer);

    // Initial update
    updateStatus();

    // Set up periodic updates
    updateTimer = setInterval(updateStatus, UPDATE_INTERVAL);
}

/**
 * Stop periodic updates
 */
function stopUpdates() {
    if (updateTimer) {
        clearInterval(updateTimer);
        updateTimer = null;
    }
}

/**
 * Fetch and update drowsiness status
 */
async function updateStatus() {
    try {
        const response = await fetch(`${API_BASE_URL}/drowsiness_status`);

        if (!response.ok) {
            throw new Error('Failed to fetch status');
        }

        const data = await response.json();

        // Update UI
        updateStatusDisplay(data);
        updateMetrics(data.metrics);
        updateChart(data.drowsiness_score);

        // Keep alarm active while drowsiness is detected
        handleAlertState(data.status);

        // Update connection indicator
        setConnectionStatus(true);

    } catch (error) {
        console.error('Error fetching status:', error);
        setConnectionStatus(false);
    }
}

/**
 * Update status display
 */
function updateStatusDisplay(data) {
    const { status, drowsiness_score } = data;

    // Update status badge
    elements.statusBadge.querySelector('.status-text').textContent = status;
    elements.statusBadge.className = 'status-badge ' + status.toLowerCase();

    // Update status circle and info
    elements.statusCircle.className = 'status-circle ' + status.toLowerCase();
    elements.statusLevel.textContent = status;

    // Update icon and description
    const statusConfig = getStatusConfig(status);
    elements.statusIcon.innerHTML = statusConfig.icon;
    elements.statusDescription.textContent = statusConfig.description;

    // Update drowsiness meter
    elements.drowsinessMeter.style.width = drowsiness_score + '%';
    elements.drowsinessMeter.className = 'meter-fill ' + status.toLowerCase();
    elements.drowsinessValue.textContent = drowsiness_score + '%';
}

/**
 * Get status configuration
 */
function getStatusConfig(status) {
    const configs = {
        'Normal': {
            icon: STATUS_ICONS.Normal,
            description: 'All systems operational'
        },
        'Warning': {
            icon: STATUS_ICONS.Warning,
            description: 'Showing signs of fatigue'
        },
        'Alert': {
            icon: STATUS_ICONS.Alert,
            description: 'DROWSINESS DETECTED!'
        }
    };

    return configs[status] || configs['Normal'];
}

/**
 * Update metrics display
 */
function updateMetrics(metrics) {
    elements.blinkCount.textContent = metrics.blink_count || 0;
    elements.yawnCount.textContent = metrics.yawn_count || 0;
    elements.earValue.textContent = (metrics.ear || 0).toFixed(2);
    elements.marValue.textContent = (metrics.mar || 0).toFixed(2);
}

/**
 * Show prompt and unlock audio after user interaction
 */
function setupAudioUnlock() {
    const unlock = () => {
        if (!elements.alertSound) {
            return;
        }

        elements.alertSound.volume = 1.0;
        elements.alertSound.play().then(() => {
            elements.alertSound.pause();
            elements.alertSound.currentTime = 0;
            audioUnlocked = true;

            if (elements.audioPrompt) {
                elements.audioPrompt.classList.add('hidden');
            }

            if (alarmActive) {
                startAlarmSound();
            }
        }).catch(() => {
            if (elements.audioPrompt) {
                elements.audioPrompt.classList.remove('hidden');
            }
        });
    };

    if (elements.audioPrompt) {
        elements.audioPrompt.classList.remove('hidden');
        elements.audioPrompt.addEventListener('click', unlock, { once: true });
    }

    document.body.addEventListener('click', unlock, { once: true });
}

/**
 * Handle alert overlay and looping alarm sound
 */
function handleAlertState(status) {
    if (status === 'Alert') {
        elements.alertOverlay.classList.remove('hidden');
        alarmActive = true;
        startAlarmSound();
        updateAlertHistory();
        document.body.style.animation = 'flash-red 0.5s ease';
        setTimeout(() => {
            document.body.style.animation = '';
        }, 500);
        return;
    }

    alarmActive = false;
    elements.alertOverlay.classList.add('hidden');
    stopAlarmSound();
}

/**
 * Start looping alarm sound
 */
function startAlarmSound() {
    if (!audioUnlocked || !elements.alertSound) {
        return;
    }

    elements.alertSound.loop = true;
    elements.alertSound.volume = 1.0;
    elements.alertSound.currentTime = 0;
    elements.alertSound.play().catch((err) => {
        console.warn('Audio playback failed:', err);
        if (elements.audioPrompt) {
            elements.audioPrompt.classList.remove('hidden');
        }
    });
}

/**
 * Stop alarm sound
 */
function stopAlarmSound() {
    if (!elements.alertSound) {
        return;
    }

    elements.alertSound.pause();
    elements.alertSound.currentTime = 0;
    elements.alertSound.loop = false;
}

/**
 * Legacy trigger helper kept for compatibility
 */
function triggerAlert() {
    handleAlertState('Alert');
}

/**
 * Update alert history from session data
 */
async function updateAlertHistory() {
    try {
        const response = await fetch(`${API_BASE_URL}/session_data`);

        if (!response.ok) return;

        const data = await response.json();

        elements.totalAlerts.textContent = data.total_alerts || 0;

        if (data.alert_history && data.alert_history.length > 0) {
            const lastAlert = data.alert_history[data.alert_history.length - 1];
            const time = new Date(lastAlert.timestamp).toLocaleTimeString();
            elements.lastAlert.textContent = time;
        } else {
            elements.lastAlert.textContent = 'None';
        }

    } catch (error) {
        console.error('Error fetching alert history:', error);
    }
}

/**
 * Set connection status indicator
 */
function setConnectionStatus(isConnected) {
    if (isConnected) {
        elements.connectionDot.style.background = '#e8a838';
    } else {
        elements.connectionDot.style.background = '#dc2626';
    }
}

/**
 * Handle visibility change (pause/resume updates)
 */
function handleVisibilityChange() {
    if (document.hidden) {
        stopUpdates();
        console.log('[SafePath] Updates paused (tab hidden)');
    } else {
        startUpdates();
        console.log('[SafePath] Updates resumed');
    }
}

// Add flash animation to body
const style = document.createElement('style');
style.textContent = `
    @keyframes flash-red {
        0%, 100% { filter: none; }
        50% { filter: brightness(1.2) sepia(1) hue-rotate(-50deg) saturate(5); }
    }
`;
document.head.appendChild(style);

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
} else {
    init();
}

// Periodic alert history update (every 5 seconds)
setInterval(updateAlertHistory, 5000);
