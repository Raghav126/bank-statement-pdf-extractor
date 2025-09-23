# Bank Statement PDF to CSV API - Setup Guide

## 📁 Project Structure
```
bank-statement-api/
├── main.py              # Main API file
├── prompts.py           # Prompt configuration
├── config.py            # Configuration management
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables (create from .env.example)
├── .env.example         # Environment variables template
└── README.md           # This file
```

## 🚀 Quick Setup

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Environment Variables
Copy `.env.example` to `.env` and update with your values:
```bash
cp .env.example .env
```

Edit `.env` file:
```bash
MISTRAL_API_KEY=your_mistral_api_key_here
API_HOST=0.0.0.0
API_PORT=8000
```

### 3. Run the API
```bash
python main.py
```

The API will be available at `http://localhost:8000`

## 📚 API Documentation

### Base URL
```
http://localhost:8000
```

### Endpoints

#### 1. **GET /** - Root endpoint
Returns API information and version.

#### 2. **GET /column-suggestions** - Get column suggestions
Get suggested column formats for different banks.

**Query Parameters:**
- `bank_name` (optional): Specific bank name

**Example:**
```bash
curl "http://localhost:8000/column-suggestions?bank_name=AXIS"
```

#### 3. **POST /validate-columns** - Validate column format
Validate column names before processing.

**Form Data:**
- `columns`: JSON string of column names

**Example:**
```bash
curl -X POST "http://localhost:8000/validate-columns" \
  -F 'columns=["Date", "Description", "Debit", "Credit", "Balance"]'
```

#### 4. **POST /process-bank-statement-json** - Process PDF (JSON Response)
Main endpoint for processing bank statements with JSON response.

**Form Data:**
- `file`: PDF file
- `columns`: JSON string of column names

**Example:**
```bash
curl -X POST "http://localhost:8000/process-bank-statement-json" \
  -F "file=@statement.pdf" \
  -F 'columns=["Date", "Description", "Debit", "Credit", "Balance"]'
```

#### 5. **POST /process-bank-statement** - Process PDF (CSV/JSON)
Process bank statement with choice of output format.

**Form Data:**
- `file`: PDF file
- `columns`: JSON string of column names
- `output_format`: "csv" or "json" (default: "csv")



## 📋 Column Format Guidelines

### Supported Column Types
The API automatically infers data types based on column names:
- **Date columns**: Any column with "date" in the name → string
- **Amount columns**: Columns with "withdraw", "deposit", "balance", "amount", "credit", "debit" → float
- **Other columns**: Default to string

### Common Column Examples
```json
// Generic format
["Date", "Description", "Debit", "Credit", "Balance"]

// Detailed format
["Transaction Date", "Value Date", "Narration", "Cheque No", "Debit Amount", "Credit Amount", "Running Balance"]

// Minimal format
["Date", "Description", "Amount", "Type"]
```

### Bank-Specific Suggestions
Use the `/column-suggestions` endpoint to get pre-configured column formats for major Indian banks.

## 🔍 API Response Format

### Success Response (JSON)
```json
{
    "success": true,
    "message": "Processing completed successfully",
    "total_transactions": 45,
    "columns": ["Date", "Description", "Debit", "Credit", "Balance"],
    "data": [
        {
            "Date": "01/01/2024",
            "Description": "ATM Withdrawal",
            "Debit": "500.00",
            "Credit": "",
            "Balance": "10500.00"
        }
    ]
}
```

### Error Response
```json
{
    "success": false,
    "message": "Processing failed: Invalid PDF format",
    "data": []
}
```

## 🛠 Development Setup

### For Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with auto-reload
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### For Production
```bash
# Use gunicorn for production
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UnicornWorker --bind 0.0.0.0:8000
```

## 🚨 Troubleshooting

### Common Issues

1. **"MISTRAL_API_KEY is required"**
   - Ensure you've set the environment variable in `.env` file
   - Get API key from Mistral AI platform

2. **"Only PDF files are supported"**
   - Ensure uploaded file has `.pdf` extension
   - Check file is not corrupted

3. **"Invalid columns format"**
   - Ensure columns are provided as valid JSON array
   - Example: `'["Date", "Description", "Amount"]'`

4. **"No transaction data found"**
   - PDF might not contain tabular data
   - Try with a different bank statement format

### Debugging Tips
- Check API logs for detailed error messages
- Use `/config` endpoint to verify configuration
- Test with `/validate-columns` before processing
- Ensure PDF contains clear tabular transaction data

## 📊 Performance Considerations

- **File Size**: Max 50MB PDF files (configurable)
- **Processing Time**: ~2-5 seconds per page depending on content
- **Rate Limiting**: 1-second delay between page processing (configurable)
- **Memory Usage**: Temporary files are automatically cleaned up

## 🔐 Security Notes

- API keys are loaded from environment variables
- Temporary files are automatically deleted after processing
- CORS origins should be configured for production use
- Consider adding authentication for production deployment
