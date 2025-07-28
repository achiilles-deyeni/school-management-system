# utils/validators.py - Comprehensive Input Validation
import re
from datetime import datetime, date
from dateutil import parser
import logging

logger = logging.getLogger(__name__)


def validate_email(email):
    """Validate email format"""
    if not email:
        return False

    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email.strip()) is not None


def validate_phone(phone):
    """Validate phone number format (Ghana format)"""
    if not phone:
        return False

    # Remove spaces, dashes, and parentheses
    clean_phone = re.sub(r'[\s\-\(\)]', '', phone)

    # Ghana phone patterns
    patterns = [
        r'^0[2-9]\d{8}$',  # Local format: 0XXXXXXXXX
        r'^\+233[2-9]\d{8}$',  # International: +233XXXXXXXXX
        r'^233[2-9]\d{8}$',  # International without +: 233XXXXXXXXX
    ]

    return any(re.match(pattern, clean_phone) for pattern in patterns)


def validate_student_id_format(student_id):
    """Validate student ID format"""
    if not student_id:
        return False

    # Format: STU + 2-digit year + 4-digit sequence (e.g., STU240001)
    pattern = r'^STU\d{6}$'
    return re.match(pattern, student_id.upper()) is not None


def validate_date(date_str, field_name="Date"):
    """Validate date format and reasonableness"""
    if not date_str:
        return False, f"{field_name} is required"

    try:
        # Try to parse the date
        parsed_date = parser.parse(date_str).date()

        # Check if date is reasonable (not in future for birth dates, etc.)
        today = date.today()

        if field_name.lower() in ['date_of_birth', 'birth_date']:
            # Birth date should not be in future or too far in past (150 years)
            if parsed_date > today:
                return False, "Birth date cannot be in the future"

            min_date = date(today.year - 150, 1, 1)
            if parsed_date < min_date:
                return False, "Birth date is too far in the past"

        elif field_name.lower() in ['admission_date']:
            # Admission date should be reasonable (within school operation period)
            min_date = date(1950, 1, 1)  # Assuming school started after 1950
            max_date = date(today.year + 1, 12, 31)  # Allow future admissions

            if parsed_date < min_date or parsed_date > max_date:
                return False, f"Admission date must be between {min_date} and {max_date}"

        return True, parsed_date

    except (ValueError, TypeError) as e:
        return False, f"Invalid {field_name.lower()} format"


def validate_name(name, field_name="Name", min_length=2, max_length=50):
    """Validate person names"""
    if not name or not name.strip():
        return False, f"{field_name} is required"

    name = name.strip()

    if len(name) < min_length:
        return False, f"{field_name} must be at least {min_length} characters"

    if len(name) > max_length:
        return False, f"{field_name} must not exceed {max_length} characters"

    # Allow letters, spaces, hyphens, apostrophes (for names like O'Connor, Mary-Jane)
    if not re.match(r"^[a-zA-Z\s\-'\.]+$", name):
        return False, f"{field_name} can only contain letters, spaces, hyphens, and apostrophes"

    return True, name.title()  # Return title-cased name


def validate_gender(gender):
    """Validate gender selection"""
    valid_genders = ['male', 'female', 'other']

    if not gender:
        return False, "Gender is required"

    if gender.lower() not in valid_genders:
        return False, f"Gender must be one of: {', '.join(valid_genders)}"

    return True, gender.lower()


def validate_class_name(class_name):
    """Validate class/grade name"""
    if not class_name or not class_name.strip():
        return False, "Class is required"

    class_name = class_name.strip()

    # Common class formats: Grade 1, Form 1, JHS 1, SHS 1, Primary 1, etc.
    if len(class_name) > 20:
        return False, "Class name is too long"

    return True, class_name.upper()


def validate_password(password, min_length=8):
    """Validate password strength"""
    if not password:
        return False, "Password is required"

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters long"

    # Check for at least one letter and one number
    if not re.search(r'[a-zA-Z]', password):
        return False, "Password must contain at least one letter"

    if not re.search(r'\d', password):
        return False, "Password must contain at least one number"

    # Check for common weak passwords
    weak_passwords = [
        'password', '12345678', 'qwerty', 'abc123', 'password123',
        '11111111', '00000000', 'letmein', 'welcome', 'admin'
    ]

    if password.lower() in weak_passwords:
        return False, "Password is too common. Please choose a stronger password"

    return True, password


def validate_student_data(data, is_update=False):
    """Validate complete student data"""
    errors = []

    # Validate required fields for new students
    if not is_update:
        required_fields = ['first_name', 'last_name', 'gender', 'date_of_birth', 'class_name']
        for field in required_fields:
            if not data.get(field, '').strip():
                errors.append(f"{field.replace('_', ' ').title()} is required")

    # Validate first name
    if data.get('first_name'):
        is_valid, result = validate_name(data['first_name'], "First name")
        if not is_valid:
            errors.append(result)

    # Validate last name
    if data.get('last_name'):
        is_valid, result = validate_name(data['last_name'], "Last name")
        if not is_valid:
            errors.append(result)

    # Validate gender
    if data.get('gender'):
        is_valid, result = validate_gender(data['gender'])
        if not is_valid:
            errors.append(result)

    # Validate date of birth
    if data.get('date_of_birth'):
        is_valid, result = validate_date(data['date_of_birth'], "Date of birth")
        if not is_valid:
            errors.append(result)

    # Validate guardian name
    if data.get('guardian_name'):
        is_valid, result = validate_name(data['guardian_name'], "Guardian name")
        if not is_valid:
            errors.append(result)

    # Validate guardian phone
    if data.get('guardian_phone'):
        if not validate_phone(data['guardian_phone']):
            errors.append("Guardian phone number format is invalid")

    # Validate guardian email (optional)
    if data.get('guardian_email') and data['guardian_email'].strip():
        if not validate_email(data['guardian_email']):
            errors.append("Guardian email format is invalid")

    # Validate emergency phone (optional)
    if data.get('emergency_phone') and data['emergency_phone'].strip():
        if not validate_phone(data['emergency_phone']):
            errors.append("Emergency phone number format is invalid")

    # Validate class name
    if data.get('class_name'):
        is_valid, result = validate_class_name(data['class_name'])
        if not is_valid:
            errors.append(result)

    # Validate admission date (optional)
    if data.get('admission_date'):
        is_valid, result = validate_date(data['admission_date'], "Admission date")
        if not is_valid:
            errors.append(result)

    # Validate address length
    if data.get('address') and len(data['address']) > 200:
        errors.append("Address is too long (maximum 200 characters)")

    # Validate medical info length
    if data.get('medical_info') and len(data['medical_info']) > 500:
        errors.append("Medical information is too long (maximum 500 characters)")

    return errors


def validate_teacher_data(data, is_update=False):
    """Validate teacher data"""
    errors = []

    # Required fields for new teachers
    if not is_update:
        required_fields = ['first_name', 'last_name', 'email', 'phone', 'subject']
        for field in required_fields:
            if not data.get(field, '').strip():
                errors.append(f"{field.replace('_', ' ').title()} is required")

    # Validate names
    for name_field in ['first_name', 'last_name']:
        if data.get(name_field):
            is_valid, result = validate_name(data[name_field], name_field.replace('_', ' ').title())
            if not is_valid:
                errors.append(result)

    # Validate email
    if data.get('email'):
        if not validate_email(data['email']):
            errors.append("Email format is invalid")

    # Validate phone
    if data.get('phone'):
        if not validate_phone(data['phone']):
            errors.append("Phone number format is invalid")

    # Validate date of birth (optional for teachers)
    if data.get('date_of_birth'):
        is_valid, result = validate_date(data['date_of_birth'], "Date of birth")
        if not is_valid:
            errors.append(result)

    # Validate hire date (optional)
    if data.get('hire_date'):
        is_valid, result = validate_date(data['hire_date'], "Hire date")
        if not is_valid:
            errors.append(result)

    return errors


def validate_event_data(data, is_update=False):
    """Validate event data"""
    errors = []

    # Required fields
    if not is_update:
        required_fields = ['title', 'date', 'location']
        for field in required_fields:
            if not data.get(field, '').strip():
                errors.append(f"{field.title()} is required")

    # Validate title
    if data.get('title'):
        title = data['title'].strip()
        if len(title) < 3:
            errors.append("Event title must be at least 3 characters")
        if len(title) > 100:
            errors.append("Event title is too long (maximum 100 characters)")

    # Validate date
    if data.get('date'):
        is_valid, result = validate_date(data['date'], "Event date")
        if not is_valid:
            errors.append(result)
        else:
            # Event date should not be too far in the past
            if isinstance(result, date):
                today = date.today()
                if result < today:
                    errors.append("Event date cannot be in the past")

    # Validate location
    if data.get('location'):
        location = data['location'].strip()
        if len(location) < 2:
            errors.append("Location must be at least 2 characters")
        if len(location) > 100:
            errors.append("Location is too long (maximum 100 characters)")

    # Validate description length
    if data.get('description') and len(data['description']) > 1000:
        errors.append("Description is too long (maximum 1000 characters)")

    return errors


def validate_admin_data(data, is_update=False):
    """Validate admin input data"""
    errors = []

    # Required fields
    if not is_update:
        required_fields = ['first_name', 'last_name', 'email', 'password']
        for field in required_fields:
            if not data.get(field, '').strip():
                errors.append(f"{field.replace('_', ' ').title()} is required")

    # Validate names
    for name_field in ['first_name', 'last_name']:
        if data.get(name_field):
            is_valid, result = validate_name(data[name_field], name_field.replace('_', ' ').title())
            if not is_valid:
                errors.append(result)

    # Validate email
    if data.get('email'):
        if not validate_email(data['email']):
            errors.append("Email format is invalid")

    # Validate password (only if creating or updating password)
    if not is_update or data.get('password'):
        is_valid, result = validate_password(data.get('password', ''))
        if not is_valid:
            errors.append(result)

    return errors


def validate_donation_data(data):
    """Validate donation data"""
    errors = []

    # Required fields
    required_fields = ['donor_name', 'amount', 'date']
    for field in required_fields:
        if not data.get(field, '').strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")

    # Validate donor name
    if data.get('donor_name'):
        is_valid, result = validate_name(data['donor_name'], "Donor name", max_length=100)
        if not is_valid:
            errors.append(result)

    # Validate amount
    if data.get('amount'):
        try:
            amount = float(data['amount'])
            if amount <= 0:
                errors.append("Donation amount must be greater than 0")
            if amount > 1000000:  # 1 million limit
                errors.append("Donation amount is too large")
        except (ValueError, TypeError):
            errors.append("Invalid donation amount")

    # Validate date
    if data.get('date'):
        is_valid, result = validate_date(data['date'], "Donation date")
        if not is_valid:
            errors.append(result)

    # Validate email (optional)
    if data.get('donor_email') and data['donor_email'].strip():
        if not validate_email(data['donor_email']):
            errors.append("Donor email format is invalid")

    # Validate phone (optional)
    if data.get('donor_phone') and data['donor_phone'].strip():
        if not validate_phone(data['donor_phone']):
            errors.append("Donor phone number format is invalid")

    return errors


def validate_expense_data(data):
    """Validate expense data"""
    errors = []

    # Required fields
    required_fields = ['description', 'amount', 'date', 'category']
    for field in required_fields:
        if not data.get(field, '').strip():
            errors.append(f"{field.replace('_', ' ').title()} is required")

    # Validate description
    if data.get('description'):
        description = data['description'].strip()
        if len(description) < 3:
            errors.append("Description must be at least 3 characters")
        if len(description) > 200:
            errors.append("Description is too long (maximum 200 characters)")

    # Validate amount
    if data.get('amount'):
        try:
            amount = float(data['amount'])
            if amount <= 0:
                errors.append("Expense amount must be greater than 0")
            if amount > 1000000:  # 1 million limit
                errors.append("Expense amount is too large")
        except (ValueError, TypeError):
            errors.append("Invalid expense amount")

    # Validate date
    if data.get('date'):
        is_valid, result = validate_date(data['date'], "Expense date")
        if not is_valid:
            errors.append(result)

    # Validate category
    valid_categories = [
        'supplies', 'utilities', 'maintenance', 'salaries', 'transport',
        'food', 'equipment', 'events', 'other'
    ]

    if data.get('category'):
        if data['category'].lower() not in valid_categories:
            errors.append(f"Category must be one of: {', '.join(valid_categories)}")

    return errors


def sanitize_input(input_string, max_length=None):
    """Sanitize user input by removing potentially harmful characters"""
    if not input_string:
        return ""

    # Remove potential script tags and other harmful content
    sanitized = re.sub(r'<[^>]*>', '', str(input_string))

    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)

    # Trim whitespace
    sanitized = sanitized.strip()

    # Limit length if specified
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]

    return sanitized


def is_safe_filename(filename):
    """Check if filename is safe for upload"""
    if not filename:
        return False

    # Remove directory path attempts
    filename = filename.split('/')[-1].split('\\')[-1]

    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\.', r'[<>:"|?*]', r'^(con|prn|aux|nul|com[1-9]|lpt[1-9])(\.|$)',
        r'^\s*$', r'^\.'
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return False

    # Check length
    if len(filename) > 255:
        return False

    return True