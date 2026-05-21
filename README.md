# Certificate Generator

A web-based application that generates certificates in bulk using a template and data from Excel/CSV files.

## Features

- **Secure Access**: Password-protected access to the generator
- **Template Upload**: Support for custom certificate template images
- **Data Import**: Support for both CSV and Excel files
- **Custom Fonts**: Multiple font options for certificate text
  - Dancing Script
  - Great Vibes
  - Pacifico
  - Allura
  - Satisfy
- **Customizable Font Size**: Adjust text size as needed
- **Bulk Generation**: Generate multiple certificates at once
- **ZIP Download**: Receive all certificates in a convenient ZIP file
- **Position Editor**: Visual tool to set text positions on certificates

## Project Structure

```
certificateGenarator1/
├── app.py                 # Main Flask application
├── static/
│   ├── css/
│   │   └── style.css     # Main stylesheet
│   ├── js/
│   │   └── script.js     # JavaScript for position editor
│   ├── fonts/            # Custom font files
│   └── generated/        # Temporary folder for certificate generation
└── templates/
    ├── home.html         # Login page
    └── index.html        # Main generator interface
```

## Requirements

- Python 3.x
- Flask
- Pillow (PIL)
- pandas
- openpyxl (for Excel file support)

Install dependencies using:
```bash
pip install flask pillow pandas openpyxl
```

## Setup and Running

1. Clone the repository or download the source code
2. Install the required dependencies
3. Run the Flask application:
   ```bash
   python app.py
   ```
4. Access the application at `http://127.0.0.1:5000`
5. Use the password "kuce&t" to access the generator

## Usage Guide

### 1. Accessing the Generator
- Open the application URL in your browser
- Enter the password "kuce&t" on the home page
- Click Submit to access the generator

### 2. Preparing Your Files

#### Certificate Template
- Prepare your certificate template as an image file (JPG, PNG)
- Ensure the template has space for dynamic text (names, dates, etc.)
- Recommended resolution: 1000x700 pixels

#### Data File
- Prepare your data in Excel (.xlsx, .xls) or CSV format
- Include columns for all dynamic text (names, dates, titles, etc.)
- Example data format:
  ```csv
  name,date,achievement
  John Doe,2024-03-15,Excellence in Programming
  Jane Smith,2024-03-15,Outstanding Performance
  ```

### 3. Generating Certificates

1. **Upload Template**
   - Click "Choose File" in the template section
   - Select your certificate template image

2. **Upload Data**
   - Click "Choose File" in the data file section
   - Select your Excel or CSV file

3. **Configure Text Settings**
   - Select desired font from the dropdown
   - Set appropriate font size

4. **Position Text Fields**
   - Use the Position Placeholders section to set text locations
   - Upload your template background
   - Add fields and position them as needed
   - Save the layout when satisfied

5. **Generate Certificates**
   - Click "Generate Certificates"
   - Wait for processing
   - Download the ZIP file containing all certificates

## Error Handling

Common errors and solutions:

1. **"Missing data file or template"**
   - Ensure both template and data files are uploaded

2. **"Unsupported file format"**
   - Check if your data file is in CSV or Excel format
   - Verify template is an image file

3. **"Invalid password"**
   - Double-check the password: kuce&t

## Technical Details

### Backend (app.py)
- Built with Flask
- Uses Pillow for image processing
- Pandas for data file handling
- Supports multiple file formats
- Implements secure password protection
- Generates certificates in memory to avoid storage issues

### Frontend
- Clean, responsive interface
- Canvas-based position editor
- Real-time preview capabilities
- Supports drag-and-drop positioning
- Built-in font previews

## Security Features

- Password-protected access
- Temporary file handling
- Secure file upload validation
- No permanent storage of generated certificates

## Best Practices

1. **Template Preparation**
   - Use high-resolution images
   - Leave adequate space for text
   - Test with different text lengths

2. **Data File Organization**
   - Use clear column headers
   - Verify data formatting
   - Keep file size reasonable

3. **Text Positioning**
   - Test with longest expected text
   - Verify alignment and spacing
   - Save layout for consistent results

## Limitations

- Maximum file size: Determined by server configuration
- Supported file formats: CSV, XLSX, XLS for data; JPG, PNG for templates
- Processing time increases with number of certificates
- Font selection limited to pre-installed options

## Future Enhancements

Potential improvements that could be added:

1. Additional font options
2. QR code generation
3. Template preview feature
4. Custom text colors
5. Multiple text alignments
6. Batch processing status
7. Certificate verification system

## Support

For issues or questions:
1. Verify file formats and sizes
2. Check error messages
3. Ensure all required fields are filled
4. Contact system administrator for persistent issues 