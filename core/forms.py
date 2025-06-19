# forms.py

from django import forms
from django.contrib.auth.models import User
from .models import UserDetail, Restaurant

class UserDetailFullForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control'}))

    class Meta:
        model = UserDetail
        fields = ['firstname', 'surname', 'mobileno']
        widgets = {
            'firstname': forms.TextInput(attrs={'class': 'form-control'}),
            'surname': forms.TextInput(attrs={'class': 'form-control'}),
            'mobileno': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        # Extract the user-related fields
        username = self.cleaned_data.pop("username")
        password = self.cleaned_data.pop("password")
        email = self.cleaned_data.pop("email")

        if self.instance.pk and hasattr(self.instance, 'user'):
            user = self.instance.user
            user.username = username
            user.email = email
            if password:
                user.set_password(password)
            if commit:
                user.save()
        else:
            # Create the user
            user = User.objects.create_user(username=username, password=password, email=email)

        # Create the user detail object
        user_detail = super().save(commit=False)
        user_detail.user = user

        if commit:
            user_detail.save()

        return user_detail