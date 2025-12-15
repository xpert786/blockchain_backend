from django.contrib import admin
from .models import SPVStripeAccount, Payment, PaymentWebhookEvent


@admin.register(SPVStripeAccount)
class SPVStripeAccountAdmin(admin.ModelAdmin):
    list_display = (
        'spv',
        'stripe_account_id',
        'account_status',
        'charges_enabled',
        'payouts_enabled',
        'details_submitted',
        'created_at',
    )
    list_filter = (
        'account_status',
        'charges_enabled',
        'payouts_enabled',
        'details_submitted',
    )
    search_fields = (
        'spv__display_name',
        'stripe_account_id',
    )
    readonly_fields = (
        'stripe_account_id',
        'charges_enabled',
        'payouts_enabled',
        'details_submitted',
        'onboarding_url',
        'created_at',
        'updated_at',
    )
    
    fieldsets = (
        ('SPV Information', {
            'fields': ('spv',)
        }),
        ('Stripe Account', {
            'fields': (
                'stripe_account_id',
                'account_status',
                'charges_enabled',
                'payouts_enabled',
                'details_submitted',
            )
        }),
        ('Onboarding', {
            'fields': (
                'onboarding_url',
                'onboarding_expires_at',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = (
        'payment_id',
        'investor',
        'spv',
        'amount',
        'currency',
        'status',
        'payment_method',
        'platform_fee',
        'net_amount',
        'created_at',
    )
    list_filter = (
        'status',
        'payment_method',
        'currency',
        'created_at',
    )
    search_fields = (
        'payment_id',
        'investor__username',
        'investor__email',
        'spv__display_name',
        'stripe_payment_intent_id',
    )
    readonly_fields = (
        'payment_id',
        'stripe_payment_intent_id',
        'stripe_charge_id',
        'stripe_transfer_id',
        'client_secret',
        'platform_fee',
        'stripe_fee',
        'net_amount',
        'error_code',
        'error_message',
        'created_at',
        'updated_at',
        'completed_at',
    )
    
    fieldsets = (
        ('Payment Info', {
            'fields': (
                'payment_id',
                'investor',
                'spv',
                'investment',
            )
        }),
        ('Amount', {
            'fields': (
                'amount',
                'currency',
                'platform_fee',
                'platform_fee_percentage',
                'stripe_fee',
                'net_amount',
            )
        }),
        ('Status', {
            'fields': (
                'status',
                'payment_method',
            )
        }),
        ('Stripe Details', {
            'fields': (
                'stripe_payment_intent_id',
                'stripe_charge_id',
                'stripe_transfer_id',
                'client_secret',
                'payment_method_id',
            ),
            'classes': ('collapse',)
        }),
        ('Error Info', {
            'fields': (
                'error_code',
                'error_message',
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'description',
                'metadata',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at',
                'completed_at',
            ),
            'classes': ('collapse',)
        }),
    )


@admin.register(PaymentWebhookEvent)
class PaymentWebhookEventAdmin(admin.ModelAdmin):
    list_display = (
        'stripe_event_id',
        'event_type',
        'processed',
        'created_at',
        'processed_at',
    )
    list_filter = (
        'event_type',
        'processed',
        'created_at',
    )
    search_fields = (
        'stripe_event_id',
        'event_type',
    )
    readonly_fields = (
        'stripe_event_id',
        'event_type',
        'payload',
        'processed',
        'error',
        'created_at',
        'processed_at',
    )
