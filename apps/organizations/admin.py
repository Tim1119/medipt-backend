from django.contrib import admin
from .models import Organization

@admin.register(Organization)
class OrganizationAdmin(admin.ModelAdmin):
    list_display = ('id','name', 'acronym', 'user', 'created_at', 'updated_at')
    search_fields = ('name', 'acronym', 'user__email')
    list_filter = ('created_at', 'updated_at')
    ordering = ('-created_at',)


