from django.db import models

class UserSearch(models.Model):
    session_key = models.CharField(max_length=255, unique=True)
    last_city = models.CharField(max_length=255, blank=True, null=True)
    search_history = models.ManyToManyField('CitySearch', blank=True, related_name='user_searches')

    def __str__(self):
        return f"Session: {self.session_key}, Last City: {self.last_city}"

class CitySearch(models.Model):
    city_name = models.CharField(max_length=255)
    search_count = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.city_name} - {self.search_count} times"

    def increment_count(self):
        self.search_count += 1
        self.save()
