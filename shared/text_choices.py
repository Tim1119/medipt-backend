from django.db import models
from django.utils.translation import gettext_lazy as _ 

class CaregiverTypes(models.TextChoices):
    DOCTOR = 'Doctor', _('Doctor')
    NURSE = 'Nurse', _('Nurse')
    PHARMACIST = 'Pharmacist', _('Pharmacist')
    ADMINISTRATIVE_STAFF = 'Administrative Staff', _('Administrative Staff')
    SURGEON = 'Surgeon', _('Surgeon')
    PHYSICIAN = 'Physician', _('Physician')
    DENTIST = 'Dentist', _('Dentist')
    OPTOMETRIST = 'Optometrist', _('Optometrist')
    RADIOLOGIST = 'Radiologist', _('Radiologist')
    PSYCHIATRIST = 'Psychiatrist', _('Psychiatrist')
    PHYSICAL_THERAPIST = 'Physical Therapist', _('Physical Therapist')
    OCCUPATIONAL_THERAPIST = 'Occupational Therapist', _('Occupational Therapist')
    MEDICAL_LAB_TECHNICIAN = 'Medical Lab Technician', _('Medical Lab Technician')
    PARAMEDIC = 'Paramedic', _('Paramedic')
    DIETITIAN = 'Dietitian', _('Dietitian')
    SPEECH_THERAPIST = 'Speech Therapist', _('Speech Therapist')
    MEDICAL_ASSISTANT = 'Medical Assistant', _('Medical Assistant')
    RESPIRATORY_THERAPIST = 'Respiratory Therapist', _('Respiratory Therapist')
    MIDWIFE = 'Midwife', _('Midwife')
    ORTHOPEDIST = 'Orthopedist', _('Orthopedist')
    CARDIOLOGIST = 'Cardiologist', _('Cardiologist')
    NEUROLOGIST = 'Neurologist', _('Neurologist')
    PEDIATRICIAN = 'Pediatrician', _('Pediatrician')
    DERMATOLOGIST = 'Dermatologist', _('Dermatologist')
    GYNECOLOGIST = 'Gynecologist', _('Gynecologist')
    UROLOGIST = 'Urologist', _('Urologist')
    ONCOLOGIST = 'Oncologist', _('Oncologist')
    ENDOCRINOLOGIST = 'Endocrinologist', _('Endocrinologist')
    ANESTHESIOLOGIST = 'Anesthesiologist', _('Anesthesiologist')


class MaritalStatus(models.TextChoices):
    MARRIED = "Married",_("Married")
    SINGLE = "Single",_("Single")
    DIVORCED = "Divorced",_("Divorced")
    WIDOWED = "Widowed",_("Widowed")

class Gender(models.TextChoices):
    MALE = "Male",_("Male")
    FEMALE = "Female",_("Female")
