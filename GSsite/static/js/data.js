// 数据处理和缓存
class HealthDataProcessor {
    constructor() {
        this.cache = new Map();
        this.dataQueue = [];
        this.batchSize = 100;
        this.processingInterval = 5000; // 5秒处理一次
        this.initWebSocket();
        this.startProcessing();
    }

    // 初始化WebSocket连接
    initWebSocket() {
        this.ws = new WebSocket(
            'ws://' + window.location.host + '/ws/health_data/'
        );

        this.ws.onmessage = (e) => {
            const data = JSON.parse(e.data);
            this.handleIncomingData(data);
        };

        this.ws.onclose = () => {
            console.log('WebSocket连接已关闭，尝试重新连接...');
            setTimeout(() => this.initWebSocket(), 2000);
        };
    }

    // 处理传入的数据
    handleIncomingData(data) {
        // 添加时间戳
        data.timestamp = new Date().toISOString();
        
        // 添加到队列
        this.dataQueue.push(data);
        
        // 更新缓存
        this.updateCache(data);
        
        // 触发数据更新事件
        this.triggerDataUpdate(data);
        
        // 检查是否需要批量处理
        if (this.dataQueue.length >= this.batchSize) {
            this.processBatch();
        }
    }

    // 更新缓存
    updateCache(data) {
        const deviceId = data.device_id;
        if (!this.cache.has(deviceId)) {
            this.cache.set(deviceId, {
                recentData: [],
                stats: {
                    minHeartRate: Infinity,
                    maxHeartRate: -Infinity,
                    avgHeartRate: 0,
                    minTemp: Infinity,
                    maxTemp: -Infinity,
                    avgTemp: 0,
                }
            });
        }

        const deviceCache = this.cache.get(deviceId);
        deviceCache.recentData.push(data);
        
        // 只保留最近100条数据
        if (deviceCache.recentData.length > 100) {
            deviceCache.recentData.shift();
        }
        
        // 更新统计信息
        this.updateStats(deviceCache, data);
    }

    // 更新统计信息
    updateStats(deviceCache, data) {
        const stats = deviceCache.stats;
        
        // 心率统计
        if (data.heart_rate) {
            stats.minHeartRate = Math.min(stats.minHeartRate, data.heart_rate);
            stats.maxHeartRate = Math.max(stats.maxHeartRate, data.heart_rate);
            stats.avgHeartRate = this.calculateAverage(
                deviceCache.recentData.map(d => d.heart_rate)
            );
        }
        
        // 体温统计
        if (data.temperature) {
            stats.minTemp = Math.min(stats.minTemp, data.temperature);
            stats.maxTemp = Math.max(stats.maxTemp, data.temperature);
            stats.avgTemp = this.calculateAverage(
                deviceCache.recentData.map(d => d.temperature)
            );
        }
    }

    // 计算平均值
    calculateAverage(values) {
        const validValues = values.filter(v => v !== null && v !== undefined);
        return validValues.length > 0
            ? validValues.reduce((a, b) => a + b) / validValues.length
            : 0;
    }

    // 批量处理数据
    processBatch() {
        if (this.dataQueue.length === 0) return;

        const batch = this.dataQueue.splice(0, this.batchSize);
        
        // 使用Web Worker处理数据
        if (window.Worker) {
            const worker = new Worker('/static/js/dataWorker.js');
            worker.postMessage(batch);
            worker.onmessage = (e) => {
                const processedData = e.data;
                this.saveBatchToServer(processedData);
            };
        } else {
            // 如果不支持Web Worker，直接处理
            this.saveBatchToServer(batch);
        }
    }

    // 将批量数据保存到服务器
    saveBatchToServer(batch) {
        fetch('/api/health-data/batch/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: JSON.stringify(batch)
        })
        .then(response => response.json())
        .then(data => {
            console.log('批量数据已保存', data);
        })
        .catch(error => {
            console.error('保存批量数据时出错:', error);
            // 保存失败时，将数据放回队列
            this.dataQueue.unshift(...batch);
        });
    }

    // 开始定期处理数据
    startProcessing() {
        setInterval(() => {
            if (this.dataQueue.length > 0) {
                this.processBatch();
            }
        }, this.processingInterval);
    }

    // 触发数据更新事件
    triggerDataUpdate(data) {
        const event = new CustomEvent('healthDataUpdate', { detail: data });
        window.dispatchEvent(event);
    }

    // 获取设备的缓存数据
    getDeviceCache(deviceId) {
        return this.cache.get(deviceId);
    }

    // 获取设备的统计信息
    getDeviceStats(deviceId) {
        const cache = this.cache.get(deviceId);
        return cache ? cache.stats : null;
    }

    // 获取设备的最新数据
    getLatestData(deviceId) {
        const cache = this.cache.get(deviceId);
        return cache && cache.recentData.length > 0
            ? cache.recentData[cache.recentData.length - 1]
            : null;
    }
}

// 获取CSRF Token
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

// 导出数据处理器实例
const healthDataProcessor = new HealthDataProcessor();
export default healthDataProcessor;

$(document).ready(function(){
    //查询用户所绑定的监测人信息
    updatePatient();

    //添加监测人表单提交
    $('#addPatientBtn').click(function() {
        if ($("#patientName").val() && $("#patientAge").val()) { // 简单的表单验证
            // TODO: 替换为你的 Django 后端添加监测人的 API 地址
            $.ajax({
                url: '/health/patients/add/', // 示例 URL，请根据你的 urls.py 调整
                method: 'POST',
                data: $('#formAddPatient').serialize(), // 发送表单数据
                dataType: 'json',
                headers: { "X-CSRFToken": getCookie('csrftoken') }, // 添加 CSRF token
                success: function(response) {
                    // 处理服务器返回的数据
                    console.log(response);
                    Msg(response, function() {
                        $("#btnAddPatientCancel").click();
                        updatePatient(); // 刷新列表
                    });
                },
                error: function(xhr, status, error) {
                    console.error('添加监测人失败：', error);
                     let errorMessage = '失败：添加监测人失败！';
                     if (xhr.responseJSON && xhr.responseJSON.message) {
                          errorMessage = '失败：' + xhr.responseJSON.message;
                     } else if (xhr.responseText) {
                          errorMessage = '失败：' + xhr.responseText;
                     }
                    Qmsg.error(errorMessage);
                }
            });
        } else {
             Qmsg.error("失败：请填写监测人姓名和年龄！");
        }
    });

    // 使用事件委托处理删除按钮的点击事件
    $('#patientList').on('click', '.delete-patient-btn', function() {
        const patientId = $(this).data('patient-id');
        if (confirm('确定要删除该监测人吗？')) {
            deletePatient(patientId);
        }
    });
});

//查询用户所绑定的监测人信息
function updatePatient(){
    // TODO: 替换为你的 Django 后端获取监测人列表的 API 地址
    $.ajax({
        url: '/health/patients/', // 示例 URL，请根据你的 urls.py 调整
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            // 处理服务器返回的数据
            console.log(response);
            $("#patientList").html(""); // 清空现有列表
            if (response && response.status === 'Success' && response.data) {
                if (response.data.length === 0) {
                    $("#patientList").append('<tr><td colspan="4" class="text-center">暂无监测人信息</td></tr>');
                } else {
                    Msg(response, function() { // 使用 Msg 函数处理 Success/Failed 状态
                        response.data.forEach(function(element, index) {
                            // 修改这里，添加 data-patient-id 属性，移除 onclick
                            var newHTML = '<tr>' +
                                '<td>' + (index + 1) + '</td>' +
                                '<td>' + element['name'] + '</td>' +
                                '<td>' + element['age'] + '</td>' +
                                '<td>' +
                                    '<a type="button" class="btn btn-primary btnList" href="javascript:void(0);" onclick="toShowPage(' + element['id'] + ')">查看</a>' + // 查看功能暂时仍然使用 ID 参数
                                    '<a type="button" class="btn btn-danger delete-patient-btn" href="javascript:void(0);" data-patient-id="' + element['id'] + '">删除</a>' + // 添加 class 和 data 属性
                                '</td>' +
                                '</tr>';
                            $("#patientList").append(newHTML);
                        });
                    });
                }
            } else if (response && response.status === 'Failed') {
                 Qmsg.error("失败：" + response.message);
            } else {
                 Qmsg.error("失败：获取监测人列表时发生未知错误。");
            }
        },
        error: function(xhr, status, error) {
            console.error('获取监测人列表失败：', error);
            Qmsg.error("失败：无法连接到服务器获取监测人列表。");
             $("#patientList").html('<tr><td colspan="4" class="text-center text-danger">加载失败，请重试</td></tr>');
        }
    });
}

//传参并转至病人数据展示
// TODO: 这个函数需要修改，使其导航到由 Django 渲染的包含病人数据的页面
// 目前仍然传递 ID，但目标 URL 需要调整
function toShowPage(patientId){
    window.location.href = '/health/data/'+patientId+'/'; // 示例 URL，需要根据你的 urls.py 调整
}

// 删除操作函数，接收 patientId
function deletePatient(patientId){
    // TODO: 替换为你的 Django 后端删除监测人的 API 地址
    $.ajax({
        url: '/health/patients/delete/', // 示例 URL，请根据你的 urls.py 调整
        method: 'POST',
        data: { 'patient_id': patientId }, // 发送监测人 ID
        dataType: 'json',
        headers: { "X-CSRFToken": getCookie('csrftoken') }, // 添加 CSRF token
        success: function(response) {
            // 处理服务器返回的数据
            console.log(response);
            Msg(response, function() {
                updatePatient(); // 刷新列表
            });
        },
        error: function(xhr, status, error) {
            console.error('删除监测人失败：', error);
             let errorMessage = '失败：删除监测人失败！';
             if (xhr.responseJSON && xhr.responseJSON.message) {
                  errorMessage = '失败：' + xhr.responseJSON.message;
             } else if (xhr.responseText) {
                  errorMessage = '失败：' + xhr.responseText;
             }
            Qmsg.error(errorMessage);
        }
    });
}

// Msg 函数 (从 main.js 或 index.js 复制，可以考虑提取到公共文件)
function Msg(response, successFunc){
    if (response && response["status"]=="Success"){
        Qmsg.success("提示："+response["message"]); // 使用 message 字段，与后端一致
        if (successFunc) successFunc();
    }else if(response && response["status"]=="Failed"){
        Qmsg.error("失败："+response["message"]); // 使用 message 字段
    } else { // 通用处理，以防后端返回的 status 不是 Success 或 Failed
        if (response && (response.message || response.msg)) {
            Qmsg.info("提示："+(response.message || response.msg));
        } else {
             Qmsg.info("提示：操作完成。");
        }
        // 即使 status 不是 Success，也执行成功回调，根据你的需求调整
        if (successFunc) successFunc();
    }
}