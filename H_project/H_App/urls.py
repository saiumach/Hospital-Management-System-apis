from django.urls import path
from .views import UserRegistrationView, UserLoginView,RoleBasedUserDetailView,ReceptionistDashboardView,AssignPatientToDoctorView,CreatePrescriptionView,PatientPrescriptionListView,generate_prescription_pdf,FilterAppointmentsView
from . import views

urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='user-register'),
    path('login/', UserLoginView.as_view(), name='user-login'),
    path('create-user-details/', RoleBasedUserDetailView.as_view(), name='create-user-details'),
    path('receptionist-dashboard/', ReceptionistDashboardView.as_view(), name='receptionist-view'),
    path('assign-patient/', AssignPatientToDoctorView.as_view(), name='assign-patient'),
    path('create-prescription/', CreatePrescriptionView.as_view(), name='create-prescription'),
    path('patient-prescriptions/<int:patient_id>/', PatientPrescriptionListView.as_view(), name='patient-prescriptions'),
    path('patient/<int:patient_id>/pdf/', generate_prescription_pdf, name='generate_prescription_pdf'),
    path('appointments/list/', FilterAppointmentsView.as_view(), name='filter-appointments'),
]
