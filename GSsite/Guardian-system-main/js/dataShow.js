$(document).ready(function(){
    // 查询用户所绑定的监测人信息 (已在patient_detail_view中处理并传递到模板)
    // updatePatient(); // 这个函数现在应该只在patient_list页面使用

    // TODO: 根据需要在 patient_detail_view 渲染的页面加载设备数据
    // 示例：页面加载时如果已有设备，加载默认设备的初始数据
    const initialDeviceId = $('#deviceSelect').val(); // 假设设备 ID 从设备选择框获取
    if (initialDeviceId) {
        updateHealthDataForDevice(initialDeviceId);
    }

    // 示例：定时更新实时数据 (例如每10秒)
    // setInterval(function() { updateHealthDataForDevice($('#deviceSelect').val()); }, 10000); // uncomment to enable periodic updates

    $("#btn_edit_profile").click(function(){
        $(".show_profile").hide();
        $(".edit_profile").show();
        $("#btn_edit_profile").hide();
        $("#btn_profile_submit_cancel").show();
        //编辑时附带原本信息
        $("#edit_name").val($("#name").html());
        $("#edit_gender").val($("#gender").html());
        $("#edit_age").val($("#age").html());
        $("#edit_phone_number").val($("#phone_number").html());
        $("#edit_id_number").val($("#id_number").html());
    });
    $("#btn_cancel_profile").click(function(){
        $(".edit_profile").hide();
        $("#btn_profile_submit_cancel").hide();
        $(".show_profile").show();
        $("#btn_edit_profile").show();
    });
    //提交用户修改信息
    $("#btn_submit_patient_profile").click(function(){
        if (phoneNumCheck()){
            $.ajax({
                url: '../php/editPatientProfile.php',
                method: 'POST',
                data: 'Request=Edit&'+window.location.search.substring(1)+'&'+$('#formEditPatientProfile').serialize(),
                dataType: 'json',
                success: function(response) {
                    // 处理服务器返回的数据
                    console.log(response);
                    Msg(response, function() {
                        $("#btn_cancel_profile").click();
                        $("#name").html($("#edit_name").val());
                        $("#age").html($("#edit_age").val());
                        $("#gender").html($("#edit_gender").val());
                        $("#phone_number").html($("#edit_phone_number").val());
                        $("#id_number").html($("#edit_id_number").val());
                    });
                },
                error: function(xhr, status, error) {
                    console.log('Ajax连接失败');
                }
            });
        } else{
            Qmsg.error("失败：请检查信息格式！");
        }
    })

    // 确保 ECharts 实例在调用 updateCharts 之前已经初始化
    // TODO: 确认 ECharts 的初始化位置，如果不在 $(document).ready 中，需要确保它们在调用此处代码时已经存在
     // 在 $(document).ready 中初始化 ECharts 实例 (如果它们还没有被初始化的话)
     if (typeof eegChart === 'undefined') { eegChart = echarts.init(document.getElementById('eeg-chart'), null, { width: 600, height: 400 }); }
     if (typeof pulseChart === 'undefined') { pulseChart = echarts.init(document.getElementById('pulse-chart'), null, { width: 600, height: 400 }); }
     if (typeof ecgChart === 'undefined') { ecgChart = echarts.init(document.getElementById('ecg-chart'), null, { width: 600, height: 400 }); }
     if (typeof bpChart === 'undefined') { bpChart = echarts.init(document.getElementById('bp-chart'), null, { width: 600, height: 400 }); }
     if (spo2Chart === 'undefined') { spo2Chart = echarts.init(document.getElementById('spo2-chart'), null, { width: 600, height: 400 }); }

    // 示例：当设备选择变化时加载数据 (假设在 dashboard.html 中有一个 id 为 deviceSelect 的下拉框)
    $('#deviceSelect').change(function() {
        const selectedDeviceId = $(this).val();
        updateHealthDataForDevice(selectedDeviceId);
    });

    // 示例：页面加载时如果已有设备，加载默认设备的初始数据
     const initialDeviceId = $('#deviceSelect').val(); // 假设设备 ID 从设备选择框获取
     if (initialDeviceId) {
         updateHealthDataForDevice(initialDeviceId);
     }

    // 示例：定时更新实时数据 (例如每10秒)
    // setInterval(function() { updateHealthDataForDevice($('#deviceSelect').val()); }, 10000); // uncomment to enable periodic updates
});

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
      var pair = vars[i].split("=");
      if (pair[0] == variable) {
        return pair[1];
      }
    }
    return false;
}
//校验手机号
function phoneNumCheck(){
    var text= $("#edit_phone_number").val();
    //这个正则表达式可以匹配以1开头，第二位为3-9之间的数字，后面跟着9个数字的手机号码。
    var re = /^1[3456789]\d{9}$/;
    if(re.test(text) || !text) {
        $("#phoneNumCheckSpan").html("");
        return true;
    }else {
        $("#phoneNumCheckSpan").html("手机号格式不正确！");
        return false;
    }
}
//定义一个函数，用于获取并更新数据
function updateHealthDataForDevice(deviceId) {
    // TODO: 替换为你的 Django 后端获取健康数据的 API 地址
    $.ajax({
        url: '/health/get-data/' + deviceId + '/', // 示例 URL，请根据你的 health_monitor.urls.py 调整
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            // 处理服务器返回的数据
            console.log('健康数据：', response);
            // TODO: 根据后端返回的数据格式更新卡片和图表
            if (response && response.length > 0) {
                const latestData = response[response.length - 1]; // 获取最新数据
                $('#heartRate').text(latestData.heart_rate !== null ? latestData.heart_rate : '--');
                $('#bloodPressure').text(latestData.blood_pressure_systolic !== null && latestData.blood_pressure_diastolic !== null ? latestData.blood_pressure_systolic + '/' + latestData.blood_pressure_diastolic : '--/--');
                $('#bloodOxygen').text(latestData.blood_oxygen !== null ? latestData.blood_oxygen : '--');
                $('#temperature').text(latestData.temperature !== null ? latestData.temperature : '--');

                // 示例：更新图表数据 (需要 Chart.js 或 ECharts 实例以及对应的更新逻辑)
                updateCharts(response); // 调用函数更新所有图表

            } else {
                 // 没有数据时清空或显示默认值
                $('#heartRate').text('--');
                $('#bloodPressure').text('--/--');
                $('#bloodOxygen').text('--');
                $('#temperature').text('--');
                 // 清空图表数据
                 clearCharts();
            }
        },
        error: function(xhr, status, error) {
            console.error('获取健康数据失败：', error);
            Qmsg.error('失败：获取健康数据失败！');
             // 获取失败时清空或显示默认值
            $('#heartRate').text('--');
            $('#bloodPressure').text('--/--');
            $('#bloodOxygen').text('--');
            $('#temperature').text('--');
             clearCharts();
        }
    });
}

// TODO: 根据你的图表库 (ECharts) 实现更新所有图表的逻辑
function updateCharts(data) {
    // 示例：根据从后端获取的数据更新 ECharts 图表
    // 这需要知道你的 ECharts 实例名称和数据结构
    // 例如，如果你有 heartRateChart, pulseChart, ecgChart, bpChart, spo2Chart ECharts 实例
    // 并且后端返回的数据是一个包含多个健康数据对象的数组，每个对象有 timestamp, heart_rate, blood_pressure_systolic, blood_pressure_diastolic, blood_oxygen, temperature 等字段

    const timestamps = data.map(item => new Date(item.timestamp).toLocaleTimeString());
    const heartRates = data.map(item => item.heart_rate);
    const bloodOxygens = data.map(item => item.blood_oxygen);
    // TODO: 提取其他图表所需的数据 (BP, ECG, Pulse) 并添加到相应的数组
    // const bloodPressuresSystolic = data.map(item => item.blood_pressure_systolic);
    // const bloodPressuresDiastolic = data.map(item => item.blood_pressure_diastolic);

    // 更新脑电图 (示例：假设后端数据中没有脑电数据，或者你需要从其他API获取)
    // 如果你的后端提供脑电数据，请修改此部分
    // if (eegChart) {
    //     eegChart.setOption({
    //         xAxis: { data: timestamps },
    //         series: [{ data: /* 脑电数据数组 */ }] // 替换为实际的脑电数据
    //     });
    // }

    // 更新心率图表
    if (pulseChart) { // 原始代码中 pulseChart 可能用于心率，根据你的ECharts实例名和用途调整
        pulseChart.setOption({
            xAxis: { data: timestamps },
            series: [{
                name: '心率', // 确保名称与你的 ECharts 配置一致
                data: heartRates
            }]
        });
    }

    // 更新血氧图表
    if (spo2Chart) { // 原始代码中 spo2Chart 用于血氧
        spo2Chart.setOption({
            xAxis: { data: timestamps },
            series: [{
                 name: '血氧', // 确保名称与你的 ECharts 配置一致
                 data: bloodOxygens
            }]
        });
    }

     // TODO: 更新其他图表 (心电 ecgChart, 血压 bpChart) 的逻辑
     // 示例：更新血压图表 (假设你需要收缩压和舒张压两条线)
     // if (bpChart) {
     //     bpChart.setOption({
     //          xAxis: { data: timestamps },
     //          series: [
     //              { name: '收缩压', type: 'line', data: bloodPressuresSystolic },
     //              { name: '舒张压', type: 'line', data: bloodPressuresDiastolic }
     //          ]
     //     });
     // }
     // TODO: 更新心电图表 ecgChart 的逻辑

    // TODO: 根据你的原始 dataShow.js 中初始化图表的代码，确保这里的图表实例名称 (eegChart, pulseChart, ecgChart, bpChart, spo2Chart) 和配置是正确的
}

// TODO: 实现清空图表数据的逻辑
function clearCharts() {
    if (eegChart) { eegChart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] }); }
    if (pulseChart) { pulseChart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] }); }
    if (ecgChart) { ecgChart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] }); }
    if (bpChart) { bpChart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] }); }
    if (spo2Chart) { spo2Chart.setOption({ xAxis: { data: [] }, series: [{ data: [] }] }); }
}

// 模拟数据
var data = [];
for (var i = 0; i < 100; i++) {
    data.push(Math.random() * 10 - 5);
}
// 模拟数据更新
setInterval(function () {
    for (var i = 0; i < 10; i++) {
        data.shift();
        data.push(Math.random() * 10 - 5);
    }
    eegChart.setOption({
        series: [
            {
                data: data
            }
        ]
    });
}, 300);
console.log("断点");

// 脑电图配置
var eegOption = {
    color: [
        '#5470c6',
    ],
    title: {
        text: '脑电'
    },
    tooltip: {
        show: false,
        trigger: 'axis',
        axisPointer: {
            type: 'line'
        }
    },
    xAxis: {
        type: 'category',
        boundaryGap: false,
        data: []
    },
    yAxis: {
        type: 'value',
        axisLine: {
            show: false
        },
        axisTick: {
            show: false
        },
        axisLabel: {
            show: false
        },
        splitLine: {
            show: false
        }
    },
    series: [
        {
            type: 'line',
            showSymbol: false,
            hoverAnimation: false,
            data: data
        }
    ]
};

// 脉搏图配置
var pulseOption = {
    color: [
        '#5470c6',
    ],
    title: {
        text: '脉搏'
    },
    tooltip: {},
    legend: {
        data:[]
    },
    xAxis: {
        data: []
    },
    yAxis: {},
    series: [{
        name: '脉搏',
        type: 'line',
        data: [25, 20, 40, 8, 23, 15,26,10,30,7]
    }]
};

//心电图配置
var ecgOption = {
    color: [
        '#5470c6',
    ],
    title: {
        text: '心电'
    },
    tooltip: {},
    legend: {
        data:[]
    },
    xAxis: {
        data: []
    },
    yAxis: {},
    series: [{
        name: '心电',
        type: 'line',
        data: [5, 20, 36, 10, 10, 20]
    }]
};

//血压图配置
var bpOption = {
    color: [
        '#5470c6',
    ],
    title: {
        text: '血压'
    },
    tooltip: {},
    legend: {
        data:[]
    },
    xAxis: {
        data: []
    },
    yAxis: {},
    series: [{
        name: '血压',
        type: 'line',
        data: [5, 20, 36, 10, 10, 20]
    }]
};

//血氧图配置
var spo2Option = {
    color: [
        '#5470c6',
    ],
    title: {
        text: '血氧'
    },
    tooltip: {},
    legend: {
        data:[]
    },
    xAxis: {
        data: []
    },
    yAxis: {},
    series: [{
        name: '血氧',
        type: 'line',
        data: [5, 20, 36, 10, 10, 20]
    }]
};

// 使用刚指定的配置项和数据绘制各个图表。
eegChart.setOption(eegOption);
pulseChart.setOption(pulseOption);
ecgChart.setOption(ecgOption);
bpChart.setOption(bpOption);
spo2Chart.setOption(spo2Option);