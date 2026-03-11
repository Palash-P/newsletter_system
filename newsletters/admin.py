from django.contrib import admin
from .models import Subscriber, Newsletter, Campaign

# Register your models here.
@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'active', 'subscribed_date']

@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'created_at']


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display = ['newsletter', 'subscriber', 'delivered', 'opened', 'clicked']