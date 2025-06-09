from django.contrib.auth.models import User
from django.db import models
from datetime import timedelta

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    cert_created = models.BooleanField(default=False)

class VPNConnectionLog(models.Model):
    username = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    connected_at = models.DateTimeField()
    disconnected_at = models.DateTimeField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.disconnected_at and not self.duration:
            self.duration = self.disconnected_at - self.connected_at
        super().save(*args, **kwargs)

    class Meta:
        unique_together = ('username', 'ip_address', 'connected_at')

    def __str__(self):
        return f"{self.username} - {self.ip_address}"
