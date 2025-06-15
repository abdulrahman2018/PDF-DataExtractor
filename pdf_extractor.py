import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime
from pdf2image import convert_from_path
import pytesseract
from PIL import Image, ImageEnhance
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self):
        self.data = []
        # Configure Tesseract for better handwritten text recognition
        self.tesseract_config = '--oem 1 --psm 6 -l eng+fra+deu+spa+ita'
        
    def clean_text(self, text):
        """Clean extracted text by removing extra whitespace and normalizing."""
        if not text:
            return ""
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        return text

    def extract_fields(self, text):
        """Extract structured fields from text."""
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Basic field extraction
            if line.startswith("Name:"):
                self.data.append({"Section": "Name", "Detail": line.replace("Name:", "").strip()})
            elif line.startswith("Date of Birth:"):
                self.data.append({"Section": "Date of Birth", "Detail": line.replace("Date of Birth:", "").strip()})
            elif line.startswith("Email:"):
                self.data.append({"Section": "Email", "Detail": line.replace("Email:", "").strip()})
            elif line.startswith("Skill") or "Python" in line or "JavaScript" in line:
                self.data.append({"Section": "Skill", "Detail": line.strip()})
            elif line.startswith("Project") or "Chatbot" in line:
                self.data.append({"Section": "Project", "Detail": line.strip()})
            elif line.startswith("Certification") or "Certified" in line:
                self.data.append({"Section": "Certification", "Detail": line.strip()})
            elif "Phone:" in line:
                self.data.append({"Section": "Phone", "Detail": line.replace("Phone:", "").strip()})
            elif "Address:" in line:
                self.data.append({"Section": "Address", "Detail": line.replace("Address:", "").strip()})

            # Advanced field extraction
            # Extract dates in various formats
            date = self.extract_date(line)
            if date:
                self.data.append({"Section": "Date", "Detail": date})

            # Extract monetary amounts
            amount = self.extract_amount(line)
            if amount:
                self.data.append({"Section": "Amount", "Detail": amount})

            # Extract names
            name = self.extract_name(line)
            if name:
                self.data.append({"Section": "Name", "Detail": name})

    def extract_date(self, text):
        """Extract dates in various formats."""
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',  # DD/MM/YYYY
            r'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
            r'\d{4}/\d{2}/\d{2}',  # YYYY/MM/DD
            r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4}',  # DD MMM YYYY
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                try:
                    date_str = matches[0]
                    if '/' in date_str or '-' in date_str:
                        if len(date_str.split('/')[0]) == 4:  # YYYY/MM/DD
                            date = datetime.strptime(date_str, '%Y/%m/%d')
                        else:  # DD/MM/YYYY
                            date = datetime.strptime(date_str, '%d/%m/%Y')
                    else:
                        date = datetime.strptime(date_str, '%d %b %Y')
                    return date.strftime('%d/%m/%Y')
                except ValueError:
                    continue
        return None

    def extract_amount(self, text):
        """Extract monetary amounts."""
        amount_patterns = [
            r'\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # Standard currency format
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*\$',   # Currency after amount
            r'USD\s*\d{1,3}(?:,\d{3})*(?:\.\d{2})?',  # USD prefix
            r'\d{1,3}(?:,\d{3})*(?:\.\d{2})?\s*USD',  # USD suffix
        ]
        
        for pattern in amount_patterns:
            matches = re.findall(pattern, text)
            if matches:
                amount = matches[0].replace('$', '').replace('USD', '').strip()
                try:
                    amount_float = float(amount.replace(',', ''))
                    return f"${amount_float:,.2f}"
                except ValueError:
                    continue
        return None

    def extract_name(self, text):
        """Extract full names."""
        name_patterns = [
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+',  # Standard name format
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)',  # Multiple name parts
            r'[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[A-Z][a-z]+)(?:\s+[A-Z][a-z]+)*',  # Complex names
        ]
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text)
            if matches:
                name = matches[0].strip()
                name = re.sub(r'\b(?:Mr|Mrs|Ms|Dr|Prof|Sir|Madam)\b', '', name, flags=re.IGNORECASE)
                name = re.sub(r'\s+', ' ', name).strip()
                if len(name.split()) >= 2:
                    return name
        return None

    def process_text_based_pdf(self, pdf_path):
        """Process text-based PDFs."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text = self.clean_text(text)
                        self.extract_fields(text)
        except Exception as e:
            logger.error(f"Error processing text-based PDF {pdf_path}: {str(e)}")
            raise

    def process_image_based_pdf(self, pdf_path):
        """Process image-based PDFs with OCR."""
        try:
            images = convert_from_path(pdf_path, dpi=300)
            
            for image in images:
                # Preprocess image
                image = image.convert('L')
                enhancer = ImageEnhance.Contrast(image)
                image = enhancer.enhance(2.0)
                
                # Perform OCR
                text = pytesseract.image_to_string(
                    image,
                    config=self.tesseract_config
                )
                
                if text:
                    text = self.clean_text(text)
                    self.extract_fields(text)
        except Exception as e:
            logger.error(f"Error processing image-based PDF {pdf_path}: {str(e)}")
            raise

    def process_pdf(self, pdf_path):
        """Process PDF and determine if it's text-based or image-based."""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                
                if text and len(text.strip()) > 100:
                    self.process_text_based_pdf(pdf_path)
                else:
                    self.process_image_based_pdf(pdf_path)
        except Exception as e:
            logger.error(f"Error processing PDF {pdf_path}: {str(e)}")
            raise

    def process_directory(self, directory_path):
        """Process all PDF files in a directory."""
        for filename in os.listdir(directory_path):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(directory_path, filename)
                try:
                    self.process_pdf(pdf_path)
                except Exception as e:
                    logger.error(f"Error processing {filename}: {str(e)}")
                    continue

    def save_to_excel(self, output_path):
        """Save extracted data to Excel with improved formatting."""
        if not self.data:
            logger.warning("No data to save")
            return
            
        try:
            df = pd.DataFrame(self.data)
            
            # Create Excel writer
            with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Extracted Data')
                
                # Get the worksheet
                worksheet = writer.sheets['Extracted Data']
                
                # Auto-adjust column widths
                for idx, col in enumerate(df.columns):
                    max_length = max(
                        df[col].astype(str).apply(len).max(),
                        len(col)
                    )
                    worksheet.column_dimensions[chr(65 + idx)].width = max_length + 2
                
                # Add filters
                worksheet.auto_filter.ref = worksheet.dimensions
                
            logger.info(f"Data saved to {output_path}")
        except Exception as e:
            logger.error(f"Error saving to Excel: {str(e)}")
            raise

def main():
    # Get the current directory
    current_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_dir = os.path.join(current_dir, 'pdfs')
    
    # Create pdfs directory if it doesn't exist
    os.makedirs(pdf_dir, exist_ok=True)
    
    # Create output directory if it doesn't exist
    output_dir = os.path.join(current_dir, 'outputs')
    os.makedirs(output_dir, exist_ok=True)
    
    # Set output file path
    output_file = os.path.join(output_dir, 'extracted_data.xlsx')
    
    print(f"Looking for PDFs in: {pdf_dir}")
    print(f"Output will be saved to: {output_file}")
    
    # Initialize and run the extractor
    extractor = PDFExtractor()
    extractor.process_directory(pdf_dir)
    extractor.save_to_excel(output_file)
    
    print("Processing complete!")

if __name__ == '__main__':
    main() 