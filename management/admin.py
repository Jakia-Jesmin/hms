from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Department, Doctor, Patient, 
    Appointment, Prescription, Medicine, 
    PrescriptionMedicine, Bill
)

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role',)}),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')

admin.site.register(User, CustomUserAdmin)

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'department', 'specialization', 'is_available')
    list_filter = ('department', 'is_available')
    search_fields = ('user__username', 'user__first_name', 'user__last_name')

@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'age', 'gender', 'blood_group', 'phone')
    list_filter = ('gender', 'blood_group')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'phone')

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'status')
    list_filter = ('status', 'appointment_date')
    search_fields = ('patient__user__username', 'doctor__user__username')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'created_at')
    search_fields = ('appointment__patient__user__username',)

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'unit')
    search_fields = ('name',)

@admin.register(PrescriptionMedicine)
class PrescriptionMedicineAdmin(admin.ModelAdmin):
    list_display = ('id', 'prescription', 'medicine', 'dosage', 'duration')

@admin.register(Bill)
class BillAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'amount', 'paid', 'created_at')
    list_filter = ('paid', 'created_at')
    search_fields = ('patient__user__username',)