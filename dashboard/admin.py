from django.contrib import admin
from .models import *  # Ensure 'Notes' is the correct model name

# Register your models here
admin.site.register(Notes)
admin.site.register(Homework)
admin.site.register(Todo)