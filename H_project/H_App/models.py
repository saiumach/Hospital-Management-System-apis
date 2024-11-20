from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
# import datetime
# from django.conf import settings
from django.utils import timezone
import uuid
# import random
from django.utils import timezone
from django.utils.timezone import now

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)


class DoctorSlot(models.Model):
    doctor = models.ForeignKey('CustomUser', related_name='doctor_slots', on_delete=models.CASCADE)
    date = models.DateField(default=now)
    slot = models.CharField(
        choices=[
            ('10:00 AM - 11:00 AM', '10:00 AM - 11:00 AM'),
            ('11:00 AM - 12:00 PM', '11:00 AM - 12:00 PM'),
            ('1:00 PM - 2:00 PM', '1:00 PM - 2:00 PM'),
            ('2:00 PM - 3:00 PM', '2:00 PM - 3:00 PM'),
            ('3:00 PM - 4:00 PM', '3:00 PM - 4:00 PM'),
            ('4:00 PM - 5:00 PM', '4:00 PM - 5:00 PM'),
        ],
        max_length=50,
    )
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.doctor.name} | {self.slot}"


class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPES = (
        ('doctor', 'Doctor'),
        ('patient', 'Patient'),
        ('receptionist', 'Receptionist'),
    )

    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=12, choices=USER_TYPES)
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    specialization = models.CharField(max_length=100, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)

    assigned_doctor = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='assigned_patients')
    assigned_slot = models.ForeignKey(DoctorSlot, null=True, blank=True, on_delete=models.SET_NULL)

    # Use a ManyToManyField to allow multiple slots for a doctor
    available_slots = models.ManyToManyField(DoctorSlot, blank=True, related_name='slots')

    problem = models.CharField(max_length=255, blank=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'user_type']

    def __str__(self):
        return self.email

class Patient(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    problem = models.CharField(max_length=255)
    assigned_doctor = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name="patients")
    assigned_slot = models.CharField(max_length=50, blank=True, null=True)
    contact_number = models.CharField(max_length=15, blank=True, null=True)

    @property
    def email(self):
        return self.user.email

    def __str__(self):
        return f"Patient: {self.name}, Problem: {self.problem}, Contact: {self.contact_number}"


from django.utils import timezone

# class Appointment(models.Model):
#     doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments_as_doctor')
#     patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments_as_patient')
#     slot = models.ForeignKey(DoctorSlot, on_delete=models.CASCADE)
#     treatment_details = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     date = models.DateField(default=timezone.now)  # Set the default to the current date
    
#     appointment_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

#     def save(self, *args, **kwargs):
#         if not self.appointment_id:
#             self.appointment_id = str(uuid.uuid4())[:8]
#         super(Appointment, self).save(*args, **kwargs)

def get_current_date():
    return timezone.now().date()

class Appointment(models.Model):
    doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments_as_doctor')
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='appointments_as_patient')
    slot = models.ForeignKey(DoctorSlot, on_delete=models.CASCADE)
    treatment_details = models.TextField()
    created_at = models.DateTimeField(default=timezone.now)
    
    # Use the function get_current_date for the default date
    date = models.DateField(default=get_current_date)  # Use the function reference
    
    appointment_id = models.CharField(max_length=50, unique=True, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.appointment_id:
            self.appointment_id = str(uuid.uuid4())[:8]
        super(Appointment, self).save(*args, **kwargs)

# models.py
class Medicine(models.Model):
    name = models.CharField(max_length=255, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)  # Allow NULL values
# class Prescription(models.Model):
#     doctor = models.ForeignKey(
#         CustomUser,
#         on_delete=models.CASCADE,
#         related_name="prescriptions_as_doctor",  # Unique reverse accessor for doctors
#     )
#     patient = models.ForeignKey(
#         CustomUser,
#         on_delete=models.CASCADE,
#         related_name="prescriptions_as_patient",  # Unique reverse accessor for patients
#     )
#     medicine = models.ManyToManyField(Medicine)
#     dosage = models.TextField()
#     instructions = models.TextField()
#     date_prescribed = models.DateField(auto_now_add=True)




class Prescription(models.Model):
    doctor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='prescriptions_as_doctor')
    patient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='prescriptions_as_patient')
    medicines = models.ManyToManyField(Medicine, related_name='prescriptions')
    dosage = models.CharField(max_length=100)
    instructions = models.TextField()
    morning = models.BooleanField(default=False)
    afternoon = models.BooleanField(default=False)
    evening = models.BooleanField(default=False)
    # date_prescribed = models.DateField( null=False,default=now)  # This will set the current timestamp for new records
    date_prescribed = models.DateField(auto_now_add=True)
    def __str__(self):
        return f"Prescription {self.id} for {self.patient.name}"

class PrescriptionMedicine(models.Model):
    prescription = models.ForeignKey(Prescription, related_name="medicine_details", on_delete=models.CASCADE)
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    morning = models.BooleanField(default=False)
    afternoon = models.BooleanField(default=False)
    evening = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.medicine.name} for {self.prescription.id}"