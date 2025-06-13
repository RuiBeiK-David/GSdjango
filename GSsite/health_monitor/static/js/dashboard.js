// 全局变量
let heartRateChart = null;
let bloodPressureChart = null;

// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 初始化图表
    initCharts();
    
    // 加载初始数据
    loadDashboardData();
    
    // 设置定时刷新
    setInterval(loadDashboardData, 30000); // 每30秒刷新一次
    
    // 绑定事件处理器
    bindEventHandlers();
    
    // 处理导航
    handleNavigation();
});

// 初始化图表
function initCharts() {
    const heartRateCtx = document.getElementById('heartRateChart').getContext('2d');
    const bloodPressureCtx = document.getElementById('bloodPressureChart').getContext('2d');
    
    heartRateChart = new Chart(heartRateCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '心率',
                data: [],
                borderColor: 'rgb(75, 192, 192)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
    
    bloodPressureChart = new Chart(bloodPressureCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: '收缩压',
                data: [],
                borderColor: 'rgb(255, 99, 132)',
                tension: 0.1
            }, {
                label: '舒张压',
                data: [],
                borderColor: 'rgb(54, 162, 235)',
                tension: 0.1
            }]
        },
        options: {
            responsive: true,
            scales: {
                y: {
                    beginAtZero: true
                }
            }
        }
    });
}

// 加载仪表板数据
async function loadDashboardData() {
    try {
        // 获取概览数据
        const overviewResponse = await fetch('/api/health-data/overview/');
        const overviewData = await overviewResponse.json();
        
        // 更新状态卡片
        document.getElementById('activeDevicesCount').textContent = overviewData.active_devices;
        document.getElementById('pendingAlertsCount').textContent = overviewData.pending_alerts;
        document.getElementById('todayDataPointsCount').textContent = overviewData.today_data_points;
        document.getElementById('criticalAlertsCount').textContent = overviewData.critical_alerts;
        
        // 更新图表数据
        updateCharts();
        
        // 更新设备列表
        if (document.getElementById('devices').classList.contains('active')) {
            loadDevices();
        }
        
        // 更新警报列表
        if (document.getElementById('alerts').classList.contains('active')) {
            loadAlerts();
        }
    } catch (error) {
        console.error('加载仪表板数据失败:', error);
        showError('加载数据失败，请稍后重试');
    }
}

// 更新图表数据
async function updateCharts() {
    try {
        const response = await fetch('/api/health-data/chart-data/');
        const data = await response.json();
        
        // 更新心率图表
        heartRateChart.data.labels = data.timestamps;
        heartRateChart.data.datasets[0].data = data.heart_rates;
        heartRateChart.update();
        
        // 更新血压图表
        bloodPressureChart.data.labels = data.timestamps;
        bloodPressureChart.data.datasets[0].data = data.systolic_pressures;
        bloodPressureChart.data.datasets[1].data = data.diastolic_pressures;
        bloodPressureChart.update();
    } catch (error) {
        console.error('更新图表失败:', error);
    }
}

// 加载设备列表
async function loadDevices() {
    try {
        const response = await fetch('/api/devices/');
        const devices = await response.json();
        
        const tbody = document.getElementById('devicesList');
        tbody.innerHTML = '';
        
        devices.forEach(device => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${device.device_id}</td>
                <td>${device.name}</td>
                <td>
                    <span class="badge ${device.is_active ? 'bg-success' : 'bg-danger'}">
                        ${device.is_active ? '在线' : '离线'}
                    </span>
                </td>
                <td>${new Date(device.last_heartbeat).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="editDevice(${device.id})">
                        <i class="fa fa-edit"></i>
                    </button>
                    <button class="btn btn-sm btn-outline-danger" onclick="deleteDevice(${device.id})">
                        <i class="fa fa-trash"></i>
                    </button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch (error) {
        console.error('加载设备列表失败:', error);
        showError('加载设备列表失败，请稍后重试');
    }
}

// 加载警报列表
async function loadAlerts() {
    try {
        const response = await fetch('/api/alerts/');
        const alerts = await response.json();
        
        const alertsList = document.getElementById('alertsList');
        alertsList.innerHTML = '';
        
        alerts.forEach(alert => {
            const alertDiv = document.createElement('div');
            alertDiv.className = `alert alert-${getSeverityClass(alert.severity)} ${alert.is_active ? '' : 'alert-resolved'}`;
            alertDiv.innerHTML = `
                <div class="d-flex justify-content-between align-items-center">
                    <div>
                        <h5 class="alert-heading">${alert.alert_type}</h5>
                        <p class="mb-0">${alert.message}</p>
                        <small class="text-muted">
                            ${new Date(alert.timestamp).toLocaleString()} - 
                            设备: ${alert.device_name}
                        </small>
                    </div>
                    ${alert.is_active ? `
                        <button class="btn btn-sm btn-outline-secondary" onclick="resolveAlert(${alert.id})">
                            <i class="fa fa-check"></i> 解决
                        </button>
                    ` : ''}
                </div>
            `;
            alertsList.appendChild(alertDiv);
        });
    } catch (error) {
        console.error('加载警报列表失败:', error);
        showError('加载警报列表失败，请稍后重试');
    }
}

// 加载阈值设置
async function loadThresholds() {
    try {
        const response = await fetch('/api/thresholds/');
        const thresholds = await response.json();
        
        const form = document.getElementById('thresholdsForm');
        form.innerHTML = '';
        
        thresholds.forEach(threshold => {
            const fieldset = document.createElement('fieldset');
            fieldset.innerHTML = `
                <legend>${threshold.device_name}</legend>
                <input type="hidden" name="device_id" value="${threshold.device}">
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label">心率范围</label>
                        <div class="input-group">
                            <input type="number" class="form-control" name="heart_rate_min" value="${threshold.heart_rate_min}">
                            <span class="input-group-text">-</span>
                            <input type="number" class="form-control" name="heart_rate_max" value="${threshold.heart_rate_max}">
                        </div>
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label">收缩压范围</label>
                        <div class="input-group">
                            <input type="number" class="form-control" name="blood_pressure_systolic_min" value="${threshold.blood_pressure_systolic_min}">
                            <span class="input-group-text">-</span>
                            <input type="number" class="form-control" name="blood_pressure_systolic_max" value="${threshold.blood_pressure_systolic_max}">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">舒张压范围</label>
                        <div class="input-group">
                            <input type="number" class="form-control" name="blood_pressure_diastolic_min" value="${threshold.blood_pressure_diastolic_min}">
                            <span class="input-group-text">-</span>
                            <input type="number" class="form-control" name="blood_pressure_diastolic_max" value="${threshold.blood_pressure_diastolic_max}">
                        </div>
                    </div>
                </div>
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label">体温范围</label>
                        <div class="input-group">
                            <input type="number" step="0.1" class="form-control" name="body_temperature_min" value="${threshold.body_temperature_min}">
                            <span class="input-group-text">-</span>
                            <input type="number" step="0.1" class="form-control" name="body_temperature_max" value="${threshold.body_temperature_max}">
                        </div>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">最低血氧</label>
                        <input type="number" class="form-control" name="blood_oxygen_min" value="${threshold.blood_oxygen_min}">
                    </div>
                </div>
            `;
            form.appendChild(fieldset);
        });
    } catch (error) {
        console.error('加载阈值设置失败:', error);
        showError('加载阈值设置失败，请稍后重试');
    }
}

// 绑定事件处理器
function bindEventHandlers() {
    // 保存设备按钮
    document.getElementById('saveDevice').addEventListener('click', async () => {
        const deviceId = document.getElementById('deviceId').value;
        const deviceName = document.getElementById('deviceName').value;
        
        try {
            const response = await fetch('/api/devices/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify({
                    device_id: deviceId,
                    name: deviceName
                })
            });
            
            if (response.ok) {
                $('#addDeviceModal').modal('hide');
                loadDevices();
                showSuccess('设备添加成功');
            } else {
                throw new Error('添加设备失败');
            }
        } catch (error) {
            console.error('添加设备失败:', error);
            showError('添加设备失败，请稍后重试');
        }
    });
    
    // 保存阈值按钮
    document.getElementById('saveThresholds').addEventListener('click', async () => {
        const form = document.getElementById('thresholdsForm');
        const formData = new FormData(form);
        
        try {
            const response = await fetch('/api/thresholds/batch-update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCookie('csrftoken')
                },
                body: JSON.stringify(Object.fromEntries(formData))
            });
            
            if (response.ok) {
                showSuccess('阈值设置已保存');
            } else {
                throw new Error('保存阈值设置失败');
            }
        } catch (error) {
            console.error('保存阈值设置失败:', error);
            showError('保存阈值设置失败，请稍后重试');
        }
    });
    
    // 刷新警报按钮
    document.getElementById('refreshAlerts').addEventListener('click', loadAlerts);
}

// 处理导航
function handleNavigation() {
    const sections = document.querySelectorAll('.section');
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            
            // 移除所有活动状态
            navLinks.forEach(l => l.classList.remove('active'));
            sections.forEach(s => s.classList.add('d-none'));
            
            // 设置当前活动状态
            link.classList.add('active');
            const targetId = link.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);
            targetSection.classList.remove('d-none');
            
            // 加载相应的数据
            if (targetId === 'devices') {
                loadDevices();
            } else if (targetId === 'alerts') {
                loadAlerts();
            } else if (targetId === 'settings') {
                loadThresholds();
            }
        });
    });
}

// 辅助函数
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

function getSeverityClass(severity) {
    switch (severity) {
        case 'CRITICAL':
            return 'danger';
        case 'HIGH':
            return 'warning';
        case 'MEDIUM':
            return 'info';
        case 'LOW':
            return 'success';
        default:
            return 'secondary';
    }
}

function showSuccess(message) {
    // 实现成功提示
    alert(message); // 临时使用alert，应该替换为更好的提示组件
}

function showError(message) {
    // 实现错误提示
    alert(message); // 临时使用alert，应该替换为更好的提示组件
}

// 删除设备
async function deleteDevice(deviceId) {
    if (!confirm('确定要删除此设备吗？')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/devices/${deviceId}/`, {
            method: 'DELETE',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            loadDevices();
            showSuccess('设备已删除');
        } else {
            throw new Error('删除设备失败');
        }
    } catch (error) {
        console.error('删除设备失败:', error);
        showError('删除设备失败，请稍后重试');
    }
}

// 解决警报
async function resolveAlert(alertId) {
    try {
        const response = await fetch(`/api/alerts/${alertId}/resolve/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCookie('csrftoken')
            }
        });
        
        if (response.ok) {
            loadAlerts();
            showSuccess('警报已解决');
        } else {
            throw new Error('解决警报失败');
        }
    } catch (error) {
        console.error('解决警报失败:', error);
        showError('解决警报失败，请稍后重试');
    }
} 