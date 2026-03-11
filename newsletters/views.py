import logging 
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django.utils import timezone

from newsletters.models import Subscriber, Newsletter
from newsletters.serializers import SubscribeSerializer, NewsletterSerializer
from newsletters.tasks import send_verification_email, send_newsletter_task
from django.http import HttpResponse, HttpResponseRedirect
import urllib.parse
from newsletters.models import Campaign
from django.core.cache import cache

@api_view(['GET'])
@permission_classes([IsAdminUser])
def analytics(request):
    CACHE_KEY = 'newsletter_analytics'
    CACHE_TTL = 300  # 5 minutes

    # Try Redis first
    cached = cache.get(CACHE_KEY)
    if cached:
        return Response({**cached, 'from_cache': True})

    # Cache miss - query the database
    total_subscribers = Subscriber.objects.count()
    active_subscribers = Subscriber.objects.filter(active=True).count()

    newsletter_stats = []
    for newsletter in Newsletter.objects.filter(status='sent'):
        campaigns = Campaign.objects.filter(newsletter=newsletter)
        total = campaigns.count()

        if total == 0:
            continue

        delivered = campaigns.filter(delivered=True).count()
        opened = campaigns.filter(opened=True).count()
        clicked = campaigns.filter(clicked=True).count()

        newsletter_stats.append({
            'id': newsletter.id,
            'title': newsletter.title,
            'sent_date': newsletter.sent_date.isoformat() if newsletter.sent_date else None,
            'total_sent': total,
            'delivered': delivered,
            'opened': opened,
            'clicked': clicked,
            'open_rate': round(opened / delivered * 100, 1) if delivered > 0 else 0,
            'click_rate': round(clicked / delivered * 100, 1) if delivered > 0 else 0,
        })

    data = {
        'total_subscribers': total_subscribers,
        'active_subscribers': active_subscribers,
        'newsletters': newsletter_stats,
        'from_cache': False,
    }

    # Store in Redis for 5 minutes
    cache.set(CACHE_KEY, data, CACHE_TTL)

    return Response(data)

@api_view(['GET'])
@permission_classes([AllowAny])
def track_open(request, campaign_id):
    try:
        campaign = Campaign.objects.get(id=campaign_id)
        if not campaign.opened:
            campaign.opened = True
            campaign.opened_at = timezone.now()
        campaign.open_count += 1
        campaign.save(update_fields=['opened', 'opened_at', 'open_count'])
    except Campaign.DoesNotExist:
        pass

    # Return a real 1x1 transparent GIF
    transparent_gif = (
        b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
        b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x00\x00\x00\x00'
        b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
        b'\x44\x01\x00\x3b'
    )
    return HttpResponse(transparent_gif, content_type='image/gif')


@api_view(['GET'])
@permission_classes([AllowAny])
def track_click(request, campaign_id):
    original_url = request.query_params.get('url', '')

    if not original_url:
        return Response({"error": "No URL"}, status=400)

    decoded_url = urllib.parse.unquote(original_url)

    try:
        campaign = Campaign.objects.get(id=campaign_id)
        if not campaign.clicked:
            campaign.clicked = True
            campaign.clicked_at = timezone.now()
        campaign.click_count += 1
        campaign.save(update_fields=['clicked', 'clicked_at', 'click_count'])
    except Campaign.DoesNotExist:
        pass

    return HttpResponseRedirect(decoded_url)

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([AllowAny])
def subscribe(request):
    serializer = SubscribeSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    existing = Subscriber.objects.filter(email=email).first()
    
    if existing:
        if existing.active:
            return Response(
                {"message": "You're already subscribed!"},
                status=status.HTTP_200_OK
            )
        
    subscriber = serializer.save()
    # logger.info(f"New subscriber: {subscriber.email}")
    
    # Queue verification email - non blocking!
    send_verification_email.delay(subscriber.id)

    return Response(
        {"message": "Please check your email to confirm subscription."},
        status=status.HTTP_201_CREATED
    )

@api_view(['GET', 'POST'])
@permission_classes([IsAdminUser])
def newsletter(request):
    if request.method == 'GET':
        all_newsletters = Newsletter.objects.all()
        serializer = NewsletterSerializer(all_newsletters, many=True)
        return Response(serializer.data)
    
    serializer = NewsletterSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    newsletter = serializer.save()
    return Response(NewsletterSerializer(newsletter).data, status=status.HTTP_201_CREATED)

@api_view(['GET'])
@permission_classes([AllowAny])
def verify_email(request, token):
    try: 
        subscriber = Subscriber.objects.get(verification_token=token)
    except Subscriber.DoesNotExist:
        return Response(
            {"error": "Invalid verification token."},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if subscriber.active:
        return Response({"message": "Email already verified!"})
    
    subscriber.active = True
    subscriber.verified_at = timezone.now()
    subscriber.save()

    return Response({"message": f"Welcome, {subscriber.name}! You're now subscribed."})

@api_view(['GET'])
@permission_classes([AllowAny])
def unsubscribe(request, token):
    try:
        subscriber = Subscriber.objects.get(unsubscribe_token=token)
    except Subscriber.DoesNotExist:
        return Response(
            {"error": "Invalid token."},
            status=status.HTTP_404_NOT_FOUND
        )

    subscriber.active = False
    subscriber.save()

    return Response({"message": "You've been unsubscribed successfully."})

@api_view(['POST'])
@permission_classes([IsAdminUser])
def send_newsletter(request, pk):
    try:
        newsletter = Newsletter.objects.get(pk=pk)
    except Newsletter.DoesNotExist:
        return Response(
            {"error": "Newsletter not found"},
            status=status.HTTP_404_NOT_FOUND
        )

    if newsletter.status == 'sent':
        return Response(
            {"error": "Already sent"},
            status=status.HTTP_400_BAD_REQUEST
        )

    subscriber_count = Subscriber.objects.filter(active=True).count()

    # Queue the task - returns immediately!
    task = send_newsletter_task.delay(newsletter.id)

    return Response({
        "message": f"Newsletter queued for {subscriber_count} subscribers.",
        "task_id": task.id
    })