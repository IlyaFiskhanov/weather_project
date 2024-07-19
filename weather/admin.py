from django.contrib import admin
from .models import CitySearch

@admin.register(CitySearch)
class CitySearchAdmin(admin.ModelAdmin):
    list_display = ('city_name', 'search_count')