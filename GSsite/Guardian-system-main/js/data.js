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