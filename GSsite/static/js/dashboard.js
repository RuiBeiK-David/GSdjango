$(document).ready(function() {
    // --- 1. Setup ---
    const apiToken = localStorage.getItem('apiToken');
    if (!apiToken) {
        // 如果没有token，重定向到登录页
        window.location.href = "/login/"; 
        return;
    }

    // 为所有AJAX请求设置认证头
    $.ajaxSetup({
        headers: { 'Authorization': 'Token ' + apiToken },
        error: function(jqXHR) { // Global error handler
            if (jqXHR.status === 401 || jqXHR.status === 403) {
                console.error("Authentication error. Redirecting to login.");
                window.location.href = "/login/";
            }
        }
    });

    const deviceSelect = $('#deviceSelect');

    if (deviceSelect.length > 0 && deviceSelect.val()) {
        const initialDeviceId = deviceSelect.val();
        updateDashboard(initialDeviceId);

        // Set up an interval to refresh data every 10 seconds
        setInterval(function() {
            const selectedDeviceId = deviceSelect.val();
            if (selectedDeviceId) {
                fetchLatestData(selectedDeviceId); // Only fetch the latest data for card updates
                fetchAlerts(); // Also refresh alerts
            }
        }, 10000); // 10000 milliseconds = 10 seconds
    }

    deviceSelect.on('change', function() {
        const selectedDeviceId = $(this).val();
        if (selectedDeviceId) {
            updateDashboard(selectedDeviceId);
        }
    });

    function updateDashboard(deviceId) {
        fetchLatestData(deviceId);
        fetchHistoryData(deviceId); // Fetch full history for charts
        fetchAlerts();
    }

    function fetchLatestData(deviceId) {
        const urlTemplate = deviceSelect.data('realtime-url-template');
        if (!urlTemplate) return;
        const url = urlTemplate.replace('PLACEHOLDER', deviceId);

        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                updateCards(data);
            },
            error: function() {
                console.error("Failed to fetch latest data for device " + deviceId);
            }
        });
    }

    function fetchHistoryData(deviceId) {
        const urlTemplate = deviceSelect.data('history-url-template');
        if (!urlTemplate) return;
        const url = urlTemplate.replace('PLACEHOLDER', deviceId);

        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                updateCharts(data);
            },
            error: function() {
                console.error("Failed to fetch history data for device " + deviceId);
            }
        });
    }

    function fetchAlerts() {
        const url = '/health-monitor/api/alerts/';
        $.ajax({
            url: url,
            method: 'GET',
            dataType: 'json',
            success: function(data) {
                updateAlertsList(data);
            },
            error: function() {
                console.error("Failed to fetch alerts.");
            }
        });
    }

    function updateCards(data) {
        $('#heartRate').text(data.heart_rate || '--');
        $('#bloodPressure').text(`${data.blood_pressure_systolic || '--'}/${data.blood_pressure_diastolic || '--'}`);
        $('#bloodOxygen').text(data.blood_oxygen || '--');
        $('#temperature').text(data.temperature || '--');
    }

    // Chart.js instances
    let heartRateChart, bloodOxygenChart;

    function updateCharts(historyData) {
        const labels = historyData.map(d => new Date(d.timestamp).toLocaleTimeString()).reverse();
        const heartRateData = historyData.map(d => d.heart_rate).reverse();
        const bloodOxygenData = historyData.map(d => d.blood_oxygen).reverse();

        if (heartRateChart) {
            heartRateChart.destroy();
        }
        heartRateChart = new Chart($('#heartRateChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '心率 (BPM)',
                    data: heartRateData,
                    borderColor: 'rgba(255, 99, 132, 1)',
                    tension: 0.1
                }]
            }
        });

        if (bloodOxygenChart) {
            bloodOxygenChart.destroy();
        }
        bloodOxygenChart = new Chart($('#bloodOxygenChart'), {
            type: 'line',
            data: {
                labels: labels,
                datasets: [{
                    label: '血氧 (%)',
                    data: bloodOxygenData,
                    borderColor: 'rgba(54, 162, 235, 1)',
                    tension: 0.1
                }]
            }
        });
    }

    function updateAlertsList(alerts) {
        const alertsList = $('#alertsList');
        alertsList.empty();
        if (alerts.length === 0) {
            alertsList.append('<p class="text-muted">暂无活跃警报</p>');
            return;
        }
        alerts.forEach(function(alert) {
            const alertType = alert.alert_type.toLowerCase();
            let severity = 'info';
            if (alertType.includes('high') || alertType.includes('low')) {
                severity = 'warning';
            }
            if (alertType.includes('critical')) {
                severity = 'danger';
            }
            const alertHtml = `
                <div class="alert alert-${severity}" role="alert">
                  <strong>${alert.alert_type}</strong>: ${alert.message}
                  <small class="float-end">${new Date(alert.timestamp).toLocaleString()}</small>
                </div>
            `;
            alertsList.append(alertHtml);
        });
    }
});

// Utility function to get cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function fetchLatestData(deviceId) {
    const url = `/health-monitor/api/devices/${deviceId}/latest/`;
    $.ajax({
        url: url,
        method: 'GET',
        success: function(data) {
            updateCards(data);
        },
        error: function() {
            console.error("Failed to fetch latest data for device " + deviceId);
        }
    });
}

function fetchHistoryData(deviceId, chartType) {
    const url = `/health-monitor/api/devices/${deviceId}/history/`;
    $.ajax({
        url: url,
        method: 'GET',
        success: function(data) {
            updateUIWithHistory(data);
        },
        error: function() {
            console.error("Failed to fetch history data for device " + deviceId);
        }
    });
}

function fetchAlerts() {
    const url = '/health-monitor/api/alerts/';
    $.ajax({
        url: url,
        method: 'GET',
        dataType: 'json',
        success: function(data) {
            // Handle alerts
        },
        error: function() {
            console.error("Failed to fetch alerts.");
        }
    });
}

// This function will be called when the "Save" button in the modal is clicked
function addDevice() {
    const deviceName = document.getElementById('deviceName').value;
    const deviceType = document.getElementById('deviceType').value;
    const token = localStorage.getItem('apiToken');

    // Basic validation
    if (!deviceName || !deviceType) {
        alert('Please fill out all fields.');
        return;
    }

    fetch('/api/devices/', { // Assuming your API endpoint is at /api/devices/
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Token ${token}`,
            'X-CSRFToken': getCookie('csrftoken') // Function to get CSRF token
        },
        body: JSON.stringify({
            name: deviceName,
            device_type: deviceType,
            is_active: true
        })
    })
    .then(response => {
        if (response.ok) {
            // Close the modal
            var modal = bootstrap.Modal.getInstance(document.getElementById('addDeviceModal'));
            modal.hide();
            // Reload the page to show the new device
            location.reload();
        } else {
            response.json().then(data => {
                alert('Error adding device: ' + JSON.stringify(data));
            });
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An unexpected error occurred.');
    });
} 