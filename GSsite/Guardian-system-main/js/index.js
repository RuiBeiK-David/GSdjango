//密码复杂度校验
function pswdCheck(){
    var text= $("#userPswd").val();
    var re =/^(?=.*[a-z])(?=.*\d)[^]{8,16}$/;
    var result =  re.test(text);
    if(!result) {
        $("#pswdCheckSpan").html("密码必须包含数字,字母,且不少于8位");
        return false;
    }else {
        $("#pswdCheckSpan").html("");
        return true;
    }
}
//确认密码
function pswdConf(){
    var text1= $("#userPswd").val();
    var text2= $("#userPswdConf").val();
    if (text2 == text1){
        $("#pswdConfSpan").html("");
        return true;
    }else {
        $("#pswdConfSpan").html("两次输入的密码不一致!");
        return false;
    }
}
//校验邮箱
function emailCheck(){
    var text= $("#userEmail").val();
    var re =/^([\w-\.]+@([\w-]+\.)+[\w-]{2,4})?$/;
    var result =  re.test(text);
    if(!result || !text) {
        $("#emailCheckSpan").html("邮箱格式不正确！");
        return false;
    }else {
        $("#emailCheckSpan").html("");
        return true;
    }
}
//注册表单提交
$('#registBtn').click(function() {
    if (pswdCheck() && pswdConf() && emailCheck()){
        // TODO: 替换为你的 Django 后端用户注册 API 地址
        $.ajax({
            url: '/health-monitor/register/', // 示例 URL，请根据你的 urls.py 调整
            method: 'POST',
            data: $('#formRegist').serialize(),
            dataType: 'json',
            headers: { "X-CSRFToken": getCookie('csrftoken') }, // 添加 CSRF token
            success: function(response) {
                // 处理服务器返回的数据
                console.log(response);
                Msg(response, function() {
                    // 注册成功后可能需要自动登录或提示用户登录
                    Qmsg.success("提示：注册成功，请登录！");
                    $("#registModalDismiss").click();
                     // TODO: 根据后端返回决定是否自动登录或跳转到登录页
                });
            },
            error: function(xhr, status, error) {
                console.error('注册失败：', error);
                let errorMessage = '失败：注册失败！';
                if (xhr.responseJSON && xhr.responseJSON.message) {
                     errorMessage = '失败：' + xhr.responseJSON.message;
                } else if (xhr.responseText) {
                     errorMessage = '失败：' + xhr.responseText;
                }
                Qmsg.error(errorMessage);
            }
        });
    } else{
        Qmsg.error("失败：请检查信息格式！");
    }
});
//登录表单提交
$('#loginBtn').click(function() {
    if ($("#loginAccount").val() && $("#loginPassword").val()){
        // TODO: 替换为你的 Django 后端登录 API 地址，或使用 Django 内置的登录视图 /admin/login/
        $.ajax({
            url: '/health-monitor/login/', // 示例 URL，使用 Django 内置登录视图
            method: 'POST',
            data: $('#formLogin').serialize(),
            dataType: 'json', // 新的登录 API 视图返回的是 JSON
            headers: { "X-CSRFToken": getCookie('csrftoken') }, // 添加 CSRF token
            success: function(response, textStatus, xhr) {
                // 处理服务器返回的数据 (Django 内置登录视图成功时会重定向)
                console.log('登录请求成功：', response);
                // 新的登录 API 视图成功返回 JSON
                if (response && response.status === 'Success') {
                    Qmsg.success("提示：登录成功！");
                    $(".loginFalse").hide();
                    $(".loginTrue").show();
                    $("#loginModalDismiss").click();
                    // TODO: 根据你的需求，登录成功后跳转到指定页面，例如首页或仪表板
                console.log('登录请求成功，检查响应状态：', xhr.status);
                if (xhr.status === 200 || xhr.status === 302) { // 成功可能是 200 或 302 重定向
                     // 如果成功，通常会重定向，Django 会设置 session cookie
                     // 这里简单地刷新页面或跳转到首页
                     Qmsg.success("提示：登录成功！");
                     $(".loginFalse").hide();
                     $(".loginTrue").show();
                     $("#loginModalDismiss").click();
                     // TODO: 根据你的需求，登录成功后跳转到指定页面，例如首页或仪表板
                     window.location.href = '/admin/'; // 示例：跳转到admin页面，你可能想跳转到 '/' 或其他页面
                } else {
                     // 如果响应状态不是成功或重定向，可能是登录失败，尝试解析错误信息
                      let errorMessage = '失败：登录失败！';
                      // TODO: 解析 Django 登录页返回的 HTML，提取错误信息
                      if (response.includes('Please enter a correct')) { // 简单的错误信息检测
                         errorMessage = '失败：用户名或密码不正确！';
                      }
                      Qmsg.error(errorMessage);
                }
            },
            error: function(xhr, status, error) {
                console.error('登录请求失败：', error);
                let errorMessage = '失败：登录请求失败！';
                 if (xhr.responseJSON && xhr.responseJSON.message) {
                     errorMessage = '失败：' + xhr.responseJSON.message;
                } else if (xhr.responseText) {
                      // 尝试解析 Django 登录页返回的 HTML 错误信息
                     if (xhr.responseText.includes('Please enter a correct')) { // 简单的错误信息检测
                         errorMessage = '失败：用户名或密码不正确！';
                      } else {
                         errorMessage = '失败：' + xhr.responseText.substring(0, 100) + '...'; // 避免显示过多HTML
                      }
                }
                Qmsg.error(errorMessage);
            }
        });
    } else{
        Qmsg.error("失败：请输入用户名和密码！");
    }
});
