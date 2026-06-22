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


class DoctorViewSet(viewsets.ModelViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin()]
        return [IsAuthenticated()]
    
    @action(detail=True, methods=['patch'])
    def toggle_availability(self, request, pk=None):
        doctor = self.get_object()
        doctor.is_available = not doctor.is_available
        doctor.save()
        serializer = self.get_serializer(doctor)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available(self, request):
        doctors = Doctor.objects.filter(is_available=True)
        serializer = self.get_serializer(doctors, many=True)
        return Response(serializer.data)


class PatientViewSet(viewsets.ModelViewSet):
    queryset = Patient.objects.all()
    serializer_class = PatientSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin() or IsReceptionist()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.role == 'receptionist':
            return Patient.objects.all()
        elif user.role == 'doctor':
            return Patient.objects.all()
        elif user.role == 'patient':
            return Patient.objects.filter(user=user)
        return Patient.objects.none()


class AppointmentViewSet(viewsets.ModelViewSet):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.role == 'receptionist':
            return Appointment.objects.all()
        elif user.role == 'doctor':
            return Appointment.objects.filter(doctor__user=user)
        elif user.role == 'patient':
            return Appointment.objects.filter(patient__user=user)
        return Appointment.objects.none()
    
    def perform_create(self, serializer):
        serializer.save()
    
    @action(detail=True, methods=['post'])
    def update_status(self, request, pk=None):
        appointment = self.get_object()
        
        # Check permissions
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
        
        # Check permissions
        user = request.user
        if user.role not in ['admin', 'doctor', 'patient', 'receptionist']:
            return Response(
                {"error": "You don't have permission to cancel appointments"},
                status=status.HTTP_403_FORBIDDEN
            )
        
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
                {"error": f"Cannot cancel appointment with status '{appointment.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        appointment.status = 'cancelled'
        appointment.save()
        return Response(AppointmentSerializer(appointment).data)
    
    @action(detail=False, methods=['get'])
    def filter(self, request):
        queryset = self.get_queryset()
        
        doctor_id = request.query_params.get('doctor_id')
        patient_id = request.query_params.get('patient_id')
        appointment_date = request.query_params.get('appointment_date')
        status_filter = request.query_params.get('status')
        
        if doctor_id:
            queryset = queryset.filter(doctor_id=doctor_id)
        if patient_id:
            queryset = queryset.filter(patient_id=patient_id)
        if appointment_date:
            queryset = queryset.filter(appointment_date__date=appointment_date)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class PrescriptionViewSet(viewsets.ModelViewSet):
    queryset = Prescription.objects.all()
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return PrescriptionCreateSerializer
        return PrescriptionSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAdmin() or IsDoctor()]
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
    
    def perform_create(self, serializer):
        serializer.save()


class MedicineViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Medicine.objects.all()
    serializer_class = MedicineSerializer
    permission_classes = [IsAuthenticated]
    
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
            return [IsAdmin() or IsReceptionist()]
        return [IsAuthenticated()]
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'admin' or user.role == 'receptionist':
            return Bill.objects.all()
        elif user.role == 'patient':
            return Bill.objects.filter(patient__user=user)
        return Bill.objects.none()
    
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
        serializer = self.get_serializer(bill)
        return Response(serializer.data)