from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

# Create your views here.

@csrf_exempt # 开发方便，生产环境请移除或正确处理 CSRF
def auth_status(request):
    """
    API: 获取当前用户认证状态
    """
    is_authenticated = request.user.is_authenticated
    return JsonResponse({'is_authenticated': is_authenticated})

# TODO: 添加其他主项目的视图（如果需要） 