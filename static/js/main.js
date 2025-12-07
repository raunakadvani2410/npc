// State
let currentState = 'IDLE';
let currentTab = null;
let rocData = [];
let referenceData = [];

// DOM Elements
const startBtn = document.getElementById('start-btn');
const stopBtn = document.getElementById('stop-btn');
const resetBtn = document.getElementById('reset-btn');
const otpContainer = document.getElementById('otp-container');
const otpInput = document.getElementById('otp-input');
const submitOtpBtn = document.getElementById('submit-otp-btn');
const statusText = document.getElementById('status-text');
const updateCounter = document.getElementById('update-counter');
const logsContainer = document.getElementById('logs-container');
const errorContainer = document.getElementById('error-container');
const errorMessage = document.getElementById('error-message');
const tabsContainer = document.getElementById('tabs-container');
const tabsHeader = document.getElementById('tabs-header');
const tabsContent = document.getElementById('tabs-content');
const configContainer = document.getElementById('config-container');
const tickerInput = document.getElementById('ticker-input');
const expiryInput = document.getElementById('expiry-input');

// Event Listeners
startBtn.addEventListener('click', handleStart);
stopBtn.addEventListener('click', handleStop);
resetBtn.addEventListener('click', handleReset);
submitOtpBtn.addEventListener('click', handleSubmitOtp);

// Enter key on OTP input
otpInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        handleSubmitOtp();
    }
});

// API Functions
async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    try {
        const response = await fetch(`/api/${endpoint}`, options);
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || 'API call failed');
        }
        
        return data;
    } catch (error) {
        console.error(`API Error (${endpoint}):`, error);
        throw error;
    }
}

// Event Handlers
async function handleStart() {
    const ticker = tickerInput.value.trim();
    const expiryDate = expiryInput.value.trim();
    
    if (!ticker) {
        alert('Please enter a ticker symbol');
        return;
    }
    
    if (!expiryDate) {
        alert('Please select an expiry date');
        return;
    }
    
    try {
        await apiCall('start', 'POST', { ticker, expiry_date: expiryDate });
        console.log('Scraping started');
    } catch (error) {
        alert(`Failed to start: ${error.message}`);
    }
}

async function handleStop() {
    try {
        await apiCall('stop', 'POST');
        console.log('Scraping stopped');
    } catch (error) {
        alert(`Failed to stop: ${error.message}`);
    }
}

async function handleReset() {
    if (!confirm('Are you sure you want to reset the app? This will stop any running processes.')) {
        return;
    }
    
    try {
        await apiCall('reset', 'POST');
        console.log('App reset');
        // Clear local state
        rocData = [];
        referenceData = [];
        currentTab = null;
        tabsContainer.style.display = 'none';
        tabsHeader.innerHTML = '';
        tabsContent.innerHTML = '';
    } catch (error) {
        alert(`Failed to reset: ${error.message}`);
    }
}

async function handleSubmitOtp() {
    const otp = otpInput.value.trim();
    
    if (otp.length !== 6) {
        alert('Please enter a 6-digit OTP');
        return;
    }
    
    try {
        await apiCall('submit_otp', 'POST', { otp });
        otpInput.value = '';
        console.log('OTP submitted');
    } catch (error) {
        alert(`Failed to submit OTP: ${error.message}`);
    }
}

// State Management
function updateUIState(status) {
    const previousState = currentState;
    currentState = status.state;
    
    // Update status text
    statusText.textContent = formatStateName(status.state);
    statusText.className = `status-value ${status.state.toLowerCase()}`;
    
    // Update counters
    updateCounter.textContent = status.counter || 0;
    
    // If we just entered SCRAPING state, fetch data immediately
    if (currentState === 'SCRAPING' && previousState !== 'SCRAPING') {
        console.log('Entered SCRAPING state, fetching data immediately');
        fetchData();
    }
    
    // Update button states
    startBtn.disabled = !['IDLE', 'ERROR', 'STOPPED'].includes(status.state);
    stopBtn.disabled = !['LOGGING_IN', 'WAITING_FOR_OTP', 'OTP_SUBMITTED', 'SCRAPING'].includes(status.state);
    
    // Show/hide config container
    if (['IDLE', 'ERROR', 'STOPPED'].includes(status.state)) {
        configContainer.style.display = 'block';
    } else {
        configContainer.style.display = 'none';
    }
    
    // Show/hide OTP input (only show when waiting for OTP)
    if (status.state === 'WAITING_FOR_OTP') {
        otpContainer.style.display = 'block';
        otpInput.focus();
    } else {
        otpContainer.style.display = 'none';
        otpInput.value = '';  // Clear OTP input when hidden
    }
    
    // Show/hide error
    if (status.state === 'ERROR' && status.error_message) {
        errorContainer.style.display = 'block';
        errorMessage.textContent = status.error_message;
    } else {
        errorContainer.style.display = 'none';
    }
    
    // Update logs
    if (status.logs && status.logs.length > 0) {
        updateLogs(status.logs);
    }
}

function formatStateName(state) {
    const stateMap = {
        'IDLE': 'Idle',
        'LOGGING_IN': 'Logging in...',
        'WAITING_FOR_OTP': 'Waiting for OTP',
        'OTP_SUBMITTED': 'Processing login...',
        'SCRAPING': 'Scraping',
        'ERROR': 'Error',
        'STOPPED': 'Stopped'
    };
    return stateMap[state] || state;
}

function updateLogs(logs) {
    logsContainer.innerHTML = logs.map(log => 
        `<div class="log-entry">${escapeHtml(log)}</div>`
    ).join('');
    
    // Auto-scroll to bottom
    logsContainer.scrollTop = logsContainer.scrollHeight;
}

// Data Management
async function fetchData() {
    if (currentState !== 'SCRAPING') {
        return;
    }
    
    try {
        const [roc, reference] = await Promise.all([
            apiCall('roc'),
            apiCall('reference')
        ]);
        
        rocData = roc || [];
        referenceData = reference || [];
        
        console.log('Fetched data:', { rocLength: rocData.length, refLength: referenceData.length });
        
        if (rocData.length > 0) {
            console.log('Rendering tables with', rocData.length, 'rows');
            renderTables();
        } else {
            console.log('No ROC data to display yet');
        }
    } catch (error) {
        console.error('Failed to fetch data:', error);
    }
}

// Table Rendering
function renderTables() {
    // Get unique strike prices
    const strikes = [...new Set(rocData.map(row => row['Strike Price']))].sort((a, b) => a - b);
    
    if (strikes.length === 0) {
        return;
    }
    
    // Show tabs container
    tabsContainer.style.display = 'block';
    
    // Render tabs if needed
    if (tabsHeader.children.length !== strikes.length) {
        renderTabs(strikes);
    }
    
    // Update current tab content
    if (currentTab !== null) {
        updateTabContent(currentTab);
    }
}

function renderTabs(strikes) {
    // Clear existing tabs
    tabsHeader.innerHTML = '';
    tabsContent.innerHTML = '';
    
    strikes.forEach((strike, index) => {
        // Create tab button
        const tabBtn = document.createElement('button');
        tabBtn.className = 'tab-button';
        tabBtn.textContent = strike;
        tabBtn.dataset.strike = strike;
        
        if (index === 0) {
            tabBtn.classList.add('active');
            currentTab = strike;
        }
        
        tabBtn.addEventListener('click', () => switchTab(strike));
        tabsHeader.appendChild(tabBtn);
        
        // Create tab content container
        const tabContentDiv = document.createElement('div');
        tabContentDiv.className = 'tab-content';
        tabContentDiv.dataset.strike = strike;
        
        if (index === 0) {
            tabContentDiv.classList.add('active');
        }
        
        tabsContent.appendChild(tabContentDiv);
    });
    
    // Render initial content
    updateTabContent(currentTab);
}

function switchTab(strike) {
    // Update button states
    document.querySelectorAll('.tab-button').forEach(btn => {
        if (btn.dataset.strike == strike) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });
    
    // Update content visibility
    document.querySelectorAll('.tab-content').forEach(content => {
        if (content.dataset.strike == strike) {
            content.classList.add('active');
        } else {
            content.classList.remove('active');
        }
    });
    
    currentTab = strike;
    updateTabContent(strike);
}

function updateTabContent(strike) {
    const tabContentDiv = document.querySelector(`.tab-content[data-strike="${strike}"]`);
    if (!tabContentDiv) return;
    
    // Save scroll position of ROC table wrapper before update
    const rocTableWrapper = tabContentDiv.querySelector('.table-section:last-child .table-wrapper');
    const scrollTop = rocTableWrapper ? rocTableWrapper.scrollTop : 0;
    
    // Filter data for this strike
    const referenceForStrike = referenceData.filter(row => row['Strike Price'] === strike);
    const rocForStrike = rocData.filter(row => row['Strike Price'] === strike)
        .sort((a, b) => new Date(b['Time (ROC)']) - new Date(a['Time (ROC)']));
    
    // Build HTML
    let html = '';
    
    // Reference table
    if (referenceForStrike.length > 0) {
        html += '<div class="table-section">';
        html += '<h4>Reference Data (t0)</h4>';
        html += buildTable(referenceForStrike, false);
        html += '</div>';
    }
    
    // ROC table
    if (rocForStrike.length > 0) {
        html += '<div class="table-section">';
        html += '<h4>Rate of Change Data</h4>';
        html += buildTable(rocForStrike, true, true);  // Apply color coding and freeze first 2 rows
        html += '</div>';
    }
    
    tabContentDiv.innerHTML = html;
    
    // Restore scroll position after update
    const newRocTableWrapper = tabContentDiv.querySelector('.table-section:last-child .table-wrapper');
    if (newRocTableWrapper && scrollTop > 0) {
        newRocTableWrapper.scrollTop = scrollTop;
    }
}

function buildTable(data, applyColorCoding, freezeFirstTwoRows = false) {
    if (data.length === 0) return '';
    
    // Define column order explicitly (not alphabetical)
    const columns = [
        'Remarks (Calls)', 
        'Volume (Calls)', 'Volume (Calls) %',
        'OI Lakhs (Calls)', 'OI Lakhs (Calls) %',
        'LTP (Calls)', 'LTP (Calls) %',
        'IV', 'IV %',
        'COI/VOL (Calls)',
        'Strike Price', 
        'COI/VOL (Puts)', 
        'LTP (Puts)', 'LTP (Puts) %',
        'OI Lakhs (Puts)', 'OI Lakhs (Puts) %',
        'Volume (Puts)', 'Volume (Puts) %',
        'Remarks (Puts)',
        'Time (ROC)', 'Time (t0)'
    ].filter(col => col in data[0]); // Only include columns that exist in the data
    
    const columnsToStyle = [
        'Volume (Calls)',
        'OI Lakhs (Calls)',
        'LTP (Calls)',
        'Volume (Puts)',
        'OI Lakhs (Puts)',
        'LTP (Puts)'
    ];
    
    // Columns that should be hidden (we merge them with their base column)
    const percentageColumns = [
        'Volume (Calls) %',
        'OI Lakhs (Calls) %',
        'LTP (Calls) %',
        'IV %',
        'LTP (Puts) %',
        'OI Lakhs (Puts) %',
        'Volume (Puts) %'
    ];
    
    // Map each percentage column to its base column
    const baseColumnMap = {
        'Volume (Calls) %': 'Volume (Calls)',
        'OI Lakhs (Calls) %': 'OI Lakhs (Calls)',
        'LTP (Calls) %': 'LTP (Calls)',
        'IV %': 'IV',
        'LTP (Puts) %': 'LTP (Puts)',
        'OI Lakhs (Puts) %': 'OI Lakhs (Puts)',
        'Volume (Puts) %': 'Volume (Puts)'
    };
    
    // Filter out percentage columns from header
    const displayColumns = columns.filter(col => !percentageColumns.includes(col));
    
    let html = '<div class="table-wrapper"><table class="data-table"><thead><tr>';
    
    // Header
    displayColumns.forEach(col => {
        html += `<th>${escapeHtml(col)}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Rows
    data.forEach((row, index) => {
        // Add frozen row class for first 2 rows of ROC table
        let rowClass = '';
        if (freezeFirstTwoRows && index === 0) {
            rowClass = ' class="frozen-row-1"';
        } else if (freezeFirstTwoRows && index === 1) {
            rowClass = ' class="frozen-row-2"';
        }
        
        html += `<tr${rowClass}>`;
        displayColumns.forEach(col => {
            const value = row[col];
            let cellClass = '';
            
            // Apply color coding for ROC data
            if (applyColorCoding && columnsToStyle.includes(col)) {
                if (value > 0) {
                    cellClass = 'positive';
                } else if (value < 0) {
                    cellClass = 'negative';
                }
            }
            
            // Check if this column has a corresponding percentage column
            const pctCol = `${col} %`;
            let displayValue = formatCellValue(value);
            
            if (row.hasOwnProperty(pctCol) && row[pctCol] !== null && row[pctCol] !== undefined) {
                const pctValue = row[pctCol];
                const pctSign = pctValue > 0 ? '+' : '';
                displayValue = `${displayValue} <span class="percentage">(${pctSign}${pctValue.toFixed(2)}%)</span>`;
            }
            
            html += `<td class="${cellClass}">${displayValue}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></div>';
    return html;
}

function formatCellValue(value) {
    if (value === null || value === undefined) {
        return '-';
    }
    
    if (typeof value === 'number') {
        // Round to 2 decimal places
        return value.toFixed(2);
    }
    
    return escapeHtml(String(value));
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Polling
async function pollStatus() {
    try {
        const status = await apiCall('status');
        updateUIState(status);
    } catch (error) {
        console.error('Failed to poll status:', error);
    }
}

async function pollData() {
    await fetchData();
}

// Initialize
function init() {
    // Poll status every 2 seconds
    setInterval(pollStatus, 2000);
    
    // Poll data every 5 seconds when scraping
    setInterval(() => {
        if (currentState === 'SCRAPING') {
            pollData();
        }
    }, 5000);
    
    // Initial poll
    pollStatus();
}

// Start on page load
document.addEventListener('DOMContentLoaded', init);

