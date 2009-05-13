"""Forms used by the CMS."""


from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth.models import User, Group
from django.contrib.auth.forms import UserCreationForm as BaseUserCreationForm


class UserCreationForm(BaseUserCreationForm):
    
    """Extended user creation form."""
    
    groups = forms.ModelMultipleChoiceField(queryset=Group.objects.all(),
                                            required=False,
                                            widget=FilteredSelectMultiple("groups", False))
    
    def save(self, commit=True):
        """Saves the user."""
        user = super(UserCreationForm, self).save(commit=False)
        user.is_staff = True
        if commit:
            user.save()
            self.save_m2m()
        return user
    
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email", "groups",)
        
        