from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from .models import CaregiverInvite, InvitationStatus

@admin.register(CaregiverInvite)
class CaregiverInviteAdmin(admin.ModelAdmin):
    list_display = ('email', 'organization', 'role', 'token', 'status', 'created_at', 'expires_at', 'invited_by')
    list_filter = ('status', 'organization', 'role', 'created_at')
    search_fields = ('email', 'organization__name', 'role', 'invited_by__email')
    actions = ['mark_as_accepted']

    # Customize how the object is displayed in the admin form
    fieldsets = (
        (None, {
            'fields': ('email', 'organization', 'role', 'token', 'status', 'expires_at', 'invited_by')
        }),
        (_('Timestamp Information'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # Display only the relevant fields when creating or editing an invitation
    add_fieldsets = (
        (None, {
            'fields': ('email', 'organization', 'role', 'expires_at', 'status')
        }),
    )

    def mark_as_accepted(self, request, queryset):
        """
        Action to mark selected invitations as accepted.
        """
        rows_updated = queryset.update(status=InvitationStatus.ACCEPTED)
        if rows_updated == 1:
            message = _("1 invitation was successfully marked as accepted.")
        else:
            message = _("%s invitations were successfully marked as accepted.") % rows_updated
        self.message_user(request, message)

    mark_as_accepted.short_description = _("Mark selected invitations as accepted")

    def get_queryset(self, request):
        """
        Exclude soft-deleted invitations from the admin interface.
        """
        return super().get_queryset(request).filter(is_deleted=False)

    def get_readonly_fields(self, request, obj=None):
        """
        Make certain fields read-only when editing an existing invitation.
        """
        if obj:  # Editing an existing object
            return ('token', 'created_at', 'updated_at')
        return ()