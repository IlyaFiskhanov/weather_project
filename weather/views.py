from django.shortcuts import render, redirect
from django.http import JsonResponse
import requests
from .forms import CityForm
from .models import UserSearch, CitySearch
from datetime import datetime, timedelta

def update_days():
    current_date = datetime.now()
    days = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
    updated_days = []
    updated_days.append(current_date.strftime(f"{days[current_date.weekday()]} (%d.%m)"))
    for i in range(1, 7):
        next_date = current_date + timedelta(days=i)
        updated_days.append(next_date.strftime(f"{days[next_date.weekday()]} (%d.%m)"))
    return updated_days

def get_weather(city_name):
    geocode_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1"
    geocode_response = requests.get(geocode_url)
    
    if geocode_response.status_code == 200:
        geocode_data = geocode_response.json()
        if "results" in geocode_data and len(geocode_data["results"]) > 0:
            latitude = geocode_data["results"][0]["latitude"]
            longitude = geocode_data["results"][0]["longitude"]
            weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max,temperature_2m_min&timezone=auto"
            weather_response = requests.get(weather_url)
            if weather_response.status_code == 200:
                weather_data = weather_response.json()
                weather_data["results"] = geocode_data["results"]
                days = update_days()
                weather_data['daily']['weekdays'] = days
                zipped_weather = zip(
                    weather_data['daily']['weekdays'],
                    weather_data['daily']['temperature_2m_max'],
                    weather_data['daily']['temperature_2m_min']
                )
                weather_data['zipped'] = list(zipped_weather)
                
                return weather_data
    return None

def index(request):
    error = None
    weather_data = None
    city_name = None
    form = CityForm()

    session_key = request.session.session_key
    if not session_key:
        request.session.save()
        session_key = request.session.session_key

    try:
        user_search = UserSearch.objects.get(session_key=session_key)
        last_city = user_search.last_city
    except UserSearch.DoesNotExist:
        last_city = None

    if request.method == 'GET' and 'city' in request.GET:
        city_name = request.GET.get('city')
        weather_data = get_weather(city_name)
        if weather_data:
            city_stat, created = CitySearch.objects.get_or_create(city_name=city_name)
            if not created:
                city_stat.search_count += 1
                city_stat.save()
        else:
            error = 'Не удалось получить данные о погоде.'

    elif request.method == 'POST':
        form = CityForm(request.POST)
        if form.is_valid():
            city = form.cleaned_data['city']
            response = requests.get(f'https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1&language=ru&format=json')
            if response.status_code == 200 and response.json().get('results'):
                location = response.json()['results'][0]
                city_name = location['name']
                latitude = location['latitude']
                longitude = location['longitude']
                
                weather_response = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={latitude}&longitude={longitude}&daily=temperature_2m_max,temperature_2m_min&timezone=auto')
                if weather_response.status_code == 200:
                    weather_data = weather_response.json()
                    days = update_days()
                    weather_data['daily']['weekdays'] = days
                    
                    zipped_weather = zip(
                        weather_data['daily']['weekdays'],
                        weather_data['daily']['temperature_2m_max'],
                        weather_data['daily']['temperature_2m_min']
                    )
                    weather_data['zipped'] = list(zipped_weather)

                    UserSearch.objects.update_or_create(
                        session_key=session_key,
                        defaults={'last_city': city_name}
                    )

                    city_stat, created = CitySearch.objects.get_or_create(city_name=city_name)
                    if not created:
                        city_stat.search_count += 1
                        city_stat.save()
                else:
                    error = 'Не удалось получить данные о погоде.'
            else:
                error = 'Не удалось найти указанный город.'

    return render(request, 'weather/index.html', {
        'form': form, 
        'weather': weather_data, 
        'city_name': city_name, 
        'error': error,
        'last_city': last_city
    })

def city_autocomplete(request):
    if 'term' in request.GET:
        query = request.GET.get('term')
        response = requests.get(f'https://geocoding-api.open-meteo.com/v1/search?name={query}&count=5&language=ru&format=json')
        if response.status_code == 200:
            results = response.json().get('results', [])
            suggestions = [{'label': f"{result['name']}, {result.get('admin1', '')}, {result['country']}", 'value': result['name']} for result in results]
            return JsonResponse(suggestions, safe=False)
    return JsonResponse([], safe=False)


def city_statistics(request):
    city_stats = CitySearch.objects.all().order_by('-search_count')
    return render(request, 'weather/city_statistics.html', {
        'city_stats': city_stats
    })

