
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('email','id', 'role', 'is_active', 'is_verified', 'is_staff', 'created_at')
    list_filter = ('role', 'is_active', 'is_verified', 'is_staff', 'created_at')
    ordering = ('-created_at',)
    readonly_fields = ('id','created_at', 'updated_at')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Role & Status'), {
            'fields': ('role', 'is_active', 'is_verified', 'is_invited', 'is_staff')
        }),
        (_('Permissions'), {
            'fields': ('is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'created_at', 'updated_at')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_active', 'is_staff'),
        }),
    )

    def get_readonly_fields(self, request, obj=None):
        """Make certain fields readonly after creation"""
        if obj:  # editing an existing object
            return self.readonly_fields + ('email',)
        return self.readonly_fields

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of superuser accounts"""
        if obj and obj.is_superuser:
            return False
        return super().has_delete_permission(request, obj)

    def get_list_display(self, request):
        """Add custom columns based on user role"""
        list_display = list(super().get_list_display(request))
        list_display.extend(['get_name', 'get_phone'])
        return list_display

    @admin.display(description=_('Name'))
    def get_name(self, obj):
        """Display name based on user role"""
        if hasattr(obj, 'organization'):
             return obj.organization.name
        if hasattr(obj, 'caregiver'):
            return obj.caregiver.first_name + ' ' + obj.caregiver.last_name
        if hasattr(obj, 'patient'):
            return obj.patient.first_name + ' ' + obj.patient.last_name
        else:
            return obj.email
       

    @admin.display(description=_('Phone'))
    def get_phone(self, obj):
        """Display phone number based on user role"""
        if hasattr(obj, 'organization'):
            return obj.organization.phone_number
        elif hasattr(obj, 'patient'):
            return obj.patient.phone_number
        elif hasattr(obj, 'caregiver'):
            return obj.caregiver.phone_number
        return '-'

    # Custom actions
    actions = ['activate_users', 'deactivate_users', 'verify_users']

    @admin.action(description=_('Activate selected users'))
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} users were successfully activated.')

    @admin.action(description=_('Deactivate selected users'))
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} users were successfully deactivated.')

    @admin.action(description=_('Verify selected users'))
    def verify_users(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} users were successfully verified.')

    class Media:
        css = {
            'all': ('admin/css/custom_admin.css',)
        }