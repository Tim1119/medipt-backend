from django.contrib import admin
from .models import Caregiver

class CaregiverAdmin(admin.ModelAdmin):
    list_display = (
        'first_name', 'last_name', 'organization', 
        'caregiver_type', 'date_of_birth', 
        'marital_status', 'gender', 'staff_number','id'  
    )
    search_fields = ('first_name', 'last_name', 'phone_number', 'organization__name')
    list_filter = ('caregiver_type', 'marital_status', 'gender', 'organization')
    ordering = ('-date_of_birth',)

    fieldsets = (
        (None, {
            'fields': (
                'user', 'organization', 'first_name', 'last_name', 
                'caregiver_type', 'date_of_birth', 'marital_status', 
                'gender', 'phone_number', 'address', 
                'profile_picture', 'staff_number'  
            )
        }),
    )

admin.site.register(Caregiver, CaregiverAdmin)
