from django.db import models

# Create your models here.
from django.db import models
from shared.models import TimeStampedUUID
from django.core.validators import FileExtensionValidator
from autoslug import AutoSlugField
from imagekit.models import ProcessedImageField
from imagekit.processors import ResizeToFill
from django.utils.translation import gettext_lazy as _ 
from shared.validators import validate_phone_number
from shared.text_choices import Gender,MaritalStatus,CaregiverTypes
from apps.accounts.models import User
from apps.organizations.models import Organization
from .utils import role_abbreviation
from datetime import date



class Caregiver(TimeStampedUUID):

    user = models.OneToOneField(User,on_delete=models.CASCADE)
    organization = models.ForeignKey(Organization,on_delete=models.CASCADE,verbose_name=_("Organization"))
    first_name = models.CharField(max_length=255,verbose_name=_("Caregiver First Name"))
    last_name = models.CharField(max_length=255,verbose_name=_("Caregiver Last Name"))
    caregiver_type = models.CharField(max_length=30,choices=CaregiverTypes.choices)
    date_of_birth = models.DateField(blank=True,null=True)
    marital_status = models.CharField(max_length=30,choices=MaritalStatus.choices,verbose_name=_("Caregiver Marital Status"),blank=True,null=True)
    profile_picture = ProcessedImageField(upload_to='caregiver_profile_pictures', default='default.png',processors=[ResizeToFill(100, 50)],
                                           format='JPEG',
                                           options={'quality': 80},
                                           validators=[ FileExtensionValidator(allowed_extensions=['jpg', 'png', 'jpeg'])])
    gender = models.CharField(max_length=20,choices=Gender.choices,blank=True,null=True)
    phone_number=models.CharField(max_length=15,validators=[validate_phone_number],blank=True,null=True)
    address = models.TextField(verbose_name=_("Caregiver's Address"),blank=True,null=True)
    slug = AutoSlugField(populate_from='user', unique=True)
    staff_number = models.CharField(max_length=30, unique=True,blank=True,null=True)
    


    class Meta:
        verbose_name = _("Caregiver")
        verbose_name_plural = _("Caregivers")
        ordering = ["-created_at"]

    @property
    def profile_picture_url(self):
        try:
            url = self.profile_picture.url
        except:
            url ='' 
        return url

    def __str__(self):
        return f"Caregiver account for {self.first_name.title()} {self.last_name.title()} for {self.organization.name.title()} Organization"

    def save(self, *args, **kwargs):
        if not self.staff_number:
            self.staff_number = self.generate_unique_staff_number()
        super(Caregiver, self).save(*args, **kwargs)


    def generate_unique_staff_number(self):
        acronym = self.organization.acronym.upper() 
        role_abbr = role_abbreviation.get(self.caregiver_type, "UNK")  # Use UNK if role is not found
        caregiver_count = Caregiver.objects.filter(organization=self.organization, caregiver_type=self.caregiver_type).count() + 1

        while True:
            # Generate the staff number
            staff_number = f"{acronym}_{role_abbr}_{caregiver_count}"
            # Check for conflicts
            if not Caregiver.objects.filter(staff_number=staff_number).exists():
                return staff_number
            caregiver_count += 1  # Increment the count if conflict exists
    
    @property
    def full_name(self):
        return self.last_name + ' ' + self.first_name 
    
    @property
    def full_name_with_role(self):
        """
        Returns the caregiver's full name along with their role/qualification.
        """
        role_abbr = role_abbreviation.get(self.caregiver_type, "")
        return f"{role_abbr.title()} {self.first_name} {self.last_name}"

    def clean(self):
        if self.date_of_birth and self.date_of_birth > date.today():
            raise ValidationError(_("Date of birth cannot be in the future."))
