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
            # Text fields
            'address_1': forms.Textarea(attrs={'rows': 2}),
            'address_2': forms.Textarea(attrs={'rows': 2}),
            'sie_eligibilty': forms.Textarea(attrs={'rows': 3}),
            'notary': forms.Textarea(attrs={'rows': 2}),
            # File fields use default FileInput widget (no need to specify)
        }


@admin.register(KYC)
class KYCAdmin(admin.ModelAdmin):
    form = KYCAdminForm
    list_display = ('id', 'user', 'status', 'city', 'country', 'submitted_at', 'file_links')
    list_filter = ('status', 'country', 'submitted_at')
    search_fields = ('user__username', 'user__email', 'company_legal_name', 'your_position', 'city', 'country', 'Investee_Company_Email')
    readonly_fields = (
        'submitted_at', 
        'file_preview_certificate',
        'file_preview_bank_statement',
        'file_preview_company_proof',
        'file_preview_owner_identity',
        'file_preview_owner_proof',
    )
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'status', 'submitted_at')
        }),
        ('Company Information', {
            'fields': ('company_legal_name', 'your_position')
        }),
        ('Company Address Information', {
            'fields': ('address_1', 'address_2', 'city', 'zip_code', 'country')
        }),
        ('Company Documents', {
            'fields': (
                'certificate_of_incorporation',
                'file_preview_certificate',
                'company_bank_statement',
                'file_preview_bank_statement',
                'company_proof_of_address',
                'file_preview_company_proof',
            ),
            'description': 'Upload company documents as files.'
        }),
        ('Owner Documents', {
            'fields': (
                'owner_identity_doc',
                'file_preview_owner_identity',
                'owner_proof_of_address',
                'file_preview_owner_proof',
            ),
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
        file_fields = [
            ('certificate_of_incorporation', 'Certificate'),
            ('company_bank_statement', 'Bank Statement'),
            ('company_proof_of_address', 'Proof of Address'),
            ('owner_identity_doc', 'Owner ID'),
            ('owner_proof_of_address', 'Owner Proof'),
        ]
        
        for field_name, display_name in file_fields:
            file_field = getattr(obj, field_name, None)
            if file_field:
                try:
                    url = file_field.url
                    links.append(f'<a href="{url}" target="_blank">{display_name}</a>')
                except (ValueError, AttributeError):
                    pass
        
        if links:
            return format_html(' | '.join(links))
        return '-'
    file_links.short_description = 'Files'
    
    def _file_preview(self, obj, field_name, field_display_name):
        """Helper method to generate file preview HTML"""
        file_field = getattr(obj, field_name, None)
        if file_field:
            try:
                url = file_field.url
                filename = file_field.name.split('/')[-1]
                file_size = file_field.size if hasattr(file_field, 'size') else 'Unknown'
                return format_html(
                    '<p><strong>Current file:</strong> <a href="{}" target="_blank">{}</a> '
                    '<small>({} bytes)</small></p>'
                    '<p><small>Upload a new file to replace the existing one.</small></p>',
                    url,
                    filename,
                    file_size
                )
            except (ValueError, AttributeError):
                return format_html('<p><em>File exists but URL unavailable.</em></p>')
        return format_html('<p><em>No file uploaded yet.</em></p>')
    
    def file_preview_certificate(self, obj):
        """Display file preview for certificate_of_incorporation"""
        return self._file_preview(obj, 'certificate_of_incorporation', 'Certificate of Incorporation')
    file_preview_certificate.short_description = 'Certificate Preview'
    
    def file_preview_bank_statement(self, obj):
        """Display file preview for company_bank_statement"""
        return self._file_preview(obj, 'company_bank_statement', 'Company Bank Statement')
    file_preview_bank_statement.short_description = 'Bank Statement Preview'
    
    def file_preview_company_proof(self, obj):
        """Display file preview for company_proof_of_address"""
        return self._file_preview(obj, 'company_proof_of_address', 'Company Proof of Address')
    file_preview_company_proof.short_description = 'Proof of Address Preview'
    
    def file_preview_owner_identity(self, obj):
        """Display file preview for owner_identity_doc"""
        return self._file_preview(obj, 'owner_identity_doc', 'Owner Identity Document')
    file_preview_owner_identity.short_description = 'Owner Identity Preview'
    
    def file_preview_owner_proof(self, obj):
        """Display file preview for owner_proof_of_address"""
        return self._file_preview(obj, 'owner_proof_of_address', 'Owner Proof of Address')
    file_preview_owner_proof.short_description = 'Owner Proof Preview'
    
    class Media:
        css = {
            'all': ('admin/css/kyc_admin.css',)
        }
