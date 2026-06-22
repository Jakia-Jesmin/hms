from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.db.models import Q
from django.utils import timezone
from .models import (
    User, Department, Doctor, Patient, 
    Appointment, Prescription, Medicine, 
    PrescriptionMedicine, Bill
)
from .serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, ChangePasswordSerializer,
    DepartmentSerializer, DoctorSerializer, PatientSerializer,
    AppointmentSerializer, AppointmentStatusUpdateSerializer,
    PrescriptionSerializer, PrescriptionCreateSerializer,
    MedicineSerializer, PrescriptionMedicineSerializer,
    BillSerializer
)
from .permissions import (
    IsAdmin, IsDoctor, IsPatient, IsReceptionist,
    IsAdminOrDoctor, IsAdminOrReceptionist,
    IsAdminOrDoctorOrReceptionist, IsOwnerOrAdmin
)


class AuthViewSet(viewsets.GenericViewSet):
    permission_classes = [AllowAny]
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Create corresponding profile based on role
            if user.role == 'doctor':
                Doctor.objects.create(
                    user=user,
                    specialization='General',
                    phone='',
                    experience=0
                )
            elif user.role == 'patient':
                Patient.objects.create(
                    user=user,
                    age=0,
                    gender='O',
                    blood_group='O+',
                    address='',
                    phone=''
                )
            
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            refresh = RefreshToken.for_user(user)
            return Response({
                'user': UserSerializer(user).data,
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({"message": "Logged out successfully"})
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'])
    def token_refresh(self, request):
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer
        serializer = TokenRefreshSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            if not user.check_password(serializer.validated_data['old_password']):
                return Response(
                    {"old_password": "Incorrect password"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response({"message": "Password changed successfully"})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=False, methods=['get', 'put'])
    def profile(self, request):
        if request.method == 'GET':
            serializer = self.get_serializer(request.user)
            return Response(serializer.data)
        else:
            serializer = self.get_serializer(
                request.user, 
                data=request.data, 
                partial=True
            )
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Department.objects.all()
        name = self.request.query_params.get('name')
        if name:
            qs = qs.filter(name__icontains=name)
        return qs

    @action(detail=True, methods=['get'])
    def doctors(self, request, pk=None):
        department = self.get_object()
        doctors = department.doctors.all()
        is_available = request.query_params.get('is_available')
        if is_available is not None:
            doctors = doctors.filter(is_available=is_available.lower() == 'true')
        from .serializers import DoctorSerializer
        return Response(DoctorSerializer(doctors, many=True).data)


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    def get_queryset(self):
        qs = Doctor.objects.all()

        department_id = self.request.query_params.get('department_id')
        specialization = self.request.query_params.get('specialization')
        is_available = self.request.query_params.get('is_available')

        if department_id:
            qs = qs.filter(department_id=department_id)
        if specialization:
            qs = qs.filter(specialization__icontains=specialization)
        if is_available is not None:
            qs = qs.filter(is_available=is_available.lower() == 'true')

        return qs

    @action(detail=False, methods=['get'])
    def available(self, request):
        doctors = self.get_queryset().filter(is_available=True)
        return Response(self.get_serializer(doctors, many=True).data)

    @action(detail=False, methods=['get', 'patch'])
    def my_profile(self, request):
        try:
            doctor = request.user.doctor_profile
        except Doctor.DoesNotExist:
            return Response(
                {"error": "Doctor profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == 'GET':
            return Response(self.get_serializer(doctor).data)
        serializer = self.get_serializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['patch'])
    def toggle_availability(self, request, pk=None):
        doctor = self.get_object()
        user = request.user
        if user.role != 'admin' and getattr(user, 'doctor_profile', None) != doctor:
            return Response(
                {"error": "You can only toggle your own availability"},
                status=status.HTTP_403_FORBIDDEN
            )
        doctor.is_available = not doctor.is_available
        doctor.save()
        return Response(self.get_serializer(doctor).data)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReceptionist()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist', 'doctor']:
            qs = Patient.objects.all()
        elif user.role == 'patient':
            qs = Patient.objects.filter(user=user)
        else:
            return Patient.objects.none()

        gender = self.request.query_params.get('gender')
        blood_group = self.request.query_params.get('blood_group')

        if gender:
            qs = qs.filter(gender=gender)
        if blood_group:
            qs = qs.filter(blood_group=blood_group)

        return qs

    @action(detail=False, methods=['get', 'patch'])
    def my_profile(self, request):
        try:
            patient = request.user.patient_profile
        except Patient.DoesNotExist:
            return Response(
                {"error": "Patient profile not found"},
                status=status.HTTP_404_NOT_FOUND
            )
        if request.method == 'GET':
            return Response(self.get_serializer(patient).data)
        serializer = self.get_serializer(patient, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist']:
            qs = Appointment.objects.all()
        elif user.role == 'doctor':
            qs = Appointment.objects.filter(doctor__user=user)
        elif user.role == 'patient':
            qs = Appointment.objects.filter(patient__user=user)
        else:
            return Appointment.objects.none()

        # Support filtering via query params on the list endpoint
        doctor_id = self.request.query_params.get('doctor_id')
        patient_id = self.request.query_params.get('patient_id')
        date = self.request.query_params.get('date')
        status_filter = self.request.query_params.get('status')

        if doctor_id:
            qs = qs.filter(doctor_id=doctor_id)
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if date:
            qs = qs.filter(appointment_date__date=date)
        if status_filter:
            qs = qs.filter(status=status_filter)

        return qs

    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        appointment = self.get_object()
        user = request.user

        if user.role not in ['admin', 'doctor', 'receptionist']:
            return Response(
                {"error": "You don't have permission to update appointment status"},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.role == 'doctor' and appointment.doctor.user != user:
            return Response(
                {"error": "You can only update your own appointments"},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AppointmentStatusUpdateSerializer(
            data=request.data,
            context={'appointment': appointment}
        )
        if serializer.is_valid():
            appointment.status = serializer.validated_data['status']
            appointment.save()
            return Response(AppointmentSerializer(appointment).data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        appointment = self.get_object()
        user = request.user

        if user.role == 'doctor' and appointment.doctor.user != user:
            return Response(
                {"error": "You can only cancel your own appointments"},
                status=status.HTTP_403_FORBIDDEN
            )
        if user.role == 'patient' and appointment.patient.user != user:
            return Response(
                {"error": "You can only cancel your own appointments"},
                status=status.HTTP_403_FORBIDDEN
            )
        if appointment.status in ['cancelled', 'completed']:
            return Response(
                {"error": f"Cannot cancel an appointment with status '{appointment.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'cancelled'
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrDoctor()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin':
            return Prescription.objects.all()
        elif user.role == 'doctor':
            return Prescription.objects.filter(appointment__doctor__user=user)
        elif user.role == 'patient':
            return Prescription.objects.filter(appointment__patient__user=user)
        return Prescription.objects.none()


class MedicineViewSet(viewsets.ModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]

    @action(detail=False, methods=['get'])
    def search(self, request):
        query = request.query_params.get('q', '')
        if query:
            medicines = Medicine.objects.filter(
                Q(name__icontains=query) |
                Q(description__icontains=query)
            )
            serializer = self.get_serializer(medicines, many=True)
            return Response(serializer.data)
        return Response([])


class BillViewSet(viewsets.ModelViewSet):
    queryset = Bill.objects.all()
    serializer_class = BillSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdminOrReceptionist()]
        return [IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        if user.role in ['admin', 'receptionist']:
            qs = Bill.objects.all()
        elif user.role == 'patient':
            qs = Bill.objects.filter(patient__user=user)
        else:
            return Bill.objects.none()

        patient_id = self.request.query_params.get('patient_id')
        paid = self.request.query_params.get('paid')

        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        if paid is not None:
            qs = qs.filter(paid=paid.lower() == 'true')

        return qs

    @action(detail=True, methods=['post'])
    def mark_paid(self, request, pk=None):
        bill = self.get_object()
        if bill.paid:
            return Response(
                {"error": "Bill is already paid"},
                status=status.HTTP_400_BAD_REQUEST
            )
        bill.paid = True
        bill.save()
        return Response(self.get_serializer(bill).data)

    @action(detail=True, methods=['post'])
    def mark_unpaid(self, request, pk=None):
        bill = self.get_object()
        if not bill.paid:
            return Response(
                {"error": "Bill is not paid yet"},
                status=status.HTTP_400_BAD_REQUEST
            )
        bill.paid = False
        bill.save()
        return Response(self.get_serializer(bill).data)