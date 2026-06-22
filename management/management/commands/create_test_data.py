from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
import random

User = get_user_model()

from management.models import (
    Department, Doctor, Patient, Appointment, 
    Medicine, Prescription, PrescriptionMedicine, Bill
)


class Command(BaseCommand):
    help = 'Create test data for Hospital Management System'

    def handle(self, *args, **kwargs):
        self.stdout.write('Creating test data...')
        
        # Create departments
        departments = [
            'Cardiology', 'Neurology', 'Orthopedics', 'Pediatrics', 
            'Dermatology', 'Ophthalmology', 'ENT', 'Gynecology',
            'Psychiatry', 'Radiology'
        ]
        dept_objs = []
        for dept in departments:
            d, created = Department.objects.get_or_create(
                name=dept,
                defaults={'description': f'{dept} department'}
            )
            dept_objs.append(d)
            self.stdout.write(f'Created department: {dept}')

        # Create admin user
        admin, created = User.objects.get_or_create(
            username='admin',
            defaults={
                'email': 'admin@hospital.com',
                'first_name': 'Admin',
                'last_name': 'User',
                'role': 'admin',
                'is_staff': True,
                'is_superuser': True
            }
        )
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write('Created admin user')

        # Create receptionist
        receptionist, created = User.objects.get_or_create(
            username='receptionist',
            defaults={
                'email': 'receptionist@hospital.com',
                'first_name': 'Reception',
                'last_name': 'Staff',
                'role': 'receptionist',
            }
        )
        if created:
            receptionist.set_password('receptionist123')
            receptionist.save()
            self.stdout.write('Created receptionist')

        # Create doctors
        doctor_data = [
            ('dr_john', 'John', 'Smith', 'Cardiology', 'Cardiologist', 15, True),
            ('dr_sarah', 'Sarah', 'Johnson', 'Neurology', 'Neurologist', 12, True),
            ('dr_michael', 'Michael', 'Brown', 'Orthopedics', 'Orthopedic Surgeon', 10, True),
            ('dr_emily', 'Emily', 'Davis', 'Pediatrics', 'Pediatrician', 8, True),
            ('dr_david', 'David', 'Wilson', 'Dermatology', 'Dermatologist', 7, True),
            ('dr_lisa', 'Lisa', 'Anderson', 'Ophthalmology', 'Ophthalmologist', 9, True),
            ('dr_robert', 'Robert', 'Taylor', 'ENT', 'ENT Specialist', 11, True),
            ('dr_maria', 'Maria', 'Martinez', 'Gynecology', 'Gynecologist', 6, True),
        ]

        doctors = []
        for username, first, last, dept_name, spec, exp, available in doctor_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@hospital.com',
                    'first_name': first,
                    'last_name': last,
                    'role': 'doctor',
                }
            )
            if created:
                user.set_password('doctor123')
                user.save()
            
            dept = Department.objects.get(name=dept_name)
            doctor, created = Doctor.objects.get_or_create(
                user=user,
                defaults={
                    'department': dept,
                    'specialization': spec,
                    'phone': f'+123456789{random.randint(10, 99)}',
                    'experience': exp,
                    'is_available': available
                }
            )
            doctors.append(doctor)
            self.stdout.write(f'Created doctor: Dr. {first} {last}')

        # Create patients
        patient_data = [
            ('alicew', 'Alice', 'Williams', 25, 'F', 'O+', '123 Main St', '+9876543210'),
            ('bobj', 'Bob', 'Jones', 45, 'M', 'A+', '456 Oak Ave', '+9876543211'),
            ('charlie_m', 'Charlie', 'Miller', 35, 'M', 'B+', '789 Pine St', '+9876543212'),
            ('diana_w', 'Diana', 'Wilson', 28, 'F', 'AB+', '321 Elm St', '+9876543213'),
            ('eve_b', 'Eve', 'Brown', 32, 'F', 'O-', '654 Maple Ave', '+9876543214'),
            ('frank_t', 'Frank', 'Taylor', 50, 'M', 'A-', '987 Cedar St', '+9876543215'),
            ('grace_l', 'Grace', 'Lee', 22, 'F', 'B-', '147 Birch St', '+9876543216'),
            ('henry_k', 'Henry', 'Kim', 40, 'M', 'AB-', '258 Oak St', '+9876543217'),
        ]

        patients = []
        for username, first, last, age, gender, blood, address, phone in patient_data:
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@email.com',
                    'first_name': first,
                    'last_name': last,
                    'role': 'patient',
                }
            )
            if created:
                user.set_password('patient123')
                user.save()
            
            patient, created = Patient.objects.get_or_create(
                user=user,
                defaults={
                    'age': age,
                    'gender': gender,
                    'blood_group': blood,
                    'address': address,
                    'phone': phone
                }
            )
            patients.append(patient)
            self.stdout.write(f'Created patient: {first} {last}')

        # Create medicines
        medicine_data = [
            ('Paracetamol', 'Pain reliever and fever reducer', '500mg tablet'),
            ('Ibuprofen', 'Anti-inflammatory pain reliever', '400mg tablet'),
            ('Amoxicillin', 'Antibiotic for bacterial infections', '500mg capsule'),
            ('Ciprofloxacin', 'Antibiotic for various infections', '500mg tablet'),
            ('Aspirin', 'Blood thinner and pain reliever', '81mg tablet'),
            ('Metformin', 'Antidiabetic medication', '850mg tablet'),
            ('Losartan', 'Blood pressure medication', '50mg tablet'),
            ('Omeprazole', 'Proton pump inhibitor', '20mg capsule'),
            ('Atorvastatin', 'Cholesterol-lowering medication', '20mg tablet'),
            ('Levothyroxine', 'Thyroid hormone replacement', '100mcg tablet'),
            ('Amlodipine', 'Blood pressure medication', '10mg tablet'),
            ('Metoprolol', 'Beta blocker for heart conditions', '50mg tablet'),
        ]

        medicines = []
        for name, desc, unit in medicine_data:
            medicine, created = Medicine.objects.get_or_create(
                name=name,
                defaults={
                    'description': desc,
                    'unit': unit
                }
            )
            medicines.append(medicine)
            self.stdout.write(f'Created medicine: {name}')

        # Create appointments
        for i in range(20):
            patient = random.choice(patients)
            doctor = random.choice(doctors)
            date = timezone.now() + timedelta(days=random.randint(1, 30))
            status = random.choice(['pending', 'approved', 'completed', 'cancelled'])
            
            appointment = Appointment.objects.create(
                patient=patient,
                doctor=doctor,
                appointment_date=date,
                status=status
            )
            self.stdout.write(f'Created appointment {i+1}')

            # Create prescription for approved or completed appointments
            if status in ['approved', 'completed'] and random.choice([True, False]):
                prescription = Prescription.objects.create(
                    appointment=appointment,
                    diagnosis=f'Diagnosis for patient {patient.user.username}',
                    notes=f'Treatment notes for appointment {appointment.id}'
                )
                
                # Add medicines to prescription
                for j in range(random.randint(1, 4)):
                    medicine = random.choice(medicines)
                    PrescriptionMedicine.objects.create(
                        prescription=prescription,
                        medicine=medicine,
                        dosage=f"{random.randint(1, 3)} {medicine.unit}",
                        duration=f"{random.randint(3, 14)} days"
                    )
                self.stdout.write(f'Created prescription for appointment {appointment.id}')

            # Create bill for some appointments
            if status in ['completed'] and random.choice([True, False]):
                Bill.objects.create(
                    patient=patient,
                    amount=round(random.uniform(50, 500), 2),
                    paid=random.choice([True, False])
                )
                self.stdout.write(f'Created bill for appointment {appointment.id}')

        self.stdout.write(self.style.SUCCESS('Test data created successfully!'))