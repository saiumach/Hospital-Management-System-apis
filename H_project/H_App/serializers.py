from rest_framework import serializers
from .models import CustomUser,Appointment,DoctorSlot,Patient,PrescriptionMedicine
import re
from .models import Prescription,Medicine
from django.utils import timezone

class UserRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['email', 'name', 'user_type', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):
        user = CustomUser(
            email=validated_data['email'],
            name=validated_data['name'],
            user_type=validated_data['user_type'],
        )
        user.set_password(validated_data['password'])
        user.save()
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()


class ReceptionistDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email']


class AssignPatientToDoctorSerializer(serializers.Serializer):
    patient_id = serializers.IntegerField()
    doctor_id = serializers.IntegerField()
    slot = serializers.CharField(max_length=100)



class DoctorSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = DoctorSlot
        fields = [ 'slot', 'is_available','date']


        
class CustomUserSerializer(serializers.ModelSerializer):
    assigned_doctor = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.filter(user_type='doctor'), required=False)
    assigned_slot = DoctorSlotSerializer(required=False)

    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'contact_number', 'problem', 'assigned_doctor', 'assigned_slot']


class DoctorPatientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["id", "name", "assigned_slot", "problem",]



class DoctorInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ["name", "contact_number", "specialization"]

class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = [ 'name'] 

# class PrescriptionMedicineSerializer(serializers.ModelSerializer):
#     medicine = MedicineSerializer()
#     class Meta:
#         model = PrescriptionMedicine
#         fields = ['prescription', 'medicine', 'morning', 'afternoon', 'evening']


class PrescriptionMedicineSerializer(serializers.ModelSerializer):
    # Accept medicine name instead of ID
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)

    class Meta:
        model = PrescriptionMedicine
        fields = [ 'medicine_name', 'morning', 'afternoon', 'evening']

    def create(self, validated_data):
        # Get the medicine name from validated_data
        medicine_name = validated_data.pop('medicine_name')

        # Check if the medicine already exists, if not, create it
        medicine, created = Medicine.objects.get_or_create(name=medicine_name)

        # Create the PrescriptionMedicine instance
        prescription_medicine = PrescriptionMedicine.objects.create(medicine=medicine, **validated_data)
        return prescription_medicine


class PrescriptionSerializer(serializers.ModelSerializer):
    medicine_details = PrescriptionMedicineSerializer(many=True)
    doctor = serializers.StringRelatedField()
    patient = serializers.StringRelatedField()
    appointment_id = serializers.CharField(source='appointment.appointment_id', read_only=True)
    
    # Ensure default value for `date_prescribed`
    date_prescribed = serializers.DateTimeField(default=timezone.now)  # Auto-sets current time if not provided

    class Meta:
        model = Prescription
        fields = ['id', 'doctor', 'patient', 'medicine_details', 'dosage', 'instructions', 'date_prescribed', 'appointment_id']
        read_only_fields = ['doctor', 'date_prescribed']

    # def to_representation(self, instance):
    #     print(instance.medicine_details.all())  # Debugging medicine details
    #     return super().to_representation(instance)

class AppointmentSerializer(serializers.ModelSerializer):
    patient = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.filter(user_type='patient'))
    doctor = serializers.PrimaryKeyRelatedField(queryset=CustomUser.objects.filter(user_type='doctor'))
    slot = DoctorSlotSerializer(read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True, source='prescriptions_as_appointment')  
    date = serializers.DateField()  # Use DateField if it's just a date

    class Meta:
        model = Appointment
        fields = ['appointment_id', 'doctor', 'patient', 'slot', 'treatment_details', 'created_at', 'date', 'prescriptions']

        def get_medicine_names(self, obj):
        # Retrieve and return the names of the medicines
            return [medicine.name for medicine in obj.medicine.all()]
        
        def get_slot(self, obj):
        # Include slot details with the slot date
            return {
                "slot": obj.slot.slot,
                "is_available": obj.slot.is_available,
                "date": obj.slot.date  # Add the date here
        }


class PatientDetailSerializer(serializers.ModelSerializer):
    appointment_details = AppointmentSerializer(source='appointments_as_patient', many=True, read_only=True)
    prescriptions = PrescriptionSerializer(many=True, read_only=True)

    class Meta:
        model = Patient
        fields = ["id", "name", "email", "contact_number", "problem",  "appointment_details","prescriptions"]

class AssignedPatientSerializer(serializers.ModelSerializer):
    assigned_slot = DoctorSlotSerializer()  # Use the updated slot serializer

    class Meta:
        model = CustomUser
        fields = [
            'id', 'name', 'email', 'contact_number', 'problem',
            'assigned_doctor', 'assigned_slot', 'prescriptions', 'appointment_id'
        ]


    def get_appointment_id(self, obj):
        # Fetch the latest appointment for the patient with the assigned doctor
        appointment = Appointment.objects.filter(patient=obj, doctor=obj.assigned_doctor).last()
        return appointment.appointment_id if appointment else None

class DoctorDetailSerializer(serializers.ModelSerializer):
    free_slots = DoctorSlotSerializer(source='doctor_slots', many=True, read_only=True)
    assigned_patients = serializers.PrimaryKeyRelatedField(source='patients_as_doctor', many=True, read_only=True)
    appointment_details = AppointmentSerializer(source='appointments_as_doctor', many=True, read_only=True)


    class Meta:
        model = CustomUser
        fields = ['id', 'name', 'email', 'specialization', 'contact_number', 'free_slots', 'assigned_patients','appointment_details']

    def update(self, instance, validated_data):
        free_slots_data = self.initial_data.get('free_slots')
        assigned_patients_data = validated_data.pop('assigned_patients', None)
        
        # Update the CustomUser fields
        instance = super().update(instance, validated_data)

        # Handle the free_slots update if provided
        if free_slots_data is not None:
            # Clear existing slots and recreate them
            DoctorSlot.objects.filter(doctor=instance).delete()
            for slot_data in free_slots_data:
                DoctorSlot.objects.create(doctor=instance, **slot_data)

        # Handle the assigned_patients update
        if assigned_patients_data is not None:
            instance.assigned_patients.set(assigned_patients_data)

        return instance

