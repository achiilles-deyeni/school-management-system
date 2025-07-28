# utils/file_handler.py - File Upload and Management Utilities
import os
import uuid
from werkzeug.utils import secure_filename
from PIL import Image
import logging
from datetime import datetime
import mimetypes
import hashlib

logger = logging.getLogger(__name__)

# Configuration
UPLOAD_FOLDERS = {
    'students': 'static/uploads/students',
    'teachers': 'static/uploads/teachers',
    'events': 'static/uploads/events',
    'documents': 'static/uploads/documents'
}

ALLOWED_EXTENSIONS = {
    'images': {'png', 'jpg', 'jpeg', 'gif', 'webp'},
    'documents': {'pdf', 'doc', 'docx', 'txt', 'rtf'},
    'spreadsheets': {'xls', 'xlsx', 'csv'},
    'all': {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx', 'txt', 'rtf', 'xls', 'xlsx', 'csv'}
}

MAX_FILE_SIZES = {
    'images': 5 * 1024 * 1024,  # 5MB for images
    'documents': 10 * 1024 * 1024,  # 10MB for documents
    'spreadsheets': 5 * 1024 * 1024,  # 5MB for spreadsheets
    'default': 5 * 1024 * 1024  # 5MB default
}

# Image settings
IMAGE_SIZES = {
    'thumbnail': (150, 150),
    'small': (300, 300),
    'medium': (600, 600),
    'large': (1200, 1200)
}


def ensure_upload_folders():
    """Ensure all upload folders exist"""
    try:
        for folder_path in UPLOAD_FOLDERS.values():
            os.makedirs(folder_path, exist_ok=True)

            # Create subfolders for different image sizes
            if 'students' in folder_path or 'teachers' in folder_path:
                for size_name in IMAGE_SIZES.keys():
                    size_folder = os.path.join(folder_path, size_name)
                    os.makedirs(size_folder, exist_ok=True)

        logger.info("Upload folders ensured")
        return True

    except Exception as e:
        logger.error(f"Error ensuring upload folders: {str(e)}")
        return False


def allowed_file(filename, file_type='images'):
    """Check if file extension is allowed"""
    if not filename:
        return False

    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
    allowed_exts = ALLOWED_EXTENSIONS.get(file_type, ALLOWED_EXTENSIONS['all'])

    return extension in allowed_exts


def get_file_type(filename):
    """Determine file type category"""
    if not filename or '.' not in filename:
        return 'unknown'

    extension = filename.rsplit('.', 1)[1].lower()

    for file_type, extensions in ALLOWED_EXTENSIONS.items():
        if extension in extensions:
            return file_type

    return 'unknown'


def validate_file_size(file, file_type=None):
    """Validate file size"""
    try:
        # Get file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)  # Reset file pointer

        # Get max size for file type
        max_size = MAX_FILE_SIZES.get(file_type, MAX_FILE_SIZES['default'])

        return file_size <= max_size, file_size, max_size

    except Exception as e:
        logger.error(f"Error validating file size: {str(e)}")
        return False, 0, 0


def generate_unique_filename(original_filename, prefix=''):
    """Generate unique filename while preserving extension"""
    if not original_filename:
        return None

    # Get file extension
    extension = ''
    if '.' in original_filename:
        extension = '.' + original_filename.rsplit('.', 1)[1].lower()

    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    unique_id = str(uuid.uuid4())[:8]

    if prefix:
        filename = f"{prefix}_{timestamp}_{unique_id}{extension}"
    else:
        filename = f"{timestamp}_{unique_id}{extension}"

    return filename


def save_student_photo(file, student_id=None):
    """Save student photo with multiple sizes"""
    try:
        if not file or not file.filename:
            return None

        # Validate file
        if not allowed_file(file.filename, 'images'):
            raise ValueError("Invalid file type. Only images are allowed.")

        # Validate file size
        is_valid_size, file_size, max_size = validate_file_size(file, 'images')
        if not is_valid_size:
            raise ValueError(f"File too large. Maximum size is {max_size // 1024 // 1024}MB")

        # Ensure upload folder exists
        ensure_upload_folders()

        # Generate filename
        prefix = f"student_{student_id}" if student_id else "student"
        filename = generate_unique_filename(file.filename, prefix)

        # Save original file
        original_path = os.path.join(UPLOAD_FOLDERS['students'], filename)
        file.save(original_path)

        # Create different sized versions
        create_image_sizes(original_path, UPLOAD_FOLDERS['students'])

        logger.info(f"Student photo saved: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error saving student photo: {str(e)}")
        raise Exception(f"Failed to save photo: {str(e)}")


def save_teacher_photo(file, teacher_id=None):
    """Save teacher photo with multiple sizes"""
    try:
        if not file or not file.filename:
            return None

        # Validate file
        if not allowed_file(file.filename, 'images'):
            raise ValueError("Invalid file type. Only images are allowed.")

        # Validate file size
        is_valid_size, file_size, max_size = validate_file_size(file, 'images')
        if not is_valid_size:
            raise ValueError(f"File too large. Maximum size is {max_size // 1024 // 1024}MB")

        # Ensure upload folder exists
        ensure_upload_folders()

        # Generate filename
        prefix = f"teacher_{teacher_id}" if teacher_id else "teacher"
        filename = generate_unique_filename(file.filename, prefix)

        # Save original file
        original_path = os.path.join(UPLOAD_FOLDERS['teachers'], filename)
        file.save(original_path)

        # Create different sized versions
        create_image_sizes(original_path, UPLOAD_FOLDERS['teachers'])

        logger.info(f"Teacher photo saved: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error saving teacher photo: {str(e)}")
        raise Exception(f"Failed to save photo: {str(e)}")


def save_document(file, document_type='general'):
    """Save document file"""
    try:
        if not file or not file.filename:
            return None

        # Determine file type
        file_type = get_file_type(file.filename)

        # Validate file type
        if file_type not in ['documents', 'spreadsheets']:
            raise ValueError("Invalid file type. Only documents and spreadsheets are allowed.")

        # Validate file size
        is_valid_size, file_size, max_size = validate_file_size(file, file_type)
        if not is_valid_size:
            raise ValueError(f"File too large. Maximum size is {max_size // 1024 // 1024}MB")

        # Ensure upload folder exists
        ensure_upload_folders()

        # Generate filename
        filename = generate_unique_filename(file.filename, document_type)

        # Save file
        file_path = os.path.join(UPLOAD_FOLDERS['documents'], filename)
        file.save(file_path)

        logger.info(f"Document saved: {filename}")
        return filename

    except Exception as e:
        logger.error(f"Error saving document: {str(e)}")
        raise Exception(f"Failed to save document: {str(e)}")


def create_image_sizes(original_path, base_folder):
    """Create different sized versions of an image"""
    try:
        filename = os.path.basename(original_path)

        with Image.open(original_path) as img:
            # Convert to RGB if necessary (for JPEG compatibility)
            if img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')

            # Create different sized versions
            for size_name, (width, height) in IMAGE_SIZES.items():
                # Calculate aspect ratio preserving dimensions
                img_ratio = img.width / img.height
                target_ratio = width / height

                if img_ratio > target_ratio:
                    # Image is wider than target
                    new_width = width
                    new_height = int(width / img_ratio)
                else:
                    # Image is taller than target
                    new_height = height
                    new_width = int(height * img_ratio)

                # Resize image
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

                # Create thumbnail with padding if needed
                if size_name == 'thumbnail':
                    thumb = Image.new('RGB', (width, height), (255, 255, 255))
                    paste_x = (width - new_width) // 2
                    paste_y = (height - new_height) // 2
                    thumb.paste(resized_img, (paste_x, paste_y))
                    resized_img = thumb

                # Save resized image
                size_folder = os.path.join(base_folder, size_name)
                size_path = os.path.join(size_folder, filename)

                # Save with optimization
                quality = 95 if size_name in ['large', 'medium'] else 85
                resized_img.save(size_path, 'JPEG', quality=quality, optimize=True)

        logger.info(f"Image sizes created for: {filename}")
        return True

    except Exception as e:
        logger.error(f"Error creating image sizes: {str(e)}")
        return False


def delete_file(filename, folder_type='students'):
    """Delete file and all its versions"""
    try:
        if not filename:
            return True

        base_folder = UPLOAD_FOLDERS.get(folder_type, UPLOAD_FOLDERS['students'])

        # Delete original file
        original_path = os.path.join(base_folder, filename)
        if os.path.exists(original_path):
            os.remove(original_path)

        # Delete sized versions for images
        if folder_type in ['students', 'teachers']:
            for size_name in IMAGE_SIZES.keys():
                size_path = os.path.join(base_folder, size_name, filename)
                if os.path.exists(size_path):
                    os.remove(size_path)

        logger.info(f"File deleted: {filename}")
        return True

    except Exception as e:
        logger.error(f"Error deleting file {filename}: {str(e)}")
        return False


def get_file_info(filename, folder_type='students'):
    """Get file information"""
    try:
        if not filename:
            return None

        base_folder = UPLOAD_FOLDERS.get(folder_type, UPLOAD_FOLDERS['students'])
        file_path = os.path.join(base_folder, filename)

        if not os.path.exists(file_path):
            return None

        stat = os.stat(file_path)

        return {
            'filename': filename,
            'size': stat.st_size,
            'size_mb': round(stat.st_size / 1024 / 1024, 2),
            'created': datetime.fromtimestamp(stat.st_ctime),
            'modified': datetime.fromtimestamp(stat.st_mtime),
            'mime_type': mimetypes.guess_type(file_path)[0],
            'exists': True
        }

    except Exception as e:
        logger.error(f"Error getting file info for {filename}: {str(e)}")
        return None


def get_image_url(filename, size='medium', folder_type='students'):
    """Get URL for specific image size"""
    if not filename:
        return '/static/images/default_avatar.png'

    if size in IMAGE_SIZES and folder_type in ['students', 'teachers']:
        return f"/static/uploads/{folder_type}/{size}/{filename}"
    else:
        return f"/static/uploads/{folder_type}/{filename}"


def cleanup_old_files(folder_type='students', retention_days=30):
    """Clean up old files older than the specified retention period."""
    try:
        base_folder = UPLOAD_FOLDERS.get(folder_type, UPLOAD_FOLDERS['students'])

        # Get the current date and time
        current_time = datetime.now()

        # Iterate over all files in the base folder
        for root, dirs, files in os.walk(base_folder):
            for file in files:
                file_path = os.path.join(root, file)

                # Get the last modified time of the file
                file_stat = os.stat(file_path)
                last_modified_time = datetime.fromtimestamp(file_stat.st_mtime)

                # Calculate the file age in days
                file_age_days = (current_time - last_modified_time).days

                # If the file is older than the retention period, delete it
                if file_age_days > retention_days:
                    os.remove(file_path)
                    logger.info(f"Old file deleted: {file_path}")

        logger.info("Cleanup completed.")
        return True

    except Exception as e:
        logger.error(f"Error during cleanup of old files: {str(e)}")
        return False
