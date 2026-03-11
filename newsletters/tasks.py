import logging
from celery import shared_task
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task
def send_verification_email(subscriber_id):
    from newsletters.models import Subscriber
    
    try:
        subscriber = Subscriber.objects.get(id=subscriber_id)
    except Subscriber.DoesNotExist:
        logger.error(f"Subscriber {subscriber_id} not found")
        return
    
    # For now just log it - we'll add real email later
    logger.info(f"Sending verification email to {subscriber.email}")
    logger.info(f"Verify link: /api/verify/{subscriber.verification_token}/")


@shared_task(bind=True, max_retries=3)
def send_newsletter_task(self, newsletter_id):
    from newsletters.models import Newsletter, Subscriber, Campaign

    try:
        newsletter = Newsletter.objects.get(id=newsletter_id)
    except Newsletter.DoesNotExist:
        logger.error(f"Newsletter {newsletter_id} not found")
        return

    newsletter.status = 'sending'
    newsletter.save(update_fields=['status'])

    subscribers = list(
        Subscriber.objects.filter(active=True).values_list('id', flat=True)
    )

    if not subscribers:
        logger.warning("No active subscribers")
        newsletter.status = 'sent'
        newsletter.sent_date = timezone.now()
        newsletter.save(update_fields=['status', 'sent_date'])
        return

    # Create campaign records
    campaigns = [
        Campaign(newsletter=newsletter, subscriber_id=sub_id)
        for sub_id in subscribers
    ]
    Campaign.objects.bulk_create(campaigns)

    # Split into batches of 100
    batch_size = 100
    batches = [subscribers[i:i+batch_size] for i in range(0, len(subscribers), batch_size)]

    for batch_num, batch in enumerate(batches, 1):
        send_batch.delay(newsletter_id, batch, batch_num, len(batches))

    newsletter.status = 'sent'
    newsletter.sent_date = timezone.now()
    newsletter.save(update_fields=['status', 'sent_date'])

    logger.info(f"Newsletter {newsletter_id} queued in {len(batches)} batches")


@shared_task(bind=True, max_retries=3)
def send_batch(self, newsletter_id, subscriber_ids, batch_num, total_batches):
    from newsletters.models import Newsletter, Campaign

    logger.info(f"Processing batch {batch_num}/{total_batches}")

    newsletter = Newsletter.objects.get(id=newsletter_id)
    campaigns = Campaign.objects.filter(
        newsletter=newsletter,
        subscriber_id__in=subscriber_ids
    ).select_related('subscriber')

    success = 0
    failed = 0

    for campaign in campaigns:
        try:
            # We'll add real email sending later
            logger.info(f"Sending to {campaign.subscriber.email}")
            campaign.sent_at = timezone.now()
            campaign.delivered = True
            campaign.save(update_fields=['sent_at', 'delivered'])
            success += 1
        except Exception as e:
            campaign.failed = True
            campaign.failure_reason = str(e)
            campaign.save(update_fields=['failed', 'failure_reason'])
            failed += 1
            logger.error(f"Failed: {campaign.subscriber.email} - {e}")

    logger.info(f"Batch {batch_num} done: {success} sent, {failed} failed")