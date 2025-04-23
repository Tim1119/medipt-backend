from django.urls import path,include
from .views import OrganizationSignupView,VerifyAccount,LoginAccountView,ResendActivationLinkView,PasswordResetRequestView,PasswordResetConfirmView,LogoutView,ChangePasswordView

urlpatterns = [
   path('organization-signup/',OrganizationSignupView.as_view(),name='organization-signup'),
   path('verify-account/<str:token>/',VerifyAccount.as_view(),name='verify-account'),
   path('login/',LoginAccountView.as_view(),name='login-account'),
   path('resend-activation-link/',ResendActivationLinkView.as_view(),name='resend-activation-link'),
   path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
   path('password-reset-confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),
   path('logout/', LogoutView.as_view(), name='logout'),
   path('change-password/', ChangePasswordView.as_view(), name='changed-password-view'),
]

