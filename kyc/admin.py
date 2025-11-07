from django.contrib import admin
from django.utils.html import format_html
from django import forms
from .models import KYC


class KYCAdminForm(forms.ModelForm):
    """Custom form for KYC admin with better widgets"""
    
    class Meta:
        model = KYC
        fields = '__all__'
        widgets = {
            'certificate_of_incorporation': forms.Textarea(attrs={'rows': 3, 'cols': 80, 'readonly': False}),
            'company_bank_statement': forms.Textarea(attrs={'rows': 3, 'cols': 80, 'readonly': False}),
            'owner_identity_doc': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
            'owner_proof_of_address': forms.Textarea(attrs={'rows': 3, 'cols': 80}),
            'address_1': forms.Textarea(attrs={'rows': 2}),
            'address_2': forms.Textarea(attrs={'rows': 2}),
            'sie_eligibilty': forms.Textarea(attrs={'rows': 3}),
            'notary': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make base64 fields smaller and add helper text
        if self.instance and self.instance.pk:
            # If there's base64 data, show it's there but make field smaller
            if self.instance.certificate_of_incorporation:
                self.fields['certificate_of_incorporation'].widget.attrs.update({
                    'rows': 2,
                    'placeholder': f'Base64 data ({len(self.instance.certificate_of_incorporation):,} chars) - Edit to change'
                })
            if self.instance.company_bank_statement:
                self.fields['company_bank_statement'].widget.attrs.update({
                    'rows': 2,
                    'placeholder': f'Base64 data ({len(self.instance.company_bank_statement):,} chars) - Edit to change'
                })


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    form = KYCAdminForm
    list_display = ('id', 'user', 'status', 'city', 'country', 'submitted_at', 'file_links')
    list_filter = ('status', 'country', 'submitted_at')
    search_fields = ('user__username', 'user__email', 'city', 'country', 'Investee_Company_Email')
    readonly_fields = ('submitted_at', 'file_preview_company_proof', 'base64_file_info')
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'status', 'submitted_at')
        }),
        ('Company Address Information', {
            'fields': ('address_1', 'address_2', 'city', 'zip_code', 'country')
        }),
        ('Company Documents', {
            'fields': (
                'company_proof_of_address',
                'file_preview_company_proof',
                'certificate_of_incorporation',
                'company_bank_statement',
                'base64_file_info',
            ),
            'description': 'Upload company documents. Certificate and Bank Statement can be uploaded as files or base64 encoded data.'
        }),
        ('Owner Documents', {
            'fields': ('owner_identity_doc', 'owner_proof_of_address'),
            'classes': ('collapse',)
        }),
        ('Company Contact Information', {
            'fields': ('Investee_Company_Contact_Number', 'Investee_Company_Email')
        }),
        ('Compliance & Attestation', {
            'fields': (
                'sie_eligibilty',
                'notary',
                'Unlocksley_To_Sign_a_Deed_Of_adherence',
                'I_Agree_To_Investee_Terms',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def file_links(self, obj):
        """Display links to uploaded files in list view"""
        links = []
        if obj.company_proof_of_address:
            url = obj.company_proof_of_address.url
            links.append(f'<a href="{url}" target="_blank">Proof of Address</a>')
        if links:
            return format_html(' | '.join(links))
        return '-'
    file_links.short_description = 'Files'
    
    def file_preview_company_proof(self, obj):
        """Display file preview and download link for company_proof_of_address"""
        if obj.company_proof_of_address:
            url = obj.company_proof_of_address.url
            filename = obj.company_proof_of_address.name.split('/')[-1]
            return format_html(
                '<p><strong>Current file:</strong> <a href="{}" target="_blank">{}</a></p>'
                '<p><small>Upload a new file to replace the existing one.</small></p>',
                url,
                filename
            )
        return format_html('<p><em>No file uploaded yet.</em></p>')
    file_preview_company_proof.short_description = 'File Preview'
    
    def base64_file_info(self, obj):
        """Display information about base64 encoded files"""
        info = []
        if obj.certificate_of_incorporation:
            length = len(obj.certificate_of_incorporation)
            info.append(f'<p><strong>Certificate of Incorporation:</strong> Base64 data ({length:,} characters)</p>')
        if obj.company_bank_statement:
            length = len(obj.company_bank_statement)
            info.append(f'<p><strong>Company Bank Statement:</strong> Base64 data ({length:,} characters)</p>')
        if obj.owner_identity_doc:
            length = len(obj.owner_identity_doc)
            info.append(f'<p><strong>Owner Identity Doc:</strong> Base64 data ({length:,} characters)</p>')
        if obj.owner_proof_of_address:
            length = len(obj.owner_proof_of_address)
            info.append(f'<p><strong>Owner Proof of Address:</strong> Base64 data ({length:,} characters)</p>')
        
        if info:
            return format_html(''.join(info) + '<p><small><em>Note: These fields store base64 encoded data. Consider converting to FileField for better file management.</em></small></p>')
        return format_html('<p><em>No base64 encoded files stored.</em></p>')
    base64_file_info.short_description = 'Base64 Files Information'
    
    class Media:
        css = {
            'all': ('admin/css/kyc_admin.css',)
        }
