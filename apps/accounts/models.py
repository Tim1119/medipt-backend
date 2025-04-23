import uuid
from django.db import models
from django.shortcuts import render
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin,Group, Permission
from django.utils.translation import gettext_lazy as _ 
from .managers import CustomUserManager
from .user_roles import UserRoles


class User(AbstractBaseUser,PermissionsMixin):
    """
    User model representing a customer account in the system.

    Attributes:
        pkid (BigAutoField): Primary key for the user.
        id (UUIDField): Unique identifier for the user.
        email (EmailField): Email address of the user.
        role (CharField): Role of the user, defined by UserRoles.
        is_active (BooleanField): Indicates if the user account is active.
        is_invited (BooleanField): Indicates if the user has been invited.
        is_verified (BooleanField): Indicates if a caregiver is verified.
        is_admin (BooleanField): Indicates if the user has admin privileges.
        is_staff (BooleanField): Indicates if the user can access the admin site.
        created_at (DateTimeField): Timestamp of when the account was created.
        updated_at (DateTimeField): Timestamp of the last update to the account.
    """

    pkid = models.BigAutoField(primary_key=True,editable=False)
    id = models.UUIDField(default=uuid.uuid4,editable=False,unique=True)
    email = models.EmailField(verbose_name=_("Email Address"),unique=True,db_index=True)
    role = models.CharField(max_length=20,choices=UserRoles.choices, null=True, blank=True)
    is_active = models.BooleanField(default=False)
    is_invited = models.BooleanField(default=False) # was the user invited to the system
    is_verified = models.BooleanField(default=False) # was the user verified by admin
    is_organization_admin = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
   
    objects = CustomUserManager()

    class Meta:
        verbose_name = _("Customer Account")
        verbose_name_plural = _("Customer Accounts")
        ordering=["-created_at"]
    
    @property
    def get_full_name(self):
        if self.role == UserRoles.ORGANIZATION:
            return self.organization.full_name
        
        if self.role == UserRoles.CAREGIVER:
            return self.caregiver.full_name
        
        if self.role == UserRoles.PATIENT:
            self.patient.full_name
        else:
            return self.email
    
    