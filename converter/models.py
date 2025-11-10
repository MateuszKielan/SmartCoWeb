from django.db import models

class Support(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    contact = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.created_at.strftime('%Y-%m-%d')})"

    class Meta:
        ordering = ['-created_at']
