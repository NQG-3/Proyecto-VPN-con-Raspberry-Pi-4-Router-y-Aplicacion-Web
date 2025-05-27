from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'password1']

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data['password1']
        user.set_password(raw_password)
        user.is_active = False  # Requiere aprobación del admin
        user._plain_password = raw_password
        if commit:
            user.save()
        return user

class AdminUserForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'is_active', 'is_staff']

    def save(self, commit=True):
        user = super().save(commit=False)
        raw_password = self.cleaned_data['password']
        user.set_password(raw_password)
        if commit:
            user.save()
        return user
