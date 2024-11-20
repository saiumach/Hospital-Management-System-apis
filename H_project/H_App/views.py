from rest_framework import generics, permissions,status,views
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .models import CustomUser,Appointment,Patient,DoctorSlot,Prescription,Appointment,Medicine,PrescriptionMedicine
from .serializers import UserRegistrationSerializer, UserLoginSerializer, DoctorDetailSerializer, PatientDetailSerializer, ReceptionistDetailSerializer, AssignPatientToDoctorSerializer,AppointmentSerializer,DoctorSlotSerializer
from django.core.exceptions import PermissionDenied
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404,render
from rest_framework.permissions import BasePermission
from .serializers import PrescriptionSerializer
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404
import uuid
from datetime import datetime, time
from datetime import datetime, date, time 
from django.utils.timezone import make_aware,get_current_timezone
from django.core.exceptions import PermissionDenied
from datetime import datetime
from django.template.loader import render_to_string
from weasyprint import HTML
from django.http import HttpResponse
from .permissions import IsReceptionist 
from django.db import transaction
from django.http import HttpResponseNotFound
from datetime import datetime
import datetime
from datetime import date
from datetime import datetime, date, time
from django.utils import timezone
from rest_framework.pagination import PageNumberPagination
from rest_framework.exceptions import ValidationError
from datetime import datetime  # Correct import
from django.utils.timezone import make_aware, get_current_timezone
from rest_framework_simplejwt.authentication import JWTAuthentication




class UserRegistrationView(generics.ListCreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [permissions.AllowAny]

class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = CustomUser.objects.filter(email=email).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'name': user.name,
                    'user_type': user.user_type
                }
            }, status=status.HTTP_200_OK)
        else:
            raise AuthenticationFailed("Invalid email or password.")
        # return Response({'error': 'Invalid email or password'}, status=400)

# class RoleBasedUserDetailView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     def get_serializer_class(self):
#         user = self.request.user
#         if user.user_type == 'doctor':
#             return DoctorDetailSerializer
#         elif user.user_type == 'patient':
#             return PatientDetailSerializer
#         elif user.user_type == 'receptionist':
#             return ReceptionistDetailSerializer
#         else:
#             raise PermissionDenied("You do not have permission to view or create this resource.")

#     def get_object(self):
#         return self.request.user

#     def get(self, request):
#         serializer = self.get_serializer(self.get_object())
#         return Response(serializer.data, status=status.HTTP_200_OK)

    
#     def patch(self, request):
#         user = self.request.user
#         serializer = self.get_serializer(user, data=request.data, partial=True)
#         serializer.is_valid(raise_exception=True)
#         serializer.save()
#         return Response(serializer.data)
    

class RoleBasedUserDetailView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        user = self.request.user
        if user.user_type == 'doctor':
            return DoctorDetailSerializer
        elif user.user_type == 'patient':
            return PatientDetailSerializer
        elif user.user_type == 'receptionist':
            return ReceptionistDetailSerializer
        else:
            raise PermissionDenied("You do not have permission to view or create this resource.")

    def get_object(self):
        return self.request.user

    def get(self, request):
        serializer = self.get_serializer(self.get_object())
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        user = self.request.user

        # Handle doctor-specific logic for updating free_slots by date
        if user.user_type == 'doctor':
            free_slots_data = request.data.get('free_slots')
            date = request.data.get('date')

            if free_slots_data is not None and date is not None:
                try:
                    # Parse and validate the date
                    parsed_date = datetime.datetime.strptime(date, '%Y-%m-%d').date()
                except ValueError:
                    raise ValidationError({"date": "Invalid date format. Use YYYY-MM-DD."})

                # Ensure free_slots_data is a list
                if not isinstance(free_slots_data, list):
                    raise ValidationError({"free_slots": "Expected a list of slot data."})

                # Create or update the slots for the given date
                updated_slots = []
                for slot_data in free_slots_data:
                    slot_time = slot_data.get('slot')
                    is_available = slot_data.get('is_available')

                    if not slot_time or not isinstance(is_available, bool):
                        raise ValidationError({"free_slots": "Each slot must include a 'slot' and 'is_available' field."})

                    # Create or update the slot for this date
                    doctor_slot, created = DoctorSlot.objects.update_or_create(
                        doctor=user,
                        date=parsed_date,
                        slot=slot_time,
                        defaults={"is_available": is_available}
                    )

                    updated_slots.append({
                        "slot": slot_time,
                        "is_available": is_available,
                        "created": created
                    })

                return Response(
                    {"message": f"Free slots for {date} updated successfully.", "updated_slots": updated_slots},
                    status=status.HTTP_200_OK
                )

        # Default behavior for other fields (non-doctor user updates)
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

# class ReceptionistDashboardView(generics.GenericAPIView):
#     permission_classes = [permissions.IsAuthenticated]

#     @staticmethod
#     def ensure_datetime(value):
#         """
#         Ensure the input value is a timezone-aware datetime object.
#         If it's a datetime.date object, convert it to a datetime object.
#         """
#         if isinstance(value, datetime):
#             # If it's already a datetime object, ensure it's timezone-aware
#             return make_aware(value) if value.tzinfo is None else value
#         elif isinstance(value, date):
#             # If it's a date object, convert it to datetime
#             tz = get_current_timezone()
#             # Combine the date with the time 00:00:00 and make it timezone-aware
#             value_as_datetime = datetime.combine(value, datetime.min.time())
#             return make_aware(value_as_datetime, timezone=tz)
#         raise TypeError(f"Unsupported type: {type(value)}. Expected datetime.date or datetime.datetime.")

#     def get(self, request, *args, **kwargs):
#         user = request.user
#         if user.user_type != 'receptionist':
#             raise PermissionDenied("Only receptionists have access to this resource.")

#         # Fetch doctors and patients data
#         doctors = CustomUser.objects.filter(user_type='doctor')
#         patients = CustomUser.objects.filter(user_type='patient')

#         # Serialize doctor and patient data
#         doctor_data = []
#         for doctor in doctors:
#             assigned_patients = Appointment.objects.filter(doctor=doctor)
#             assigned_patient_data = []

#             for appointment in assigned_patients:
#                 # Ensure datetime fields are timezone-aware
#                 appointment_date = self.ensure_datetime(appointment.date)
#                 created_at = self.ensure_datetime(appointment.created_at)

#                 patient = appointment.patient
#                 appointment_id = appointment.appointment_id

#                 # Assigned slot data
#                 assigned_slot_data = {
#                     "slot": appointment.slot.slot,
#                     "is_available": appointment.slot.is_available,
#                 }

#                 doctor_data_for_appointment = {
#                     "id": doctor.id,
#                     "name": doctor.name,
#                     "email": doctor.email,
#                     "specialization": doctor.specialization,
#                 }

#                 patient_data = PatientDetailSerializer(patient).data
#                 patient_data['appointment_details'] = [
#                     {
#                         "appointment_id": appointment_id,
#                         "doctor": doctor_data_for_appointment,
#                         "slot": assigned_slot_data,
#                         "treatment_details": appointment.treatment_details,
#                         "created_at": created_at.isoformat(),
#                         "date": appointment_date.isoformat(),
#                     }
#                 ]
#                 assigned_patient_data.append(patient_data)

#             doctor_info = DoctorDetailSerializer(doctor).data
#             doctor_info['assigned_patients'] = assigned_patient_data
#             doctor_data.append(doctor_info)

#         # Serialize receptionist data
#         receptionist_data = ReceptionistDetailSerializer(user).data

#         return Response({
#             'receptionist': receptionist_data,
#             'doctors': doctor_data,
#             'patients': PatientDetailSerializer(patients, many=True).data,
#         })



class DoctorPagination(PageNumberPagination):
    page_size = 1  # Number of doctors per page
    page_size_query_param = 'page_size'
    max_page_size = 100

class PatientPagination(PageNumberPagination):
    page_size = 1  # Number of patients per page
    page_size_query_param = 'page_size'
    max_page_size = 100



class ReceptionistDashboardView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @staticmethod
    def ensure_datetime(value):
        """
        Ensure the input value is a timezone-aware datetime object.
        If it's a datetime.date object, convert it to a datetime object.
        """
        if isinstance(value, datetime):
            # If it's already a datetime object, ensure it's timezone-aware
            return make_aware(value) if value.tzinfo is None else value
        elif isinstance(value, date):
            # If it's a date object, convert it to datetime
            tz = get_current_timezone()
            # Combine the date with the time 00:00:00 and make it timezone-aware
            value_as_datetime = datetime.combine(value, datetime.min.time())
            return make_aware(value_as_datetime, timezone=tz)
        raise TypeError(f"Unsupported type: {type(value)}. Expected datetime.date or datetime.datetime.")

    def get(self, request, *args, **kwargs):
        user = request.user
        if user.user_type != 'receptionist':
            raise PermissionDenied("Only receptionists have access to this resource.")

        # Fetch doctors and patients data
        doctors = CustomUser.objects.filter(user_type='doctor')
        patients = CustomUser.objects.filter(user_type='patient')

        # Apply pagination to the doctor and patient data
        doctor_paginator = DoctorPagination()
        paginated_doctors = doctor_paginator.paginate_queryset(doctors, request)

        patient_paginator = PatientPagination()
        paginated_patients = patient_paginator.paginate_queryset(patients, request)

        # Prepare the doctor data with assigned patients
        doctor_data = []
        for doctor in paginated_doctors:
            assigned_patients = Appointment.objects.filter(doctor=doctor)
            assigned_patient_data = []

            for appointment in assigned_patients:
                # Ensure datetime fields are timezone-aware
                appointment_date = self.ensure_datetime(appointment.date)
                created_at = self.ensure_datetime(appointment.created_at)

                patient = appointment.patient
                appointment_id = appointment.appointment_id

                # Assigned slot data
                assigned_slot_data = {
                    "slot": appointment.slot.slot,
                    "is_available": appointment.slot.is_available,
                }

                doctor_data_for_appointment = {
                    "id": doctor.id,
                    "name": doctor.name,
                    "email": doctor.email,
                    "specialization": doctor.specialization,
                }

                patient_data = PatientDetailSerializer(patient).data
                patient_data['appointment_details'] = [
                    {
                        "appointment_id": appointment_id,
                        "doctor": doctor_data_for_appointment,
                        "slot": assigned_slot_data,
                        "treatment_details": appointment.treatment_details,
                        "created_at": created_at.isoformat(),
                        "date": appointment_date.isoformat(),
                    }
                ]
                assigned_patient_data.append(patient_data)

            doctor_info = DoctorDetailSerializer(doctor).data
            doctor_info['assigned_patients'] = assigned_patient_data
            doctor_data.append(doctor_info)

        # Serialize receptionist data
        receptionist_data = ReceptionistDetailSerializer(user).data

        # Return paginated data with doctor and patient details
        response_data = {
            'receptionist': receptionist_data,
            'doctors': doctor_paginator.get_paginated_response(doctor_data).data,
            'patients': patient_paginator.get_paginated_response(
                PatientDetailSerializer(paginated_patients, many=True).data
            ).data,
        }

        return Response(response_data)





    
class AssignPatientToDoctorView(APIView):
    def post(self, request):
        patient_id = request.data.get('patient_id')
        doctor_id = request.data.get('doctor_id')
        slot = request.data.get('slot')

        # Retrieve the patient and doctor
        try:
            patient = CustomUser.objects.get(id=patient_id, user_type='patient')
        except CustomUser.DoesNotExist:
            return Response({"detail": "Patient not found"}, status=status.HTTP_404_NOT_FOUND)

        try:
            doctor = CustomUser.objects.get(id=doctor_id, user_type='doctor')
        except CustomUser.DoesNotExist:
            return Response({"detail": "Doctor not found"}, status=status.HTTP_404_NOT_FOUND)

        # Check specialization match
        if doctor.specialization.lower() != patient.problem.lower():
            return Response({"detail": "Doctor's specialization does not match patient's problem."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Check if the slot is available
        available_slot = DoctorSlot.objects.filter(doctor=doctor, slot=slot, is_available=True).first()
        if not available_slot:
            return Response({"detail": "No available doctor with matching specialization and slot."},
                            status=status.HTTP_400_BAD_REQUEST)

        # Create the appointment
        appointment = Appointment.objects.create(
            doctor=doctor,
            patient=patient,
            slot=available_slot,  # Assign the DoctorSlot instance
            treatment_details="Pending",  # or other initial value as appropriate
            # created_at=datetime.now()
        )

        # Mark the slot as unavailable
        available_slot.is_available = False
        available_slot.save()

        # Prepare the response
        response_data = {
            "id": patient.id,
            "name": patient.name,
            "email": patient.email,
            "contact_number": patient.contact_number,
            "problem": patient.problem,
            "assigned_doctor": doctor.email,
            "assigned_slot": {
                "slot": available_slot.slot,
                "is_available": available_slot.is_available
            },
            "prescriptions": [],
            "appointment_id": appointment.id  # Include the generated appointment ID
        }

        return Response(response_data, status=status.HTTP_200_OK)


# -------------------------------------------------------------------------------






class CreatePrescriptionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Ensure the logged-in user is a doctor
        if request.user.user_type != 'doctor':
            return Response({"detail": "Only doctors can create prescriptions."}, status=status.HTTP_403_FORBIDDEN)

        # Get the required fields from the request
        patient_id = request.data.get('patient_id')
        medicines = request.data.get('medicines', [])  # List of medicine details
        dosage = request.data.get('dosage')
        instructions = request.data.get('instructions')
        appointment_id = request.data.get('appointment_id')
        date = request.data.get('date')  # Expecting a date string
        treatment_details = request.data.get('treatment_details', '')

        # Validate required fields
        if not patient_id or not medicines or not dosage or not instructions or not appointment_id:
            return Response({"detail": "Patient ID, medicines, dosage, instructions, and appointment ID are required."}, 
                             status=status.HTTP_400_BAD_REQUEST)

        # Validate if the patient exists and is of type 'patient'
        try:
            patient = CustomUser.objects.get(id=patient_id, user_type='patient')
        except CustomUser.DoesNotExist:
            return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        # Validate if the appointment exists
        try:
            appointment = Appointment.objects.get(appointment_id=appointment_id)
        except Appointment.DoesNotExist:
            return Response({"detail": "Invalid appointment ID."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if the doctor is assigned to the patient
        if appointment.doctor != request.user:
            return Response({"detail": "You are not assigned to this patient."}, status=status.HTTP_403_FORBIDDEN)

        # Convert the `date` to a timezone-aware datetime object
        if date:
            try:
        # Parse the date string into a date object
                date_obj = datetime.strptime(date, "%Y-%m-%d")  # Assuming the format is 'YYYY-MM-DD'
        # Combine the date with the time (set to midnight, for example)
                date_obj = datetime.combine(date_obj, datetime.min.time())
        # Make the datetime object timezone-aware
                date_obj = timezone.make_aware(date_obj)
            except ValueError:
                return Response({"detail": "Invalid date format. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)
        else:
            date_obj = None  # If no date is provided

        # Create the prescription within a transaction
        try:
            with transaction.atomic():
                # Create the Prescription instance
                prescription = Prescription.objects.create(
                    doctor=request.user,
                    patient=patient,
                    dosage=dosage,
                    instructions=instructions,
                    date_prescribed=date_obj  # Use the timezone-aware datetime object
                )

                # Resolve or create Medicine instances and add them to PrescriptionMedicine
                for medicine_data in medicines:
                    medicine_name = medicine_data.get('medicine_name')
                    morning = medicine_data.get('morning', False)
                    afternoon = medicine_data.get('afternoon', False)
                    evening = medicine_data.get('evening', False)

                    # Ensure medicine_name is provided
                    if not medicine_name:
                        return Response({"detail": "Medicine name is required for each medicine."}, status=status.HTTP_400_BAD_REQUEST)

                    # Get or create the Medicine instance
                    medicine, created = Medicine.objects.get_or_create(name=medicine_name)

                    # Create the PrescriptionMedicine instance
                    PrescriptionMedicine.objects.create(
                        prescription=prescription,
                        medicine=medicine,
                        morning=morning,
                        afternoon=afternoon,
                        evening=evening
                    )

                # Optionally update the appointment details
                if date:
                    appointment.date = date_obj
                if treatment_details:
                    appointment.treatment_details = treatment_details
                appointment.save()

            # Serialize and return the prescription data
            serializer = PrescriptionSerializer(prescription)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"detail": f"An error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# correct code

# class PatientPrescriptionListView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, patient_id):
#         # Ensure the logged-in user is a doctor
#         if request.user.user_type != 'doctor':
#             return Response({"detail": "Only doctors can view prescriptions."}, status=status.HTTP_403_FORBIDDEN)

#         # Ensure the patient exists
#         try:
#             patient = CustomUser.objects.get(id=patient_id, user_type='patient')
#         except CustomUser.DoesNotExist:
#             return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

#         # Filter prescriptions based on doctor and patient
#         prescriptions = Prescription.objects.filter(doctor=request.user, patient=patient)
#         serializer = PrescriptionSerializer(prescriptions, many=True)
#         return Response(serializer.data)


# class PatientPrescriptionListView(APIView):
#     permission_classes = [IsAuthenticated]

#     def get(self, request, patient_id):
#         # Ensure the logged-in user is a doctor
#         if request.user.user_type != 'doctor':
#             return Response({"detail": "Only doctors can view prescriptions."}, status=status.HTTP_403_FORBIDDEN)

#         # Ensure the patient exists
#         try:
#             patient = CustomUser.objects.get(id=patient_id, user_type='patient')
#         except CustomUser.DoesNotExist:
#             return Response({"detail": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

#         # Filter prescriptions based on doctor and patient
#         prescriptions = Prescription.objects.filter(doctor=request.user, patient=patient)

#         # Serialize the patient's details
#         patient_data = PatientDetailSerializer(patient).data

#         # Serialize the prescriptions and include them in the patient data
#         patient_data['prescriptions'] = PrescriptionSerializer(prescriptions, many=True).data

#         # Return the response with the patient details and prescriptions
#         return Response(patient_data)


from rest_framework.permissions import AllowAny


class PatientPrescriptionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, patient_id):
        # Get prescriptions for the patient
        prescriptions = Prescription.objects.filter(patient_id=patient_id)

        # Convert date_prescribed to timezone-aware datetime if it's a date object
        for prescription in prescriptions:
            if isinstance(prescription.date_prescribed, date):  # check for datetime.date type
                # Convert to a timezone-aware datetime object
                prescription.date_prescribed = timezone.make_aware(
                    datetime.combine(prescription.date_prescribed, datetime.min.time())
                )

        # Serialize and return response
        serializer = PrescriptionSerializer(prescriptions, many=True)
        return Response(serializer.data)
# def generate_prescription_pdf(request, patient_id):
#     try:
#         patient = CustomUser.objects.get(id=patient_id)
#     except CustomUser.DoesNotExist:
#         return HttpResponse("Patient not found. Please check the patient ID.", status=404)

#     # Fetch prescriptions related to the patient
#     prescriptions = patient.prescriptions_as_patient.all()

#     # Fetch the latest appointment (if needed)
#     appointment = Appointment.objects.filter(patient=patient).last()

#     # Generate the HTML content using the template
#     html_content = render_to_string('prescription_pdf.html', {
#         'patient': patient,
#         'prescriptions': prescriptions,  # Include prescriptions data
#         'appointment': appointment,
#         'generated_at': datetime.datetime.now(),
#     })

#     # Create the PDF using WeasyPrint
#     html = HTML(string=html_content)
#     pdf = html.write_pdf()

#     # Return the PDF as a downloadable file
#     response = HttpResponse(pdf, content_type='application/pdf')
#     response['Content-Disposition'] = 'attachment; filename="prescription.pdf"'
#     return response




def generate_prescription_pdf(request, patient_id):
    try:
        patient = CustomUser.objects.get(id=patient_id)
    except CustomUser.DoesNotExist:
        return HttpResponse("Patient not found. Please check the patient ID.", status=404)

    # Fetch prescriptions related to the patient
    prescriptions = patient.prescriptions_as_patient.all()

    # Fetch the latest appointment (if needed)
    appointment = Appointment.objects.filter(patient=patient).last()

    # Generate the HTML content using the template
    html_content = render_to_string('prescription_pdf.html', {
        'patient': patient,
        'prescriptions': prescriptions,  # Include prescriptions data
        'appointment': appointment,
        'generated_at': datetime.now(),  # Correct usage
    })

    # Create the PDF using WeasyPrint
    html = HTML(string=html_content)
    pdf = html.write_pdf()

    # Return the PDF as a downloadable file
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="prescription.pdf"'
    return response


class AppointmentPagination(PageNumberPagination):
    page_size = 1  # Define the number of items per page
    page_size_query_param = 'page_size'  # Allow clients to set the page size
    max_page_size = 100  # Optionally, set a maximum page size

class FilterAppointmentsView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # Check if the user is authorized to access this API
        if user.user_type not in ["receptionist", "doctor"]:
            return Response(
                {"error": "You are not authorized to access this endpoint."},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Receptionist can view all appointments; doctors can view only their appointments
        if user.user_type == "receptionist":
            appointments = Appointment.objects.all()
        elif user.user_type == "doctor":
            appointments = Appointment.objects.filter(doctor=user)

        # Validate the date format
        try:
            # Parse the start_date and end_date from the URL path
            start_date = datetime.strptime(self.request.query_params.get('from_date'), "%Y-%m-%d")
            end_date = datetime.strptime(self.request.query_params.get('to_date'), "%Y-%m-%d")
            
            # Filter appointments based on the date range
            appointments = appointments.filter(date__gte=start_date, date__lte=end_date)

        except ValueError:
            return Response(
                {"error": "Invalid date format. Use 'YYYY-MM-DD'."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Apply pagination
        paginator = AppointmentPagination()
        paginated_appointments = paginator.paginate_queryset(appointments, request)
        
        # Serialize and return the paginated results
        serializer = AppointmentSerializer(paginated_appointments, many=True)
        return paginator.get_paginated_response(serializer.data)