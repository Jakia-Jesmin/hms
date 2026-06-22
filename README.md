cat > README.md << 'EOF'
# Hospital Management System (HMS) API

A comprehensive RESTful API for Hospital Management System built with Django REST Framework.

## Features

- 🔐 **Authentication**: JWT-based authentication with role-based access control
- 👤 **User Management**: Register, Login, Profile Management
- 👨‍⚕️ **Doctor Management**: CRUD operations, availability toggle
- 🏥 **Patient Management**: Complete patient records
- 📋 **Appointment Management**: Book, view, update, cancel appointments
- 💊 **Prescription Management**: Create prescriptions with multiple medicines
- 💰 **Billing**: Generate bills, mark as paid
- 🔍 **Search & Filter**: Search medicines, filter appointments

## User Roles

- **Admin**: Full system access
- **Doctor**: Manage appointments, create prescriptions
- **Patient**: View appointments, prescriptions, bills
- **Receptionist**: Manage appointments, patients, bills

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment

### Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/HMS.git
cd HMS