from flask import *
from PIL import Image, ImageDraw, ImageFont
import pandas as pd
import os
import zipfile
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, flash, session
import uuid
import json
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # Required for flash messages

# Folder setup
GENERATED_FOLDER = 'static/generated'
FONTS_FOLDER = 'static/fonts'
os.makedirs(GENERATED_FOLDER, exist_ok=True)

VALID_PASSWORD = "kuce&t"

def get_font_path(font_name):
    """Get the full path to a font file"""
    return os.path.join(FONTS_FOLDER, font_name)

def add_text_to_image(image, text, position, font_size=36, font_name="DancingScript-Regular.ttf", color=(0, 0, 0), max_width_ratio=0.8, line_spacing=1.2):
    """Add text to an image at specified position with center alignment and automatic wrapping.

    The text will be wrapped to fit within max_width_ratio of the image width, with each line
    centered horizontally around the provided position. The entire block is vertically centered
    on the given position as well.
    """
    try:
        draw = ImageDraw.Draw(image)

        # Load font
        font = None
        font_path = get_font_path(font_name)
        if os.path.exists(font_path):
            try:
                font = ImageFont.truetype(font_path, font_size)
            except Exception as e:
                print(f"Error loading font {font_name}: {e}")
                font = ImageFont.load_default()
        else:
            print(f"Font file not found: {font_path}")
            font = ImageFont.load_default()

        # Compute max text width allowed
        image_width, image_height = image.size
        max_text_width = int(image_width * max_width_ratio)

        # Prepare word-wrapped lines
        words = str(text).split()
        if not words:
            return image

        lines = []
        current_line = words[0]
        for word in words[1:]:
            test_line = current_line + " " + word
            bbox = draw.textbbox((0, 0), test_line, font=font)
            line_width = bbox[2] - bbox[0]
            if line_width <= max_text_width:
                current_line = test_line
            else:
                lines.append(current_line)
                current_line = word
        lines.append(current_line)

        # Measure total height to vertically center block
        line_heights = []
        max_line_width = 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            max_line_width = max(max_line_width, line_width)
            line_heights.append(line_height)

        # Total height with spacing between lines
        if line_heights:
            total_text_height = int(sum(line_heights[i] if i == 0 else line_heights[i] * line_spacing for i in range(len(line_heights))))
        else:
            total_text_height = 0

        # Start Y so that the block is centered at the provided position
        start_y = position[1] - total_text_height // 2

        # Draw each line centered horizontally at the given X
        current_y = start_y
        for i, line in enumerate(lines):
            bbox = draw.textbbox((0, 0), line, font=font)
            line_width = bbox[2] - bbox[0]
            line_height = bbox[3] - bbox[1]
            x = position[0] - line_width // 2
            draw.text((x, current_y), line, font=font, fill=color)
            # Advance Y with spacing for next line
            increment = line_height if i == 0 else int(line_height * line_spacing)
            current_y += increment

        return image
    except Exception as e:
        print(f"Error adding text: {e}")
        return image

def add_signature_to_image(image, signature_image, position_type="bottom_right", custom_x=None, custom_y=None, size_percentage=20):
    """Add signature to an image at specified position"""
    try:
        if signature_image is None:
            return image
            
        # Calculate signature size
        original_width, original_height = signature_image.size
        new_width = int(original_width * size_percentage / 100)
        new_height = int(original_height * size_percentage / 100)
        
        # Resize signature
        signature_resized = signature_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Calculate position
        template_width, template_height = image.size
        
        if position_type == "bottom_right":
            x = template_width - new_width - 20  # 20px margin from right edge
            y = template_height - new_height - 20  # 20px margin from bottom edge
        elif position_type == "bottom_left":
            x = 20  # 20px margin from left edge
            y = template_height - new_height - 20  # 20px margin from bottom edge
        elif position_type == "bottom_center":
            x = (template_width - new_width) // 2  # Center horizontally
            y = template_height - new_height - 20  # 20px margin from bottom edge
        elif position_type == "custom" and custom_x is not None and custom_y is not None:
            x = custom_x
            y = custom_y
        else:
            # Default to bottom right
            x = template_width - new_width - 20
            y = template_height - new_height - 20
        
        # Ensure position is within image bounds
        x = max(0, min(x, template_width - new_width))
        y = max(0, min(y, template_height - new_height))
        
        # Paste signature onto image
        if signature_resized.mode == 'RGBA':
            # Handle transparency
            image.paste(signature_resized, (x, y), signature_resized)
        else:
            # No transparency, paste directly
            image.paste(signature_resized, (x, y))
        
        return image
    except Exception as e:
        print(f"Error adding signature: {e}")
        return image

def calculate_text_position(template_width, template_height, field_type, field_index=0, layout_config=None):
    """Calculate optimal text position based on field type and template dimensions"""
    
    # Define relative positions (as percentages of template dimensions)
    positions = {
        'name': {
            'x': 0.5,  # 50% of width (center)
            'y': 0.45  # 45% of height (slightly above center)
        },
        'event': {
            'x': 0.5,
            'y': 0.55  # 55% of height (slightly below center)
        },
        'course': {
            'x': 0.5,
            'y': 0.65  # 65% of height
        },
        'date': {
            'x': 0.5,
            'y': 0.75  # 75% of height
        },
        'instructor': {
            'x': 0.5,
            'y': 0.85  # 85% of height
        },
        'organization': {
            'x': 0.5,
            'y': 0.92  # 92% of height
        },
        'duration': {
            'x': 0.5,
            'y': 0.95  # 95% of height
        },
        'top': {
            'x': 0.5,
            'y': 0.2  # 20% of height (top area)
        },
        'center': {
            'x': 0.5,
            'y': 0.5  # 50% of height (exact center)
        },
        'bottom': {
            'x': 0.5,
            'y': 0.8  # 80% of height (bottom area)
        },
        'default': {
            'x': 0.5,
            'y': 0.5 + (field_index * 0.08)  # Stack vertically with spacing
        }
    }
    
    # Check if custom layout is specified
    if layout_config and field_type in layout_config:
        custom_position = layout_config[field_type]
        if custom_position in positions:
            pos = positions[custom_position]
        else:
            pos = positions.get(field_type, positions['default'])
    else:
        pos = positions.get(field_type, positions['default'])
    
    # Convert percentages to actual pixel coordinates
    x = int(template_width * pos['x'])
    y = int(template_height * pos['y'])
    
    return (x, y)

def sanitize_filename(filename):
    """Sanitize filename by removing/replacing invalid characters"""
    import re
    # Remove or replace invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove extra spaces and replace with underscores
    filename = re.sub(r'\s+', '_', filename.strip())
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    # Remove leading/trailing underscores
    filename = filename.strip('_')
    # Limit length to avoid filesystem issues
    if len(filename) > 100:
        filename = filename[:100]
    # Ensure filename is not empty
    if not filename:
        filename = "Unknown"
    return filename

def get_field_type(column_name):
    """Determine field type based on column name"""
    column_lower = column_name.lower()
    
    if any(word in column_lower for word in ['name', 'full_name', 'participant', 'student', 'attendee']):
        return 'name'
    elif any(word in column_lower for word in ['event', 'program', 'workshop', 'seminar', 'conference']):
        return 'event'
    elif any(word in column_lower for word in ['course', 'training', 'certification', 'module', 'class']):
        return 'course'
    elif any(word in column_lower for word in ['date', 'completion_date', 'issued_date', 'graduation_date']):
        return 'date'
    elif any(word in column_lower for word in ['instructor', 'trainer', 'teacher', 'facilitator', 'presenter']):
        return 'instructor'
    elif any(word in column_lower for word in ['organization', 'company', 'institution', 'school', 'university']):
        return 'organization'
    elif any(word in column_lower for word in ['duration', 'hours', 'credits', 'length']):
        return 'duration'
    else:
        return 'default'

@app.route('/')
def home():
    return render_template('home.html')

@app.route('/verify_password', methods=['POST'])
def verify_password():
    password = request.form.get('password')
    if password == VALID_PASSWORD:
        return redirect(url_for('index'))
    else:
        flash('Invalid password! Try again.', 'error')
        return redirect(url_for('home'))

@app.route('/index')
def index():
    # Check if there's existing certificate session to restore form data
    form_data = None
    if 'certificate_session' in session:
        form_data = session['certificate_session'].get('form_data')
        print(f"DEBUG: Form data found in index: {form_data}")
    
    return render_template('index.html', form_data=form_data)

@app.route('/back_to_generate')
def back_to_generate():
    """Go back to generate page with preserved form data"""
    if 'certificate_session' not in session:
        return redirect(url_for('index'))
    
    # Keep the session data for form restoration but don't clean up files yet
    form_data = session['certificate_session'].get('form_data')
    print(f"DEBUG: Form data being restored: {form_data}")
    
    return render_template('index.html', form_data=form_data)

@app.route('/clear_session')
def clear_session():
    """Clear session data and start fresh"""
    if 'certificate_session' in session:
        session_id = session['certificate_session']['session_id']
        session_folder = os.path.join(GENERATED_FOLDER, session_id)
        if os.path.exists(session_folder):
            import shutil
            try:
                shutil.rmtree(session_folder)
            except Exception as e:
                print(f"Error cleaning up session folder: {e}")
        session.pop('certificate_session', None)
    
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate_certificates():
    # Check if we have existing form data and no new files uploaded
    existing_form_data = None
    if 'certificate_session' in session:
        existing_form_data = session['certificate_session'].get('form_data')
    
    # Check if new files are uploaded
    new_template = 'template' in request.files and request.files['template'].filename
    new_data_file = 'data_file' in request.files and request.files['data_file'].filename
    
    if not new_template and not new_data_file and existing_form_data:
        # Use existing files from previous session
        session_id = session['certificate_session']['session_id']
        session_folder = os.path.join(GENERATED_FOLDER, session_id)
        
        template_path = os.path.join(session_folder, existing_form_data['template_filename'])
        data_path = os.path.join(session_folder, existing_form_data['data_filename'])
        
        if not os.path.exists(template_path) or not os.path.exists(data_path):
            flash('Previous files not found. Please upload files again.', 'error')
            return redirect(url_for('index'))
        
        # Create file objects from existing files
        from werkzeug.datastructures import FileStorage
        template_file = FileStorage(open(template_path, 'rb'), filename=existing_form_data['template_filename'])
        data_file = FileStorage(open(data_path, 'rb'), filename=existing_form_data['data_filename'])
    else:
        # Use new uploaded files
        if 'data_file' not in request.files or 'template' not in request.files:
            return "Missing data file or template", 400
        data_file = request.files['data_file']
        template_file = request.files['template']

    font_name = request.form.get('font', 'DancingScript-Regular.ttf')
    font_size = int(request.form.get('fontsize', 36))
    
    # Get multiple signature configuration
    signature_images = {}
    signature_sizes = {}
    
    # Process all signature files (signature1, signature2, signature3, etc.)
    for key, value in request.files.items():
        if key.startswith('signature') and not key.endswith('_size'):
            try:
                signature_image = Image.open(value)
                # Convert to RGBA to handle transparency
                if signature_image.mode != 'RGBA':
                    signature_image = signature_image.convert('RGBA')
                signature_images[key] = signature_image
            except Exception as e:
                print(f"Error loading signature {key}: {e}")
                signature_images[key] = None
    
    # Process all signature sizes
    for key, value in request.form.items():
        if key.endswith('_size') and key.startswith('signature'):
            signature_sizes[key.replace('_size', '')] = int(value)
    
    # Get layout configuration
    layout_config = {}
    if request.form.get('name_position'):
        layout_config['name'] = request.form.get('name_position')
    if request.form.get('event_position'):
        layout_config['event'] = request.form.get('event_position')
    if request.form.get('date_position'):
        layout_config['date'] = request.form.get('date_position')
    if request.form.get('course_position'):
        layout_config['course'] = request.form.get('course_position')
    
    try:
        # Read the data file
        file_extension = os.path.splitext(data_file.filename)[1].lower()
        if file_extension == '.csv':
            df = pd.read_csv(data_file)
        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(data_file)
        else:
            return "Unsupported file format. Please upload a CSV or Excel file.", 400

        # Load the template image
        template = Image.open(template_file)
        
        # Convert template to RGB mode to avoid RGBA issues when saving as JPEG
        if template.mode == 'RGBA':
            # Create a white background
            background = Image.new('RGB', template.size, (255, 255, 255))
            background.paste(template, mask=template.split()[-1])  # Use alpha channel as mask
            template = background
        elif template.mode != 'RGB':
            template = template.convert('RGB')
        
        template_width, template_height = template.size

        # Load saved layout configuration
        saved_layout = {}
        layout_file_path = 'static/uploads/layout.json'
        if os.path.exists(layout_file_path):
            try:
                with open(layout_file_path, 'r') as f:
                    saved_layout = json.load(f)
            except Exception as e:
                print(f"Error loading layout file: {e}")
                saved_layout = {}

        # Generate unique session ID for this batch
        session_id = str(uuid.uuid4())
        session_folder = os.path.join(GENERATED_FOLDER, session_id)
        os.makedirs(session_folder, exist_ok=True)

        # Save template and data files for reuse
        template_filename = f"template_{session_id}.jpg"
        data_filename = f"data_{session_id}{file_extension}"
        
        template_path = os.path.join(session_folder, template_filename)
        data_path = os.path.join(session_folder, data_filename)
        
        template_file.save(template_path)
        data_file.save(data_path)

        # Create certificates
        certificate_files = []
        for idx, row in df.iterrows():
            # Extract student name for filename
            student_name = "Unknown"
            for field_name in row.index:
                if any(word in field_name.lower() for word in ['name', 'full_name', 'participant', 'student', 'attendee']):
                    student_name = str(row[field_name])
                    break
            
            # Create filename with student name
            sanitized_name = sanitize_filename(student_name)
            cert_name = f"certificate_{sanitized_name}_{idx + 1}.jpg"
            cert_path = os.path.join(session_folder, cert_name)
            cert_image = template.copy()
            
            # Only add text for fields that are in the saved layout
            for field_name, position in saved_layout.items():
                if field_name in row:
                    text_value = str(row[field_name])
                    # Convert canvas coordinates to image coordinates
                    x = int(position[0] * template_width / 1000)  # canvas width is 1000
                    y = int(position[1] * template_height / 700)  # canvas height is 700
                    
                    cert_image = add_text_to_image(
                        cert_image, 
                        text_value, 
                        (x, y), 
                        font_size, 
                        font_name
                    )
            
            # Add all signatures if provided and positioned
            for sig_key, sig_image in signature_images.items():
                if not sig_image:
                    continue
                # Map first uploaded signature key 'signature1' to layout key 'signature' if needed
                layout_key = None
                if sig_key in saved_layout:
                    layout_key = sig_key
                elif sig_key == 'signature1' and 'signature' in saved_layout:
                    layout_key = 'signature'
                # Also handle potential keys like 'signature2', 'signature3' placed as-is
                if layout_key is None:
                    continue

                # Convert canvas coordinates to image coordinates
                signature_x = int(saved_layout[layout_key][0] * template_width / 1000)  # canvas width is 1000
                signature_y = int(saved_layout[layout_key][1] * template_height / 700)  # canvas height is 700

                # Get size for this signature
                sig_size = signature_sizes.get(sig_key, 20)

                cert_image = add_signature_to_image(
                    cert_image,
                    sig_image,
                    "custom",
                    signature_x,
                    signature_y,
                    sig_size
                )
            
            # Ensure image is in RGB mode before saving as JPEG
            if cert_image.mode == 'RGBA':
                # Create a white background
                background = Image.new('RGB', cert_image.size, (255, 255, 255))
                background.paste(cert_image, mask=cert_image.split()[-1])  # Use alpha channel as mask
                cert_image = background
            elif cert_image.mode not in ['RGB', 'L']:
                # Convert other modes to RGB
                cert_image = cert_image.convert('RGB')
            elif cert_image.mode == 'L':
                # Convert grayscale to RGB
                cert_image = cert_image.convert('RGB')
            
            try:
                cert_image.save(cert_path, 'JPEG', quality=95)
                certificate_files.append(cert_name)
            except Exception as e:
                print(f"Error saving certificate {cert_name}: {e}")
                print(f"Image mode: {cert_image.mode}, Size: {cert_image.size}")
                # Try to save as PNG if JPEG fails
                try:
                    png_path = cert_path.replace('.jpg', '.png')
                    cert_image.save(png_path, 'PNG')
                    certificate_files.append(os.path.basename(png_path))
                    print(f"Saved as PNG instead: {png_path}")
                except Exception as png_error:
                    print(f"Failed to save as PNG too: {png_error}")
                    raise e

        # Extract student names for display
        student_names = []
        recipient_emails = []
        for idx, row in df.iterrows():
            # Try to find name field in the row
            name_value = "Unknown"
            email_value = None
            for field_name in row.index:
                if any(word in field_name.lower() for word in ['name', 'full_name', 'participant', 'student', 'attendee']):
                    name_value = str(row[field_name])
                # capture email
                if email_value is None and ('email' in field_name.lower() or 'mail' in field_name.lower()):
                    email_value = str(row[field_name])
            student_names.append(name_value)
            recipient_emails.append(email_value if email_value is not None else '')

        # Store session info for preview and download
        session['certificate_session'] = {
            'session_id': session_id,
            'total_certificates': len(df),
            'certificate_files': certificate_files,
            'student_names': student_names,
            'recipient_emails': recipient_emails,
            'form_data': {
                'font_name': font_name,
                'font_size': font_size,
                'layout_config': layout_config,
                'template_filename': template_filename,
                'data_filename': data_filename,
                'file_extension': file_extension,
                'signature_sizes': signature_sizes
            }
        }
        
        print(f"DEBUG: Form data being saved: {session['certificate_session']['form_data']}")

        return redirect(url_for('preview_certificates'))

    except Exception as e:
        return f"Error generating certificates: {str(e)}", 500

@app.route('/preview')
def preview_certificates():
    if 'certificate_session' not in session:
        flash('No certificates to preview. Please generate certificates first.', 'error')
        return redirect(url_for('index'))
    
    session_data = session['certificate_session']
    session_id = session_data['session_id']
    certificate_files = session_data['certificate_files']
    
    return render_template('preview.html', 
                         session_id=session_id, 
                         certificate_files=certificate_files,
                         student_names=session_data.get('student_names', []),
                         total_certificates=session_data['total_certificates'])

@app.route('/download')
def download_certificates():
    if 'certificate_session' not in session:
        flash('No certificates to download. Please generate certificates first.', 'error')
        return redirect(url_for('index'))
    
    session_id = session['certificate_session']['session_id']
    session_folder = os.path.join(GENERATED_FOLDER, session_id)
    
    if not os.path.exists(session_folder):
        flash('Certificate files not found. Please generate certificates again.', 'error')
        return redirect(url_for('index'))
    
    # Determine download format (zip or pdf)
    download_format = request.args.get('format', 'zip').lower()

    try:
        # Collect certificate image paths
        image_filenames = [fn for fn in os.listdir(session_folder)
                           if os.path.isfile(os.path.join(session_folder, fn))
                           and fn.startswith('certificate_')
                           and (fn.lower().endswith('.jpg') or fn.lower().endswith('.png'))]
        image_filenames.sort()

        if download_format == 'pdf':
            if not image_filenames:
                return 'No certificates found to include in PDF.', 400

            # Open images and convert to RGB
            images = []
            for fn in image_filenames:
                img = Image.open(os.path.join(session_folder, fn))
                if img.mode in ['RGBA', 'P']:
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                images.append(img)

            # Save all into a single PDF
            pdf_buffer = BytesIO()
            try:
                first_image, *rest_images = images
                first_image.save(pdf_buffer, format='PDF', save_all=True, append_images=rest_images)
            finally:
                # Close images to free resources
                for im in images:
                    try:
                        im.close()
                    except Exception:
                        pass
            pdf_buffer.seek(0)

            # Cleanup after preparing download
            import shutil
            shutil.rmtree(session_folder)
            session.pop('certificate_session', None)

            return send_file(
                pdf_buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name='certificates.pdf'
            )
        else:
            # Default: ZIP
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in image_filenames:
                    file_path = os.path.join(session_folder, filename)
                    zipf.write(file_path, arcname=filename)
            zip_buffer.seek(0)

            # Cleanup after preparing download
            import shutil
            shutil.rmtree(session_folder)
            session.pop('certificate_session', None)

            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name='certificates.zip'
            )

    except Exception as e:
        return f"Error downloading certificates: {str(e)}", 500

@app.route('/static/generated/<session_id>/<filename>')
def serve_certificate(session_id, filename):
    """Serve individual certificate images for preview"""
    file_path = os.path.join(GENERATED_FOLDER, session_id, filename)
    if os.path.exists(file_path):
        return send_file(file_path)
    else:
        return "Certificate not found", 404

@app.route('/save_layout', methods=['POST'])
def save_layout():
    """Save layout configuration from the position editor"""
    try:
        layout_data = request.get_json()
        # Save layout to a JSON file
        with open('static/uploads/layout.json', 'w') as f:
            json.dump(layout_data, f, indent=2)
        return jsonify({"status": "success", "message": "Layout saved successfully!"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/send_emails', methods=['POST'])
def send_emails():
    if 'certificate_session' not in session:
        flash('No certificates to email. Please generate certificates first.', 'error')
        return redirect(url_for('index'))

    session_data = session['certificate_session']
    session_id = session_data['session_id']
    session_folder = os.path.join(GENERATED_FOLDER, session_id)

    # Read SMTP and email details
    sender_email = request.form.get('sender_email')
    sender_password = request.form.get('sender_password')
    smtp_host = request.form.get('smtp_host')
    smtp_port = int(request.form.get('smtp_port', 587))
    subject = request.form.get('subject', 'Your Certificate')
    body = request.form.get('body', 'Please find your certificate attached.')

    # Validate inputs
    if not all([sender_email, sender_password, smtp_host, smtp_port]):
        flash('Missing SMTP settings. Please fill all fields.', 'error')
        return redirect(url_for('preview_certificates'))

    # Prefer recipient emails stored during generation
    recipient_emails = session_data.get('recipient_emails')
    df = None
    email_col = None
    if not recipient_emails or all((not e or str(e).strip().lower() in ['nan', 'none']) for e in recipient_emails):
        # Fallback: try reading data file (if still present)
        data_filename = session_data['form_data']['data_filename']
        data_path = os.path.join(session_folder, data_filename)
        try:
            ext = os.path.splitext(data_filename)[1].lower()
            if ext == '.csv':
                df = pd.read_csv(data_path)
            else:
                df = pd.read_excel(data_path)
        except Exception as e:
            flash(f'Failed to read data file for emails: {e}', 'error')
            return redirect(url_for('preview_certificates'))

        # Heuristically detect email column
        for col in df.columns:
            cl = str(col).lower()
            if 'email' in cl or 'mail' in cl:
                email_col = col
                break
        if email_col is None:
            flash('No email column found in your data. Include a column with "email" in its name.', 'error')
            return redirect(url_for('preview_certificates'))

    # Map certificates to rows (order preserved from generation)
    certificate_files = session_data['certificate_files']
    total = len(certificate_files)
    sent = 0
    failures = []

    try:
        server = smtplib.SMTP(smtp_host, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
    except Exception as e:
        flash(f'SMTP login failed: {e}', 'error')
        return redirect(url_for('preview_certificates'))

    try:
        for idx, cert_filename in enumerate(certificate_files):
            # Guard against mismatch sizes
            if recipient_emails:
                if idx >= len(recipient_emails):
                    break
                recipient = str(recipient_emails[idx] or '').strip()
            else:
                if df is None or idx >= len(df):
                    break
                recipient = str(df.iloc[idx][email_col]).strip()
            if not recipient or recipient.lower() in ['nan', 'none']:
                failures.append((idx + 1, 'Missing email'))
                continue

            cert_path = os.path.join(session_folder, cert_filename)
            if not os.path.exists(cert_path):
                failures.append((idx + 1, 'Certificate file missing'))
                continue

            try:
                msg = EmailMessage()
                msg['From'] = sender_email
                msg['To'] = recipient
                msg['Subject'] = subject
                msg.set_content(body)

                # Attach certificate
                with open(cert_path, 'rb') as f:
                    data = f.read()
                # Determine mime subtype by extension
                subtype = 'jpeg' if cert_filename.lower().endswith('.jpg') else 'png'
                msg.add_attachment(data, maintype='image', subtype=subtype, filename=cert_filename)

                server.send_message(msg)
                sent += 1
            except Exception as send_err:
                failures.append((idx + 1, str(send_err)))
                continue
    finally:
        try:
            server.quit()
        except Exception:
            pass

    # Prepare modal parameters
    if sent == total and not failures:
        success = True
        message = f'Successfully sent {sent}/{total} certificates to student emails!'
        details = f'All {total} certificates have been issued and delivered to their respective email addresses.'
    else:
        success = False
        message = f'Sent {sent}/{total} certificates. {len(failures)} failed.'
        details = f'Successfully delivered {sent} certificates to student emails.'
        if failures:
            fail_msg = ', '.join([f"#{i}:{err}" for i, err in failures[:5]])
            if len(failures) > 5:
                fail_msg += f" (+{len(failures)-5} more)"
            details += f'<br><br>Failures: {fail_msg}'

    # Redirect with modal parameters
    return redirect(url_for('preview_certificates', 
                          email_sent='true', 
                          email_success=str(success).lower(),
                          email_message=message,
                          email_details=details))

if __name__ == "__main__":
    print("✅ Flask app running at: http://127.0.0.1:5000/")
    print("📎 Try these URLs in your browser:")
    print("  • Home page:            http://127.0.0.1:5000/")
    app.run(debug=True)
