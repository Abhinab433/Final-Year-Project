from django.shortcuts import render, redirect

def cover(request):
    return render(request, 'cover.html')
