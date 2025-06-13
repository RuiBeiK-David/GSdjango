// Web Worker for data processing
self.onmessage = function(e) {
    const batch = e.data;
    const processedData = processBatch(batch);
    self.postMessage(processedData);
};

function processBatch(batch) {
    return batch.map(data => {
        // 数据预处理
        if (data.heart_rate) {
            data.heart_rate = validateHeartRate(data.heart_rate);
        }
        if (data.temperature) {
            data.temperature = validateTemperature(data.temperature);
        }
        if (data.systolic && data.diastolic) {
            const bp = validateBloodPressure(data.systolic, data.diastolic);
            data.systolic = bp.systolic;
            data.diastolic = bp.diastolic;
        }
        
        // 添加处理时间戳
        data.processed_at = new Date().toISOString();
        
        return data;
    });
}

function validateHeartRate(hr) {
    // 心率范围检查（30-220 BPM）
    if (hr < 30) return 30;
    if (hr > 220) return 220;
    return Math.round(hr);
}

function validateTemperature(temp) {
    // 体温范围检查（35-42 °C）
    if (temp < 35) return 35;
    if (temp > 42) return 42;
    return parseFloat(temp.toFixed(1));
}

function validateBloodPressure(systolic, diastolic) {
    // 血压范围检查
    // 收缩压：70-200 mmHg
    // 舒张压：40-130 mmHg
    return {
        systolic: Math.min(Math.max(systolic, 70), 200),
        diastolic: Math.min(Math.max(diastolic, 40), 130)
    };
} 