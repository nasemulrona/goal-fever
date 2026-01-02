# payments/views.py
# Temporary views for now
from django.shortcuts import render

def dummy_view(request):
    return render(request, 'payments/dummy.html', {})