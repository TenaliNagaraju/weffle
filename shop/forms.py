from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import CustomerQuery, DeliveryAgent, MenuItem, MenuVariant, Order, SiteSetting, User


class RegisterForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'}))
    phone = forms.CharField(
        max_length=15,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone number'}),
    )
    address = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Delivery address'}),
    )

    class Meta:
        model = User
        fields = ['username', 'email', 'phone', 'address', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in ['username', 'password1', 'password2']:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
        self.fields['username'].widget.attrs['placeholder'] = 'Username'

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.phone = self.cleaned_data['phone']
        user.address = self.cleaned_data['address']
        user.role = User.ROLE_CUSTOMER
        if commit:
            user.save()
        return user


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['username'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Username'})
        self.fields['password'].widget.attrs.update({'class': 'form-control', 'placeholder': 'Password'})


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'address']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class CheckoutForm(forms.Form):
    delivery_address = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}))
    delivery_phone = forms.CharField(max_length=15, widget=forms.TextInput(attrs={'class': 'form-control'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))


class CustomerQueryForm(forms.ModelForm):
    class Meta:
        model = CustomerQuery
        fields = ['subject', 'message', 'order']
        widgets = {
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your message...'}),
            'order': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, user, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['order'].required = False
        self.fields['order'].queryset = Order.objects.filter(customer=user).exclude(
            status=Order.STATUS_CANCELLED
        )
        self.fields['order'].empty_label = 'General query (no specific order)'


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ['category', 'name', 'description', 'image', 'is_available', 'is_featured', 'sort_order']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_featured': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'sort_order': forms.NumberInput(attrs={'class': 'form-control'}),
        }


class MenuVariantForm(forms.ModelForm):
    class Meta:
        model = MenuVariant
        fields = ['shape', 'price', 'price_label', 'is_available']
        widgets = {
            'shape': forms.Select(attrs={'class': 'form-select'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'price_label': forms.TextInput(attrs={'class': 'form-control'}),
            'is_available': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['status', 'delivery_agent']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'delivery_agent': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['delivery_agent'].required = False
        self.fields['delivery_agent'].queryset = User.objects.filter(role=User.ROLE_DELIVERY, is_active=True)
        self.fields['delivery_agent'].empty_label = 'Assign later'


class QueryResponseForm(forms.ModelForm):
    class Meta:
        model = CustomerQuery
        fields = ['status', 'admin_response']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'admin_response': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class DeliveryAgentForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    password = forms.CharField(required=False, widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    first_name = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = DeliveryAgent
        fields = ['phone', 'vehicle_info', 'is_active']
        widgets = {
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'vehicle_info': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }


class AdminPasswordForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    new_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('New passwords do not match.')
        return cleaned


class SiteSettingForm(forms.ModelForm):
    class Meta:
        model = SiteSetting
        fields = ['key', 'value', 'description']
        widgets = {
            'key': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }
