function getLoginStatus(){
    // 从 localStorage 获取 API token
    const apiToken = localStorage.getItem('apiToken');

    $.ajax({
        url: '/api/check-login/', // 修正API URL
        method: 'GET',
        dataType: 'json',
        headers: {
            // 将 token 添加到请求头
            'Authorization': 'Token ' + apiToken 
        },
        success: function(response) {
            console.log('登录状态：', response);
            if (response && response.is_authenticated){
                $(".loginTrue").show();
                $(".loginFalse").hide();
                console.log("已登录");
            } else {
                // 即使请求成功，但后端验证为未登录
                $(".loginFalse").show();
                $(".loginTrue").hide();
                console.log("请先登录！");
            }
        },
        error: function(xhr, status, error) {
            console.error('获取登录状态失败：', error);
            // 获取状态失败视为未登录
            $(".loginFalse").show();
            $(".loginTrue").hide();
            // 只有当服务器返回401或403时才显示错误消息，避免在登录页也弹窗
            if (xhr.status === 401 || xhr.status === 403) {
                 Qmsg.error("失败：您的会话已过期，请重新登录！");
            }
        }
    });
}

function logOut(){
    const apiToken = localStorage.getItem('apiToken');
    $.ajax({
        url: '/api/logout/', // 修正API URL
        method: 'POST',
        dataType: 'json',
        headers: { 
            "X-CSRFToken": getCookie('csrftoken'),
            'Authorization': 'Token ' + apiToken 
        },
        success: function(response) {
             Qmsg.success("提示：登出成功！");
             localStorage.removeItem('apiToken'); // 登出后移除token
             window.location.href = '/accounts/login/'; // Redirect to the login page
        },
         error: function(xhr, status, error) {
            console.error('登出请求失败：', error);
            Qmsg.error('失败：登出失败！');
        }
    });
}
// 获取 CSRF token (与 index.js 中的函数重复，可以考虑提取到公共文件)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
function Msg(response, successFunc){
    if (response["status"]=="Success"){
        Qmsg.success("提示："+response["msg"]);
        successFunc();
    }else if(response["status"]=="Failed"){
        Qmsg.error("失败："+response["msg"]);
    } else { // 添加一个通用的响应处理，以防后端返回的 status 不是 Success 或 Failed
        if (response && response.message) {
            Qmsg.info("提示："+response["message"]); // 假设后端可能返回 info 级别的消息
        } else {
             Qmsg.info("提示：操作完成。");
        }
         successFunc(); // 即使 status 不是 Success，也执行成功回调，根据你的需求调整
    }
}
function toggleSide(){
    $('.side_collapse').toggle();
    $(".toggle-width").toggleClass('sidebar-icon-only');
    // TODO: Adjust main content margin and header logo width based on sidebar state (similar to dashboard.html)
}
$(document).ready(function() {
    getLoginStatus();
    $('.nav-pills .nav-link').hover(function() {
        $(this).addClass('active');
    }, function() {
        if (!$(this).is($(".fix"))) {
            $(this).removeClass('active');
        }
    });
     // TODO: 将 logout 函数添加到全局作用域或确保其可访问，以便 onclick="logOut()" 调用
     window.logOut = logOut;
     // TODO: 将 toggleSide 函数添加到全局作用域或确保其可访问
     window.toggleSide = toggleSide;
});