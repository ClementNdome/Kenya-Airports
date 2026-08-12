# obstacle_compliance/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from django.urls import reverse_lazy
from django.utils.safestring import mark_safe

from .models import UserProfile


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control', 'autofocus': True}),
        help_text='Required. A valid email address is needed to activate your account.',
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class VerificationAwareAuthenticationForm(AuthenticationForm):
    """Login form that explains why an unverified account cannot log in."""

    def clean(self):
        username = self.cleaned_data.get('username')
        password = self.cleaned_data.get('password')

        if username is not None and password:
            user = User.objects.filter(username=username).first()
            if user is not None and not user.is_active:
                profile = UserProfile.objects.filter(user=user).first()
                if profile is not None and not profile.email_verified:
                    resend_url = '{}?username={}'.format(
                        reverse_lazy('obstacle_compliance:resend_verification'), username
                    )
                    raise forms.ValidationError(
                        mark_safe(
                            'Your account is not yet verified. Check your email for the '
                            'activation link, or <a href="{}">resend the verification email</a>.'
                            .format(resend_url)
                        ),
                        code='unverified',
                    )
        return super().clean()
