from django.contrib import admin
from django.urls import reverse
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

from .models import NewsletterSubscriber


def send_custom_email(request, subscriber, subject, message):
    unsubscribe = request.build_absolute_uri(
        reverse("newsletter_unsubscribe", args=[subscriber.token])
    )

    html = render_to_string("emails/newsletter.html", {
        "email": subscriber.email,
        "message": message,
        "unsubscribe_link": unsubscribe,
    })

    email = EmailMultiAlternatives(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [subscriber.email],
    )

    email.attach_alternative(html, "text/html")
    email.send()


@admin.action(description="Send custom email")
def send_promo(modeladmin, request, queryset):
    for sub in queryset:
        send_custom_email(
            request,  # ✅ must pass request
            sub,
            "Subio Special Offer 🌿",
            "We have launched new organic products. Visit now!"
        )


@admin.register(NewsletterSubscriber)
class NewsletterAdmin(admin.ModelAdmin):
    list_display = ("email", "subscribed_at")
    search_fields = ("email",)
    ordering = ("-subscribed_at",)
    actions = [send_promo]

from django.contrib import admin
from .models import Category

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name","image")