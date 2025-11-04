from django.shortcuts import render

def home(request):
    return render(request, 'principal/home.html')
