# users/forms.py
from django import forms
from .models import CustomUser, Syndicate

class SyndicateManagerSignupForm(forms.ModelForm):
    syndicate_name = forms.CharField(max_length=255)
    syndicate_description = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'password', 'role']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = 'syndicate'
        if commit:
            user.save()
            # Create Syndicate with form input
            Syndicate.objects.create(
                name=self.cleaned_data['syndicate_name'],
                manager=user,
                description=self.cleaned_data['syndicate_description']
            )
        return user
