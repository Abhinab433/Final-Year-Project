from django.shortcuts import render, redirect, get_object_or_404
from accounts.models import CustomUser
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django import forms
from django.db.models import Count
import requests
import json 
from chat.models import ChatUsageLog, GeneratedImage
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator

# Check if user is a staff member
def is_staff(user):
    return user.is_staff

@login_required
def home(request):
    users = CustomUser.objects.annotate(chat_usage_count=Count('chatusagelog')).all()
    chat_logs = ChatUsageLog.objects.filter(user=request.user)
    images = GeneratedImage.objects.filter(user=request.user).order_by('-created_at')

    paginator = Paginator(chat_logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    labels = [user.username for user in users]
    data = [user.chat_usage_count for user in users]
    
    context = {
        'labels': json.dumps(labels),
        'data': json.dumps(data),
        'users': users,
        'chat_logs': page_obj,
        'images': images,
    }

    return render(request, 'dashboard/home.html', context)

# Form for adding/editing users
class UserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password']
        widgets = {
            'password': forms.PasswordInput(),
        }

# Restrict access to staff users
@user_passes_test(is_staff)
def view_users(request):
    users = CustomUser.objects.all()
    return render(request, 'dashboard/view_users.html', {'users': users})

@user_passes_test(is_staff)
def manage_users(request):
    users = CustomUser.objects.all()
    return render(request, 'dashboard/manage_users.html', {'users': users})

@user_passes_test(is_staff)
def add_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.password = make_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'User added successfully!')
            return redirect('manage_users')
    else:
        form = UserForm()
    
    return render(request, 'dashboard/add_user.html', {'form': form})

@user_passes_test(is_staff)
def edit_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
            user = form.save(commit=False)
            if form.cleaned_data['password']:
                user.password = make_password(form.cleaned_data['password'])
            user.save()
            messages.success(request, 'User updated successfully!')
            return redirect('manage_users')
    else:
        form = UserForm(instance=user)

    return render(request, 'dashboard/edit_user.html', {'form': form, 'user': user})

@user_passes_test(is_staff)
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, 'User deleted successfully!')
    return redirect('manage_users')

API_KEY = 'pub_65664ef813889ca68ab9dce6d154eca8901a2'

def news(request):
    country = 'np'
    category = request.GET.get('category')

    if category:
        url = f'https://newsdata.io/api/1/latest?country={country}&apikey={API_KEY}&category={category}'
    else:
        url = f'https://newsdata.io/api/1/latest?country={country}&apikey={API_KEY}'

    response = requests.get(url)
    data = response.json()

    articles = data.get('results', []) if data.get('status') == 'success' else []
    DEFAULT_IMAGE_URL = "/static/images/cover.jpg"

    for article in articles:
        article['image_url'] = article.get('image_url') or DEFAULT_IMAGE_URL
        article['source_name'] = article.get('source_name', '')
        article['creator'] = article.get('creator', 'Unknown')
        article['pubDate'] = article.get('pubDate', '')
        article['link'] = article.get('link', '')

    return render(request, 'dashboard/news.html', {'articles': articles})

@user_passes_test(is_staff)
def user_chat_logs(request):
    chat_logs = ChatUsageLog.objects.select_related('user').all()
    
    paginator = Paginator(chat_logs, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'dashboard/user_chat_logs.html', {'chat_logs': page_obj})
