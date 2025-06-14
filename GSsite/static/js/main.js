function getLoginStatus(){
    // Get API token from localStorage
    const apiToken = localStorage.getItem('apiToken');

    $.ajax({
        url: '/api/check-login/', // Corrected API URL
        method: 'GET',
        dataType: 'json',
        headers: {
            // Add token to request headers
            'Authorization': 'Token ' + apiToken 
        },
        success: function(response) {
            console.log('Login status:', response);
            if (response && response.is_authenticated){
                $(".loginTrue").show();
                $(".loginFalse").hide();
                console.log("Logged in");
            } else {
                // Even if request succeeds, but backend validates as not logged in
                $(".loginFalse").show();
                $(".loginTrue").hide();
                console.log("Please login first!");
            }
        },
        error: function(xhr, status, error) {
            console.error('Failed to get login status:', error);
            // Treat status fetch failure as not logged in
            $(".loginFalse").show();
            $(".loginTrue").hide();
            // Only show error message when server returns 401 or 403, avoid popup on login page
            if (xhr.status === 401 || xhr.status === 403) {
                 Qmsg.error("Error: Your session has expired, please login again!");
            }
        }
    });
}

function logOut(){
    const apiToken = localStorage.getItem('apiToken');
    $.ajax({
        url: '/api/logout/', // Corrected API URL
        method: 'POST',
        dataType: 'json',
        headers: { 
            "X-CSRFToken": getCookie('csrftoken'),
            'Authorization': 'Token ' + apiToken 
        },
        success: function(response) {
             Qmsg.success("Notice: Logout successful!");
             localStorage.removeItem('apiToken'); // Remove token after logout
             window.location.href = '/login/'; // Corrected redirect URL to '/login/'
        },
         error: function(xhr, status, error) {
            console.error('Logout request failed:', error);
            Qmsg.error('Error: Logout failed!');
        }
    });
}
// Get CSRF token (duplicate with function in index.js, consider extracting to a common file)
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
        Qmsg.success("Notice: "+response["msg"]);
        successFunc();
    }else if(response["status"]=="Failed"){
        Qmsg.error("Error: "+response["msg"]);
    } else { // Add a general response handler for cases where backend returns status other than Success or Failed
        if (response && response.message) {
            Qmsg.info("Notice: "+response["message"]); // Assume backend might return info level messages
        } else {
             Qmsg.info("Notice: Operation completed.");
        }
         successFunc(); // Execute success callback even if status is not Success, adjust according to your needs
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
     // TODO: Add logout function to global scope or ensure it's accessible for onclick="logOut()" calls
     window.logOut = logOut;
     // TODO: Add toggleSide function to global scope or ensure it's accessible
     window.toggleSide = toggleSide;
});