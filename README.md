# PDF Data Extractor

Extract structured data (names, dates, amounts, and more) from PDF files and export to Excel. Supports both text-based and image-based PDFs, with a modern web frontend and standalone batch script.

---

## Features
- **Extracts:** Names, dates, amounts, emails, phone numbers, addresses, skills, projects, certifications, and more
- **Supports:**
  - Text-based PDFs (using pdfplumber)
  - Image-based PDFs (using OCR: pytesseract + pdf2image)
- **Batch processing:** Process all PDFs in a directory
- **Web frontend:** Upload PDFs and download Excel results via a modern UI
- **Excel output:** Auto-formatted, filterable, and easy to analyze
- **Error handling:** Robust logging and graceful error messages

---

## Requirements
- Python 3.8+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (for image-based PDFs)
- All Python dependencies in `requirements.txt`

---

## Setup

1. **Clone the repository** (or copy the files to your project directory):
   ```bash
   git clone <your-repo-url>
   cd <your-repo>
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Tesseract OCR:**
   - **macOS:**
     ```bash
     brew install tesseract
     ```
   - **Ubuntu:**
     ```bash
     sudo apt-get install tesseract-ocr
     ```
   - **Windows:**
     Download and install from [here](https://github.com/tesseract-ocr/tesseract/wiki)

---

## Usage

### 1. **Standalone Batch Script**

- Place your PDF files in the `pdfs/` directory (create it if it doesn't exist).
- Run the script:
  ```bash
  python3 pdf_extractor.py
  ```
- Output will be saved to `outputs/extracted_data.xlsx`.

### 2. **Web Frontend (Flask App)**

- Start the Flask app:
  ```bash
  python3 app.py
  ```
- Open your browser and go to [http://127.0.0.1:5000](http://127.0.0.1:5000)
- Upload one or more PDF files using the web interface
- Download the extracted Excel file when processing is complete

---

## Project Structure
```
/your-project/
│
├── app.py                # Flask web app
├── pdf_extractor.py      # PDF extraction logic (standalone & backend)
├── requirements.txt      # Python dependencies
├── README.md             # This file
├── /templates/
│   └── index.html        # Frontend HTML
├── /static/
│   ├── style.css         # Frontend CSS
│   ├── script.js         # Frontend JS
│   └── (icons, etc.)
├── /uploads/             # Temporary upload storage (web)
├── /outputs/             # Excel output files
├── /pdfs/                # Batch input for standalone script
└── venv/                 # Python virtual environment
```

---

## Customization
- **Extraction rules:** Edit `extract_fields` in `pdf_extractor.py` to add or change what is extracted.
- **Output format:** Edit `save_to_excel` in `pdf_extractor.py` for custom Excel formatting.
- **Frontend:** Edit files in `/templates/` and `/static/` for UI changes.

---

## Troubleshooting
- **No data to save:** Make sure your PDFs are in the correct folder and contain extractable data.
- **ModuleNotFoundError:** Activate your virtual environment and install dependencies.
- **Tesseract errors:** Ensure Tesseract is installed and available in your system PATH.

---

## License
MIT (or your preferred license) 