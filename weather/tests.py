from django.test import TestCase, Client
from django.urls import reverse

class WeatherAppTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.index_url = reverse('index')
        self.autocomplete_url = reverse('city_autocomplete')
# Проверяем GET-запрос к главной странице
    def test_index_view_get(self):
        response = self.client.get(self.index_url)
        self.assertEqual(response.status_code, 200)  
        self.assertTemplateUsed(response, 'weather/index.html') 
        self.assertIn('form', response.context)
 # Проверяем GET-запрос к функции автозаполнения с параметром 'term'
    def test_city_autocomplete(self):
        response = self.client.get(self.autocomplete_url, {'term': 'Старая'})
        self.assertEqual(response.status_code, 200)  
        self.assertEqual(response['Content-Type'], 'application/json') 
        data = response.json()
        self.assertIsInstance(data, list)  
        if data:
            self.assertIn('label', data[0]) 
            self.assertIn('value', data[0]) 
