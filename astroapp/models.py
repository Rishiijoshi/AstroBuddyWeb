from django.db import models
from django.conf import settings

# Create your models here.
class SavedEvent(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    event_title = models.CharField(max_length=255)
    event_description = models.TextField()
    event_time = models.DateTimeField()
    location = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'event_title', 'event_time')

    def __str__(self):
        return f"{self.event_title} - {self.user.username}"
