import uuid 
from django.db import models 
from django.utils import timezone

class Subscriber(models.Model):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=255)
    subscribed_date = models.DateTimeField(default=timezone.now)
    active = models.BooleanField(default=False)

    verification_token = models.UUIDField(default=uuid.uuid4, unique=True)
    unsubscribe_token = models.UUIDField(default=uuid.uuid4, unique=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.name} <{self.email}>"
    
class Newsletter(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sending', 'Sending'),
        ('sent', 'Sent'),
    ]

    title = models.CharField(max_length=255)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    sent_date = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')

    def __str__(self):
        return f"{self.title} <{self.status}>" 
    
class Campaign(models.Model):
    newsletter = models.ForeignKey(
        Newsletter, on_delete=models.CASCADE, related_name='campaigns'
    )
    subscriber = models.ForeignKey(
        Subscriber, on_delete=models.CASCADE, related_name='campaigns'
    )

    sent_at = models.DateTimeField(null=True, blank=True)
    delivered = models.BooleanField(default=False)
    failed = models.BooleanField(default=False)
    failure_reason = models.TextField(blank=True)
    

    opened = models.BooleanField(default=False)
    opened_at = models.DateTimeField(null=True, blank=True)
    open_count = models.IntegerField(default=0)


    clicked = models.BooleanField(default=False)
    clicked_at = models.DateTimeField(null=True, blank=True)
    click_count = models.IntegerField(default=0)


    class Meta:
        unique_together = ['newsletter', 'subscriber']

    def __str__(self):
        return f"{self.newsletter.title} → {self.subscriber.email}"
