from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import (
    User, Department, Doctor, Patient, 
    Appointment, Prescription, Medicine, 
    PrescriptionMedicine, Bill
)


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'first_name', 'last_name', 
                 'full_name', 'role', 'date_joined')
        read_only_fields = ('id', 'date_joined')
    
    def get_full_name(self, obj):
        return obj.get_full_name()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES, default='patient')
    
    class Meta:
        model = User
        fields = ('id', 'username', 'email', 'password', 'password_confirm', 
                 'first_name', 'last_name', 'role')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password": "Passwords do not match"})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Email already exists"})
        
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role=validated_data.get('role', 'patient'),
        )
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Invalid credentials")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")
        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({"new_password": "Passwords do not match"})
        return attrs


class DepartmentSerializer(serializers.ModelSerializer):
    doctor_count = serializers.IntegerField(source='doctors.count', read_only=True)

    class Meta:
        model = Department
        fields = ('id', 'name', 'description', 'doctor_count')


class DoctorSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.filter(role='doctor'),
        write_only=True
    )
    department_name = serializers.CharField(source='department.name', read_only=True)
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Doctor
        fields = ('id', 'user', 'user_id', 'user_details', 'full_name',
                  'department', 'department_name', 'specialization',
                  'phone', 'experience', 'is_available')
        read_only_fields = ('id', 'user')


class PatientSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    user_id = serializers.PrimaryKeyRelatedField(
        source='user',
        queryset=User.objects.filter(role='patient'),
        write_only=True
    )
    full_name = serializers.CharField(source='user.get_full_name', read_only=True)

    class Meta:
        model = Patient
        fields = ('id', 'user', 'user_id', 'user_details', 'full_name',
                  'age', 'gender', 'blood_group', 'address', 'phone')
        read_only_fields = ('id', 'user')


class AppointmentSerializer(serializers.ModelSerializer):
    patient_details = PatientSerializer(source='patient', read_only=True)
    doctor_details = DoctorSerializer(source='doctor', read_only=True)
    patient_id = serializers.PrimaryKeyRelatedField(
        source='patient', 
        queryset=Patient.objects.all(),
        write_only=True
    )
    doctor_id = serializers.PrimaryKeyRelatedField(
        source='doctor', 
        queryset=Doctor.objects.all(),
        write_only=True
    )
    
    class Meta:
        model = Appointment
        fields = ('id', 'patient', 'patient_id', 'patient_details', 
                 'doctor', 'doctor_id', 'doctor_details',
                 'appointment_date', 'status', 'created_at')
        read_only_fields = ('id', 'created_at', 'status')
    
    def validate(self, attrs):
        # Check if doctor is available at that time
        doctor = attrs.get('doctor')
        appointment_date = attrs.get('appointment_date')
        
        if doctor and appointment_date:
            # Check for overlapping appointments
            existing = Appointment.objects.filter(
                doctor=doctor,
                appointment_date=appointment_date,
                status__in=['pending', 'approved']
            )
            if self.instance:
                existing = existing.exclude(id=self.instance.id)
            if existing.exists():
                raise serializers.ValidationError(
                    "Doctor already has an appointment at this time"
                )
        
        return attrs


class AppointmentStatusUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Appointment.STATUS_CHOICES)
    
    def validate_status(self, value):
        if value == 'approved':
            # Check if doctor is available
            appointment = self.context.get('appointment')
            if appointment and appointment.doctor:
                if not appointment.doctor.is_available:
                    raise serializers.ValidationError("Doctor is not available")
        return value


class MedicineSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medicine
        fields = '__all__'


class PrescriptionMedicineSerializer(serializers.ModelSerializer):
    medicine_name = serializers.CharField(source='medicine.name', read_only=True)
    medicine_details = MedicineSerializer(source='medicine', read_only=True)
    
    class Meta:
        model = PrescriptionMedicine
        fields = ('id', 'prescription', 'medicine', 'medicine_name', 
                 'medicine_details', 'dosage', 'duration')


class PrescriptionSerializer(serializers.ModelSerializer):
    medicines = PrescriptionMedicineSerializer(many=True, read_only=True)
    patient_name = serializers.CharField(source='appointment.patient.user.get_full_name', read_only=True)
    doctor_name = serializers.CharField(source='appointment.doctor.user.get_full_name', read_only=True)
    
    class Meta:
        model = Prescription
        fields = ('id', 'appointment', 'patient_name', 'doctor_name',
                 'diagnosis', 'notes', 'medicines', 'created_at')
        read_only_fields = ('id', 'created_at')


class PrescriptionCreateSerializer(serializers.ModelSerializer):
    medicines = PrescriptionMedicineSerializer(many=True)
    
    class Meta:
        model = Prescription
        fields = ('id', 'appointment', 'diagnosis', 'notes', 'medicines')
    
    def create(self, validated_data):
        medicines_data = validated_data.pop('medicines')
        prescription = Prescription.objects.create(**validated_data)
        
        for medicine_data in medicines_data:
            PrescriptionMedicine.objects.create(
                prescription=prescription,
                **medicine_data
            )
        
        return prescription
    
    def validate(self, attrs):
        # Check if prescription already exists for this appointment
        appointment = attrs.get('appointment')
        if Prescription.objects.filter(appointment=appointment).exists():
            raise serializers.ValidationError(
                "Prescription already exists for this appointment"
            )
        return attrs


class BillSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source='patient.user.get_full_name', read_only=True)
    
    class Meta:
        model = Bill
        fields = ('id', 'patient', 'patient_name', 'amount', 'paid', 'created_at')
        read_only_fields = ('id', 'created_at')