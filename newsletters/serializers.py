from rest_framework import serializers
from newsletters.models import Subscriber, Newsletter, Campaign

class SubscribeSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Subscriber
        fields = ['email', 'name']

    def validate_email(self,value):
        return value.lower().strip()
    
class NewsletterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Newsletter
        fields = ['id', 'title', 'content', 'status', 'created_at', 'scheduled_for']
        read_only_fields = ['created_at', 'status']
    