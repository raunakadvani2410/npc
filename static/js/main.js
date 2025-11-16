// State
let currentState = 'IDLE';
let currentSymbol = 'NIFTY';  // Default symbol
let currentTab = null;
let activeSymbols = ['NIFTY'];  // Default
let symbolData = {
    'NIFTY': { rocData: [], referenceData: [] }
};

// Legacy state for backward compatibility
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

// Symbol input elements
const symbolInputContainer = document.getElementById('symbol-input-container');
const niftyExpiryInput = document.getElementById('nifty-expiry-input');
const equitySymbolInput = document.getElementById('equity-symbol-input');
const equityExpiryInput = document.getElementById('equity-expiry-input');

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
    try {
        // Get symbol configuration (date inputs return YYYY-MM-DD format)
        const niftyExpiry = niftyExpiryInput.value;
        const equitySymbol = equitySymbolInput.value.trim().toUpperCase();
        const equityExpiry = equityExpiryInput.value;
        
        // Validate inputs
        if (!niftyExpiry) {
            alert('Please select NIFTY expiry date');
            return;
        }
        
        if (equitySymbol && !equityExpiry) {
            alert('Please select expiry date for equity symbol');
            return;
        }
        
        // Build payload
        const payload = { nifty_expiry: niftyExpiry };
        
        if (equitySymbol && equityExpiry) {
            payload.equity_symbol = equitySymbol;
            payload.equity_expiry = equityExpiry;
            activeSymbols = ['NIFTY', equitySymbol];
            // Initialize symbol data structure
            symbolData = {
                'NIFTY': { rocData: [], referenceData: [] },
                [equitySymbol]: { rocData: [], referenceData: [] }
            };
        } else {
            activeSymbols = ['NIFTY'];
            symbolData = {
                'NIFTY': { rocData: [], referenceData: [] }
            };
        }
        
        await apiCall('start', 'POST', payload);
        console.log('Scraping started');
        
        // Hide symbol input container
        symbolInputContainer.style.display = 'none';
        
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
        
        // Clear multi-symbol state
        activeSymbols = ['NIFTY'];
        currentSymbol = 'NIFTY';
        symbolData = {
            'NIFTY': { rocData: [], referenceData: [] }
        };
        
        // Clear legacy state
        rocData = [];
        referenceData = [];
        currentTab = null;
        
        // Clear UI
        tabsContainer.style.display = 'none';
        tabsHeader.innerHTML = '';
        tabsContent.innerHTML = '';
        
        // Remove symbol tabs if they exist
        const existingSymbolTabs = document.querySelector('.symbol-tabs');
        if (existingSymbolTabs) {
            existingSymbolTabs.remove();
        }
        
        // Show symbol input container
        symbolInputContainer.style.display = 'block';
        
        // Reset input values
        equitySymbolInput.value = '';
        equityExpiryInput.value = '';
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
    
    // Show/hide symbol input container (only show when IDLE)
    if (status.state === 'IDLE') {
        symbolInputContainer.style.display = 'block';
    } else {
        symbolInputContainer.style.display = 'none';
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
        // Fetch symbols list first
        const symbolsResponse = await apiCall('symbols');
        activeSymbols = symbolsResponse.symbols || ['NIFTY'];
        
        // Fetch data for each symbol
        for (const symbol of activeSymbols) {
            try {
                const [roc, reference] = await Promise.all([
                    apiCall(`roc/${symbol}`),
                    apiCall(`reference/${symbol}`)
                ]);
                
                // Store in symbol-specific data structure
                if (!symbolData[symbol]) {
                    symbolData[symbol] = {};
                }
                symbolData[symbol].rocData = roc || [];
                symbolData[symbol].referenceData = reference || [];
                
                console.log(`Fetched data for ${symbol}:`, { 
                    rocLength: symbolData[symbol].rocData.length, 
                    refLength: symbolData[symbol].referenceData.length 
                });
            } catch (error) {
                console.error(`Error fetching data for ${symbol}:`, error);
                // Continue with other symbols
            }
        }
        
        // Update legacy state for current symbol (backward compatibility)
        if (symbolData[currentSymbol]) {
            rocData = symbolData[currentSymbol].rocData;
            referenceData = symbolData[currentSymbol].referenceData;
        }
        
        // Render UI
        renderSymbolTabs();
        
        if (symbolData[currentSymbol] && symbolData[currentSymbol].rocData.length > 0) {
            console.log('Rendering tables for', currentSymbol, 'with', symbolData[currentSymbol].rocData.length, 'rows');
            renderTables(currentSymbol);
        } else {
            console.log(`No ROC data to display yet for ${currentSymbol}`);
        }
    } catch (error) {
        console.error('Failed to fetch data:', error);
    }
}

// Symbol Tab Rendering
function renderSymbolTabs() {
    if (activeSymbols.length <= 1) {
        // Only one symbol, no need for symbol tabs
        const existingSymbolTabs = document.querySelector('.symbol-tabs');
        if (existingSymbolTabs) {
            existingSymbolTabs.remove();
        }
        return;
    }
    
    // Create top-level symbol tabs
    let symbolTabsHTML = '<div class="symbol-tabs">';
    activeSymbols.forEach(symbol => {
        const activeClass = symbol === currentSymbol ? 'active' : '';
        symbolTabsHTML += `<button class="symbol-tab ${activeClass}" data-symbol="${symbol}">${symbol}</button>`;
    });
    symbolTabsHTML += '</div>';
    
    // Insert before tabs-header or at start of tabs-container
    const existingSymbolTabs = document.querySelector('.symbol-tabs');
    if (existingSymbolTabs) {
        existingSymbolTabs.remove();
    }
    
    tabsContainer.insertAdjacentHTML('afterbegin', symbolTabsHTML);
    
    // Add click handlers
    document.querySelectorAll('.symbol-tab').forEach(btn => {
        btn.addEventListener('click', () => switchSymbol(btn.dataset.symbol));
    });
}

function switchSymbol(symbol) {
    currentSymbol = symbol;
    
    // Update symbol tab styling
    document.querySelectorAll('.symbol-tab').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.symbol === symbol);
    });
    
    // Update legacy state
    if (symbolData[symbol]) {
        rocData = symbolData[symbol].rocData;
        referenceData = symbolData[symbol].referenceData;
    }
    
    // Re-render tables for new symbol
    renderTables(symbol);
}

// Table Rendering
function renderTables(symbol) {
    symbol = symbol || currentSymbol;
    const data = symbolData[symbol];
    
    if (!data || !data.rocData || data.rocData.length === 0) {
        console.log(`No data available for ${symbol}`);
        return;
    }
    
    // Use symbol-specific data
    const symbolRocData = data.rocData;
    const symbolRefData = data.referenceData;
    
    // Get unique strike prices
    const strikes = [...new Set(symbolRocData.map(row => row['Strike Price']))].sort((a, b) => a - b);
    
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
    
    // Get data for current symbol
    const data = symbolData[currentSymbol];
    if (!data) return;
    
    const symbolRocData = data.rocData || [];
    const symbolRefData = data.referenceData || [];
    
    // Filter data for this strike
    const referenceForStrike = symbolRefData.filter(row => row['Strike Price'] === strike);
    const rocForStrike = symbolRocData.filter(row => row['Strike Price'] === strike)
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
        html += buildTable(rocForStrike, true);
        html += '</div>';
    }
    
    tabContentDiv.innerHTML = html;
}

function buildTable(data, applyColorCoding) {
    if (data.length === 0) return '';
    
    // Define column order explicitly (not alphabetical)
    const columns = [
        'Remarks (Calls)', 'Volume (Calls)', 'OI Lakhs (Calls)', 'LTP (Calls)', 'IV', 'COI/VOL (Calls)',
        'Strike Price', 'COI/VOL (Puts)', 'Volume (Puts)', 'OI Lakhs (Puts)', 'LTP (Puts)', 'Remarks (Puts)',
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
    
    let html = '<table class="data-table"><thead><tr>';
    
    // Header
    columns.forEach(col => {
        html += `<th>${escapeHtml(col)}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Rows
    data.forEach(row => {
        html += '<tr>';
        columns.forEach(col => {
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
            
            const displayValue = formatCellValue(value);
            html += `<td class="${cellClass}">${displayValue}</td>`;
        });
        html += '</tr>';
    });
    
    html += '</tbody></table>';
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

