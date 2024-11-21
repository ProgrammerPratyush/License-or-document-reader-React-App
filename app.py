from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from PIL import Image
from flask_cors import CORS
import pytesseract
import os
import re

# Flask app initialization
app = Flask(__name__)

# Enable CORS for your app
CORS(app)

# Set up the Tesseract executable path (update if necessary for your system)
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'  # Adjust for Windows

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///documents.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy and Migrate
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Create a model for storing document data
class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    document_number = db.Column(db.String(50), nullable=False)
    issue_date = db.Column(db.String(20), nullable=True)
    expiration_date = db.Column(db.String(20), nullable=True)

# Define upload route
@app.route('/upload', methods=['POST'])
def upload_document():
    if 'document' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400
    
    file = request.files['document']
    file_path = os.path.join("uploads", file.filename)
    file.save(file_path)
    
    # Perform OCR
    extracted_text = extract_text_from_image(file_path)
    
    # Parse key information
    data = parse_document(extracted_text)

    # Save parsed data to database
    new_document = Document(
        name=data.get("Name", "Unknown"),
        document_number=data.get("Document Number", "Unknown"),
        issue_date=data.get("Issue Date"),
        expiration_date=data.get("Expiration Date")
    )
    db.session.add(new_document)
    db.session.commit()

    return jsonify(data)

# Preprocess the image (convert to grayscale and apply thresholding)
def preprocess_image(image_path):
    img = Image.open(image_path)
    # Convert to grayscale
    gray_img = img.convert('L')
    # Apply thresholding to get better text contrast
    threshold_img = gray_img.point(lambda p: p > 128 and 255)  # Binarization
    return threshold_img

# Extract text from image
def extract_text_from_image(image_path):
    processed_img = preprocess_image(image_path)
    text = pytesseract.image_to_string(processed_img)
    return text

# Improved parsing with regex to extract the details
def parse_document(text):
    data = {}
    
    # Updated patterns for matching fields
    document_number_pattern = r"DL\s*(\d)"
    expiration_date_pattern = r"EXP\s*(\d{2}/\d{2}/\d{4})"
    dob_pattern = r"DOB\s*(.*)"
    issue_date_pattern = r"ISS\s*(\d{2}/\d{2}/\d{4})"
    name_pattern = r"FN\s*(.*)"
    sex_pattern = r"SEX\s*(\w)"
    height_pattern = r"HGT\s*(\d+'-\d+\"|\d+\'\s*\d+\"|\d{1,2}-\d{2}|\d+\")"  # Matches height patterns
    weight_pattern = r"WGT\s*(\d+ lb)"
    hair_color_pattern = r"HAIR\s*(\w+)"
    eyes_color_pattern = r"EYES\s*(\w+)"
    address_pattern = r"(\d{1,5}\s[\w\s]+(?:\s[A-Za-z]+){1,3}\s*\d{5})"  # Matches street address format like '2570 24TH STREET ANYTOWN, CA 95818'
    rstr_pattern = r"RSTR\s*(\w+)"  # Matches the "RSTR" field
    
    # Use regex to match the fields
    document_number_match = re.search(document_number_pattern, text)
    expiration_date_match = re.search(expiration_date_pattern, text)
    dob_match = re.search(dob_pattern, text)
    issue_date_match = re.search(issue_date_pattern, text)
    name_match = re.search(name_pattern, text)
    sex_match = re.search(sex_pattern, text)
    height_match = re.search(height_pattern, text)
    weight_match = re.search(weight_pattern, text)
    hair_color_match = re.search(hair_color_pattern, text)
    eyes_color_match = re.search(eyes_color_pattern, text)
    address_match = re.search(address_pattern, text)
    rstr_match = re.search(rstr_pattern, text)

    # Populate the data dictionary with extracted information
    if document_number_match:
        data["Document Number"] = document_number_match.group(1).strip()
    if expiration_date_match:
        data["Expiration Date"] = expiration_date_match.group(1).strip()
    if dob_match:
        data["Date of Birth"] = dob_match.group(1).strip()
    if issue_date_match:
        data["Issue Date"] = issue_date_match.group(1).strip()
    if name_match:
        data["Name"] = name_match.group(1).strip()
    if sex_match:
        data["Sex"] = sex_match.group(1).strip()
    if height_match:
        data["Height"] = height_match.group(1).strip()
    if weight_match:
        data["Weight"] = weight_match.group(1).strip()
    if hair_color_match:
        data["Hair Color"] = hair_color_match.group(1).strip()
    if eyes_color_match:
        data["Eyes Color"] = eyes_color_match.group(1).strip()
    if address_match:
        data["Address"] = address_match.group(0).strip()  # Capture the full address
    if rstr_match:
        data["RSTR"] = rstr_match.group(1).strip()

    # Handle missing fields with default values, like "NONE" for RSTR
    if "RSTR" not in data:
        data["RSTR"] = "NONE"
    
    return data

if __name__ == '__main__':
    # Create uploads folder if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    # Run the Flask app
    app.run(debug=True)
