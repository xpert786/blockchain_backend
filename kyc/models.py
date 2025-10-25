from django.db import models
from users.models import CustomUser  # if you want to link KYC to a user

class KYC(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    certificate_of_incorporation = models.TextField(blank=True, null=True)
    company_bank_statement = models.TextField(blank=True, null=True)
    address_1 = models.TextField(blank=True, null=True)
    address_2 = models.TextField(blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    zip_code = models.CharField(max_length=20, blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True)
    company_proof_of_address = models.FileField(blank=True, null=True)
    owner_identity_doc = models.TextField(blank=True, null=True)
    owner_proof_of_address = models.TextField(blank=True, null=True)
    sie_eligibilty = models.TextField(blank=True, null=True)
    notary = models.TextField(blank=True, null=True)
    Unlocksley_To_Sign_a_Deed_Of_adherence = models.BooleanField(default=False)
    Investee_Company_Contact_Number = models.CharField(max_length=20, blank=True, null=True)
    Investee_Company_Email = models.EmailField(blank=True, null=True)
    I_Agree_To_Investee_Terms = models.BooleanField(blank=True, null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='Pending')
    submitted_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return f"{self.user.username} - {self.status}"
