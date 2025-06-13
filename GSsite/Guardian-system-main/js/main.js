function getLoginStatus(){
    // TODO: 替换为你的 Django 后端获取登录状态的 API 地址
    $.ajax({
        url: '/health-monitor/check-login/', // 示例 URL，请根据你的 urls.py 调整
        method: 'GET',
        dataType: 'json',
        success: function(response) {
            // 处理服务器返回的数据
            console.log('登录状态：', response);
            if (response && response.is_authenticated){
                $(".loginTrue").show();
                $(".loginFalse").hide(); // 确保未登录元素隐藏
                console.log("已登录");
            } else {
                $(".loginFalse").show();
                $(".loginTrue").hide(); // 确保已登录元素隐藏
                console.log("请先登录！");
                // 如果当前页面需要登录但用户未登录，可以考虑重定向到登录页
                // if (window.location.pathname != '/' && window.location.pathname != '/admin/login/'){ // 示例判断，根据你的需求调整
                //     Qmsg.error("失败：请先登录！");
                //     window.location.href = '/admin/login/'; // 示例重定向到admin登录页
                // }
            }
        },
        error: function(xhr, status, error) {
            console.error('获取登录状态失败：', error);
            // 获取状态失败通常视为未登录
            $(".loginFalse").show();
            $(".loginTrue").hide();
            Qmsg.error("失败：无法获取登录状态！");
        }
    });
}
function logOut(){
    // TODO: 替换为你的 Django 后端登出视图或 API 地址
    $.ajax({
        url: '/auth/logout/', // 示例 URL，使用 Django 内置登出视图
        method: 'POST',
        dataType: 'json', // Django 内置登出视图通常返回重定向或 HTML，可能需要调整dataType或处理方式
        headers: { "X-CSRFToken": getCookie('csrftoken') }, // 添加 CSRF token
        success: function(response, textStatus, xhr) {
            // 处理服务器返回的数据 (Django 内置登出视图成功时会重定向)
             console.log('登出请求成功，检查响应状态：', xhr.status);
            // 登出成功后通常会清除 session cookie 并重定向
             Qmsg.success("提示：登出成功！");
             // TODO: 根据你的需求，登出成功后跳转到指定页面，例如首页或登录页
             window.location.href = '/admin/login/'; // 示例：跳转到admin登录页
        },
         error: function(xhr, status, error) {
            console.error('登出请求失败：', error);
             let errorMessage = '失败：登出失败！';
             // Django 内置登出视图成功时会重定向或返回JSON响应，根据实际情况处理
               Qmsg.error(errorMessage);
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