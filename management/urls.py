from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AuthViewSet, UserViewSet, DepartmentViewSet, DoctorViewSet,
    PatientViewSet, AppointmentViewSet, PrescriptionViewSet,
    MedicineViewSet, BillViewSet
)

router = DefaultRouter()
router.register('auth', AuthViewSet, basename='auth')
router.register('users', UserViewSet, basename='user')
router.register('departments', DepartmentViewSet, basename='department')
router.register('doctors', DoctorViewSet, basename='doctor')
router.register('patients', PatientViewSet, basename='patient')
router.register('appointments', AppointmentViewSet, basename='appointment')
router.register('prescriptions', PrescriptionViewSet, basename='prescription')
router.register('medicines', MedicineViewSet, basename='medicine')
router.register('bills', BillViewSet, basename='bill')

urlpatterns = [
    path('', include(router.urls)),
]