# Generated by Django 5.1.6 on 2025-05-01 13:37

import apps.patients.validators
import autoslug.fields
import django.core.validators
import django.db.models.deletion
import imagekit.models.fields
import shared.validators
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('caregivers', '0001_initial'),
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Patient',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('first_name', models.CharField(max_length=255, verbose_name='Patient First Name')),
                ('last_name', models.CharField(max_length=255, verbose_name='Patient Last Name')),
                ('medical_id', models.CharField(blank=True, max_length=30, null=True, unique=True)),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('marital_status', models.CharField(blank=True, choices=[('Married', 'Married'), ('Single', 'Single'), ('Divorced', 'Divorced'), ('Widowed', 'Widowed')], max_length=30, null=True, verbose_name='Patient Marital Status')),
                ('profile_picture', imagekit.models.fields.ProcessedImageField(blank=True, default='default.png', null=True, upload_to='patient_profile_pictures', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'png', 'jpeg'])])),
                ('gender', models.CharField(blank=True, choices=[('Male', 'Male'), ('Female', 'Female')], max_length=20, null=True)),
                ('phone_number', models.CharField(blank=True, max_length=15, null=True, validators=[shared.validators.validate_phone_number])),
                ('emergency_phone_number', models.CharField(blank=True, max_length=15, null=True, validators=[shared.validators.validate_phone_number])),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='user', unique=True)),
                ('address', models.TextField(blank=True, null=True, verbose_name="Patient's Address")),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Patient',
                'verbose_name_plural': 'Patients',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PatientDiagnosisDetails',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('assessment', models.CharField(max_length=255, verbose_name='Assesssment')),
                ('diagnoses', models.CharField(max_length=255, verbose_name="Patient's Diagnoses")),
                ('medication', models.CharField(max_length=255, verbose_name='Medication')),
                ('health_allergies', models.TextField(blank=True, help_text='Health Allergies (if any)', null=True)),
                ('health_care_center', models.CharField(max_length=255, verbose_name='Health Care Center')),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='patient', unique=True)),
                ('notes', models.TextField()),
                ('caregiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='caregivers.caregiver', verbose_name='Caregiver')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='organizations.organization', verbose_name='Organization')),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Patient Diagnosis Details',
                'verbose_name_plural': 'Patient Diagnosis Details',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PatientMedicalRecord',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('blood_group', models.CharField(choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], help_text='Blood group of the patient', max_length=3)),
                ('genotype', models.CharField(choices=[('AA', 'AA'), ('AS', 'AS'), ('SS', 'SS'), ('AC', 'AC')], help_text='Genotype of the patient', max_length=2)),
                ('weight', models.DecimalField(blank=True, decimal_places=2, help_text='Weight of the patient in kilograms (kg)', max_digits=5, null=True)),
                ('height', models.DecimalField(blank=True, decimal_places=1, help_text='Height of the patient in centimeters (cm)', max_digits=4, null=True)),
                ('allergies', models.TextField(blank=True, help_text='Allergies (if any)', null=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='patient', unique=True)),
                ('patient', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='patients.patient', verbose_name='Patient')),
            ],
            options={
                'verbose_name': 'Patient Medical Record',
                'verbose_name_plural': 'Patient Medical Records',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='VitalSign',
            fields=[
                ('pkid', models.BigAutoField(editable=False, primary_key=True, serialize=False)),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('body_temperature', models.DecimalField(blank=True, decimal_places=1, help_text='Body temperature in degrees Celsius (°C)', max_digits=4, null=True)),
                ('pulse_rate', models.PositiveIntegerField(blank=True, help_text='Pulse rate in beats per minute (bpm)', null=True)),
                ('blood_pressure', models.CharField(blank=True, help_text="Blood pressure in the format 'Systolic/Diastolic' (e.g., '120/80')", max_length=7, null=True, validators=[apps.patients.validators.validate_blood_pressure])),
                ('blood_oxygen', models.DecimalField(blank=True, decimal_places=1, help_text='Blood oxygen level as a percentage (%)', max_digits=4, null=True)),
                ('respiration_rate', models.PositiveIntegerField(blank=True, help_text='Respiration rate in breaths per minute (bpm)', null=True)),
                ('weight', models.DecimalField(blank=True, decimal_places=2, help_text='Weight of the patient in kilograms (kg)', max_digits=5, null=True)),
                ('slug', autoslug.fields.AutoSlugField(editable=False, populate_from='patient_diagnoses_details', unique=True)),
                ('patient_diagnoses_details', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='patients.patientdiagnosisdetails', verbose_name='Patient Diagnosis Details')),
            ],
            options={
                'verbose_name': 'Vital Sign',
                'verbose_name_plural': 'Vital Signs',
                'ordering': ['-created_at'],
            },
        ),
    ]
