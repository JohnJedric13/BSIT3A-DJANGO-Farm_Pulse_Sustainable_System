from django import forms
from django.contrib.auth.models import User


class UserForm(forms.ModelForm):
    password = forms.CharField(
        widget=forms.PasswordInput,
        required=False
    )

    class Meta:
        model = User
        fields = [
            'username',
            'first_name',
            'last_name',
            'email',
            'password',
            'is_staff',
            'is_active',
            'is_superuser',
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Force standard text fields required
        for field in ['username', 'first_name', 'last_name', 'email']:
            if field in self.fields:
                self.fields[field].required = True

        # Password required only when creating
        if not self.instance.pk:
            self.fields['password'].required = True

    def save(self, commit=True):
        user = super().save(commit=False)

        password = self.cleaned_data.get('password')
        if password:
            user.set_password(password)

        if user.is_superuser:
            user.is_staff = True

        if commit:
            user.save()

        return user
