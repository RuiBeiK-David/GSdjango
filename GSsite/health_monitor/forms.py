from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile

class SignUpForm(UserCreationForm):
    """
    自定义注册表单，添加电子邮件字段并为表单字段设置样式
    """
    username = forms.CharField(
        max_length=150,
        help_text='必填。150个字符或者更少。只能包含字母、数字和@/./+/-/_ 字符。',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '用户名'})
    )
    
    email = forms.EmailField(
        max_length=254,
        required=True,
        help_text='必填。请输入有效的电子邮箱地址。',
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': '电子邮箱'})
    )
    
    password1 = forms.CharField(
        label='密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '密码'})
    )
    
    password2 = forms.CharField(
        label='确认密码',
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '确认密码'})
    )
    
    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
    
    def clean_email(self):
        """验证邮箱是否已被使用"""
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('该电子邮箱已被使用')
        return email

class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ('name', 'gender', 'phone_number', 'id_number')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'id_number': forms.TextInput(attrs={'class': 'form-control'}),
        } 