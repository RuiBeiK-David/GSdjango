from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Device, HealthAlert, UserProfile, DataPoint, Alert
from .forms import SignUpForm, UserProfileForm
from django.contrib.auth import login
from django.urls import reverse_lazy
from django.views import generic
from rest_framework.authtoken.models import Token
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def api_logout_view(request):
    """
    API endpoint for user logout. This invalidates the user's token.
    """
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Successfully logged out.'}, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@login_required
def dashboard(request):
    user_devices = Device.objects.filter(user=request.user)
    # Pass the first device to the template context if it exists, otherwise None
    first_device = user_devices.first()
    
    # Get the API token for the logged-in user
    token, _ = Token.objects.get_or_create(user=request.user)

    context = {
        'user_devices': user_devices,
        'selected_device': first_device, # The initially selected device
        'token': token.key
    }
    return render(request, 'health_monitor/dashboard.html', context)

class SignUpView(generic.CreateView):
    form_class = SignUpForm
    success_url = reverse_lazy('login')
    template_name = 'registration/register.html'

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        UserProfile.objects.create(user=user)
        return redirect('dashboard')

@login_required
def device_details(request, device_id):
    device = get_object_or_404(Device, device_id=device_id, user=request.user)
    alerts = HealthAlert.objects.filter(device=device).order_by('-timestamp')
    data_points = DataPoint.objects.filter(device=device).order_by('-timestamp')[:50] # Get recent 50 data points
    
    context = {
        'device': device,
        'alerts': alerts,
        'data_points': data_points,
    }
    return render(request, 'health_monitor/device_details.html', context)

@login_required
def alert_details(request, alert_id):
    alert = get_object_or_404(HealthAlert, id=alert_id, device__user=request.user)
    context = {
        'alert': alert
    }
    return render(request, 'health_monitor/alert_details.html', context)

@login_required
def profile_view(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    token, _ = Token.objects.get_or_create(user=request.user)
    context = {
        'profile': profile,
        'token': token.key
    }
    return render(request, 'health_monitor/profile.html', context)

@login_required
def edit_profile(request):
    profile, created = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = UserProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('profile-page')
    else:
        form = UserProfileForm(instance=profile)
    return render(request, 'health_monitor/edit_profile.html', {'form': form})

def about_view(request):
    return render(request, 'health_monitor/about.html')

    # ... existing code ...

    # ... rest of the existing code ... 