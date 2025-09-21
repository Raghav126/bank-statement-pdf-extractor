from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import tempfile
import os
import json
import base64
import io
import time
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import markdown
from bs4 import BeautifulSoup
import re

from invoke.util import debug
from pdf2image import convert_from_path
from mistralai import Mistral, DocumentURLChunk, ImageURLChunk, TextChunk
from natsort import natsorted
from prompts import BankStatementPrompts, get_column_suggestions, SUGGESTED_BANK_COLUMNS
from config import Config

# Configure logging
logging.basicConfig(level=Config.LOG_LEVEL, format=Config.LOG_FORMAT)
logger = logging.getLogger(__name__)

app = FastAPI(title="Bank Statement PDF to CSV API", version="1.0.0")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=Config.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Mistral client
client = Mistral(api_key=Config.MISTRAL_API_KEY)



class BankStatementProcessor:
    def __init__(self):
        self.client = client
        self.prompts = BankStatementPrompts()
    
    def get_ocr_markdowns(self, pdf_bytes: bytes, filename: str) -> Dict[str, Any]:
        """Extract OCR markdown from PDF bytes"""
        try:
            # Upload PDF file to Mistral's OCR service
            uploaded_file = self.client.files.upload(
                file={
                    "file_name": filename,
                    "content": pdf_bytes,
                },
                purpose="ocr",
            )

            # Get URL for the uploaded file
            signed_url = self.client.files.get_signed_url(file_id=uploaded_file.id, expiry=1)

            # Process PDF with OCR
            pdf_response = self.client.ocr.process(
                document=DocumentURLChunk(document_url=signed_url.url),
                model=Config.MISTRAL_OCR_MODEL,
                include_image_base64=True
            )

            # Convert response to JSON format
            response_dict = json.loads(pdf_response.model_dump_json())
            return response_dict
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"OCR processing failed: {str(e)}")

    def preprocess_markdown(self, md_text: str) -> str:
        """Clean markdown text"""
        return md_text.replace("<br>", "").replace("<br/>", "").replace("<br />", "")
        # """Clean markdown text and normalize tables"""
        # md_text = md_text.replace("<br>", "").replace("<br/>", "").replace("<br />", "")
        #
        # # Ensure tables start after a blank line
        # md_text = re.sub(r"([^\n])(\|.+\|.+\|)", r"\1\n\n\2", md_text)
        #
        # return md_text


    def strip_latex_math(self, md_text: str) -> str:
        """Remove LaTeX math expressions"""
        def latex_to_text(match):
            content = match.group(1)
            content = re.sub(r"\\begin\{[a-zA-Z]+\}", "", content)
            content = re.sub(r"\\end\{[a-zA-Z]+\}", "", content)
            content = re.sub(r"\\text\s*\{\s*(.*?)\s*\}", r"\1", content)
            content = content.replace("\\\\", " ")
            content = re.sub(r"\s+", " ", content)
            return content.strip()

        return re.sub(r"\$+([^\$]+?)\$+", latex_to_text, md_text)

    def markdown_to_html(self, md_text: str) -> str:
        """Convert markdown to HTML"""
        return markdown.markdown(md_text, extensions=["markdown.extensions.tables"])

    def markdown_table_to_html(self, md_text: str) -> str:
        """Process markdown tables to HTML"""
        clean_md = self.preprocess_markdown(md_text)
        clean_md = self.strip_latex_math(clean_md)
        return self.markdown_to_html(clean_md)

    def extract_all_table_parts(self, markdown_text: str) -> List[tuple]:
        """Extract tables from markdown text"""
        html = self.markdown_table_to_html(markdown_text)
        soup = BeautifulSoup(html, "html.parser")
        tables = soup.find_all("table")

        all_tables = []
        for table in tables:
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            rows = [
                [td.get_text(strip=True) for td in tr.find_all("td")]
                for tr in table.find_all("tr")[1:]
            ]
            if headers and rows:
                all_tables.append((headers, rows))
        return all_tables

    def convert_pdf_to_images(self, pdf_path: str) -> List[Dict[str, str]]:
        """Convert PDF pages to base64-encoded images"""
        try:
            images = convert_from_path(pdf_path)
            encoded_images = []
            for img in images:
                buffered = io.BytesIO()
                img.save(buffered, format="PNG")
                encoded = base64.b64encode(buffered.getvalue()).decode("utf-8")
                encoded_images.append({
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{encoded}"
                })
            return encoded_images
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Image conversion failed: {str(e)}")

    def infer_json_type(self, col_name: str) -> str:
        """Infer JSON type from column name"""
        col = col_name.lower()
        if "date" in col:
            return "string"
        elif any(kw in col for kw in ["withdraw", "deposit", "balance", "amount", "credit", "debit"]):
            return "float"
        else:
            return "string"

    def generate_json_format(self, columns: List[str]) -> str:
        """Generate JSON format example"""
        lines = [f'    "{col}": "{self.infer_json_type(col)}"' for col in columns]
        return "[\n  {\n" + ",\n".join(lines) + "\n  },\n  ...\n]"

    def process_page_with_llm(self, html_content: str, image_data: Dict[str, str], 
                             user_columns: List[str]) -> List[Dict[str, Any]]:
        """Process a single page using LLM"""
        try:
            json_example = self.generate_json_format(user_columns)
            prompt = self.prompts.get_data_extraction_prompt(user_columns, json_example, html_content)
            
            chat_response = self.client.chat.complete(
                model=Config.MISTRAL_CHAT_MODEL,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            ImageURLChunk(image_url=image_data["image_url"]),
                            TextChunk(text=prompt),
                        ],
                    }
                ],
                response_format={"type": "json_object"},
                temperature=0
            )

            # Parse JSON response
            response_content = chat_response.choices[0].message.content
            try:
                result = json.loads(response_content)
                # Ensure it's a list
                if isinstance(result, dict):
                    # If it's wrapped in an object, try to extract the array
                    for value in result.values():
                        if isinstance(value, list):
                            return value
                    return []
                return result if isinstance(result, list) else []
            except json.JSONDecodeError:
                return []
                
        except Exception as e:
            print(f"LLM processing error: {str(e)}")
            return []

    def process_bank_statement(self, pdf_bytes: bytes, filename: str, user_columns: List[str]) -> List[Dict[str, Any]]:
        """Main processing function"""
        
        # Step 1: Get OCR markdowns
        ocr_response = self.get_ocr_markdowns(pdf_bytes, filename)
        
        # Step 2: Process markdowns to HTML tables per page
        page_html_contents = []
        current_table = {"headers": None, "rows": []}
        
        for page in ocr_response["pages"]:
            markdown_text = page["markdown"]
            all_tables_from_page = self.extract_all_table_parts(markdown_text)
            
            page_tables = []
            for headers, rows in all_tables_from_page:
                page_tables.append((headers, rows))
                
                if headers == current_table["headers"]:
                    current_table["rows"].extend(rows)
                else:
                    if current_table["headers"] and current_table["rows"]:
                        pass  # We could store combined tables here if needed
                    current_table = {"headers": headers, "rows": rows}
            
            # Generate HTML for this page
            page_html_parts = []
            for idx, (headers, rows) in enumerate(page_tables, 1):
                html = "<table>\n"
                html += "<thead><tr>" + "".join(f"<th>{h}</th>" for h in headers) + "</tr></thead>\n"
                html += "<tbody>\n"
                for row in rows:
                    html += "<tr>" + "".join(f"<td>{cell}</td>" for cell in row) + "</tr>\n"
                html += "</tbody></table>\n"
                page_html_parts.append(html)
            
            page_html_content = "\n".join(page_html_parts)
            page_html_contents.append(page_html_content)
        
        # Step 3: Convert PDF to images for LLM processing
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
            temp_pdf.write(pdf_bytes)
            temp_pdf_path = temp_pdf.name
        
        try:
            image_blocks = self.convert_pdf_to_images(temp_pdf_path)
        finally:
            os.unlink(temp_pdf_path)
        
        # Step 4: Process each page with LLM
        final_json = []
        for page_html, image_data in zip(page_html_contents, image_blocks):
            if page_html.strip():  # Only process if there's content
                page_results = self.process_page_with_llm(page_html, image_data, user_columns)
                final_json.extend(page_results)
            time.sleep(Config.API_RATE_LIMIT_DELAY)  # Rate limiting
        
        return final_json

# Initialize processor
processor = BankStatementProcessor()

@app.get("/")
async def root():
    return {"message": "Bank Statement PDF to CSV API", "version": "1.0.0"}

@app.post("/process-bank-statement")
async def start_process_bank_statement(
    file: UploadFile = File(...),
    columns: str = Form(...),  # JSON string of column names
    output_format: str = Form(default="csv")  # csv or json
):
    """
    Process bank statement PDF and return structured data
    
    Args:
        file: PDF file upload
        columns: JSON array string of column names e.g., '["Date", "Description", "Amount"]'
        output_format: Output format - 'csv' or 'json'
    
    Returns:
        Processed bank statement data in requested format
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # # Parse and validate columns
    # try:
    #     user_columns = json.loads(columns)
    #     if not isinstance(user_columns, list) or not user_columns:
    #         raise ValueError("Columns must be a non-empty list")
    #     if not all(isinstance(col, str) for col in user_columns):
    #         raise ValueError("All column names must be strings")
    # except (json.JSONDecodeError, ValueError) as e:
    #     raise HTTPException(status_code=400, detail=f"Invalid columns format: {str(e)}")

    try:
        # Parse the columns JSON string
        columns_data = json.loads(columns)

        # Extract column names from the objects
        column_names = [col["name"] for col in columns_data if "name" in col]

        # Create a mapping of column names to IDs for potential future use
        column_mapping = {col["name"]: col["id"] for col in columns_data if "name" in col and "id" in col}

    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid columns format: {str(e)}")
    
    # Validate output format
    if output_format.lower() not in ['csv', 'json']:
        raise HTTPException(status_code=400, detail="Output format must be 'csv' or 'json'")
    
    try:
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Process the PDF
        results = processor.process_bank_statement(pdf_bytes, file.filename, column_names)
        
        if not results:
            return JSONResponse(
                content={"message": "No transaction data found in the PDF", "data": []},
                status_code=200
            )
        
        # Return based on requested format
        if output_format.lower() == 'json':
            return JSONResponse(content={
                "message": "Processing completed successfully",
                "total_transactions": len(results),
                "columns": column_names,
                "data": results
            })
        
        else:  # CSV format
            # Create DataFrame and convert to CSV
            df = pd.DataFrame(results, columns=column_names)
            
            # # Create temporary CSV file
            # with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_csv:
            #     df.to_csv(temp_csv.name, index=False)
            #     temp_csv_path = temp_csv.name
            
            
            # # Return CSV file
            # return FileResponse(
            #     path=temp_csv_path,
            #     filename=f"bank_statement.csv",
            #     media_type="text/csv",
            #     background=lambda: os.unlink(temp_csv_path)  # Clean up temp file
            # )
            # Generate timestamped filename
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            csv_filename = f"bank_statement_{timestamp}.csv"
            csv_path = os.path.join(Config.OUTPUT_DIR, csv_filename)

            # Save CSV locally
            df.to_csv(csv_path, index=False, encoding="utf-8")

            # Return saved CSV file
            return FileResponse(
                path=csv_path,
                filename=csv_filename,
                media_type="text/csv"
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@app.post("/process-bank-statement-json")
async def process_bank_statement_json_only(
    file: UploadFile = File(...),
    columns: str = Form(...)  # JSON string of column names
):
    """
    Process bank statement PDF and return JSON data only
    Simplified endpoint for frontend integration
    
    Args:
        file: PDF file upload
        columns: JSON array string of column names e.g., '["Date", "Description", "Amount"]'
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")
    
    # Parse and validate columns
    # try:
    #     user_columns = json.loads(columns)
    #     if not isinstance(user_columns, list) or not user_columns:
    #         raise ValueError("Columns must be a non-empty list")
    #     if not all(isinstance(col, str) for col in user_columns):
    #         raise ValueError("All column names must be strings")
    try:
        # Parse the columns JSON string
        columns_data = json.loads(columns)

        # Extract column names from the objects
        column_names = [col["name"] for col in columns_data if "name" in col]
    except (json.JSONDecodeError, ValueError) as e:
        raise HTTPException(status_code=400, detail=f"Invalid columns format: {str(e)}")
    
    try:
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Process the PDF
        results = processor.process_bank_statement(pdf_bytes, file.filename, column_names)
        
        # return {
        #     "success": True,
        #     "message": "Processing completed successfully",
        #     "total_transactions": len(results),
        #     "columns": user_columns,
        #     "data": results
        # }
        for idx, item in enumerate(results, start=1):
            item["id"] = idx
        print(results)
        return {"transactions": results}
            
    except Exception as e:
        return {
            "success": False,
            "message": f"Processing failed: {str(e)}",
            "data": []
        }

@app.post("/validate-columns")
async def validate_columns(columns: str = Form(...)):
    """
    Validate column format before processing
    
    Args:
        columns: JSON array string of column names
    """
    try:
        user_columns = json.loads(columns)
        if not isinstance(user_columns, list) or not user_columns:
            raise ValueError("Columns must be a non-empty list")
        if not all(isinstance(col, str) for col in user_columns):
            raise ValueError("All column names must be strings")
        
        return {
            "valid": True,
            "message": "Columns format is valid",
            "columns": user_columns,
            "column_count": len(user_columns)
        }
    except (json.JSONDecodeError, ValueError) as e:
        return {
            "valid": False,
            "message": f"Invalid columns format: {str(e)}",
            "columns": [],
            "column_count": 0
        }

@app.get("/config")
async def get_config():
    """Get current API configuration (for debugging)"""
    return Config.get_summary()

# @app.get("/column-suggestions")
# async def get_column_suggestions(bank_name: Optional[str] = None):
#     """
#     Get suggested column names for different banks
    
#     Args:
#         bank_name: Optional bank name to get specific suggestions
#     """
#     if bank_name:
#         suggestions = get_column_suggestions(bank_name)
#         return {
#             "bank": bank_name.upper(),
#             "suggested_columns": suggestions
#         }
#     else:
#         return {
#             "all_bank_suggestions": SUGGESTED_BANK_COLUMNS,
#             "generic_columns": get_column_suggestions()
#         }
@app.get("/column-suggestions")
async def column_suggestions_endpoint(bank_name: Optional[str] = None):
    """
    Get suggested column names for different banks
    
    Args:
        bank_name: Optional bank name to get specific suggestions
    """
    if bank_name:
        suggestions = get_column_suggestions(bank_name)  # Now calls the actual function
        return {
            "bank": bank_name.upper(),
            "suggested_columns": suggestions
        }
    else:
        return {
            "all_bank_suggestions": SUGGESTED_BANK_COLUMNS,
            "generic_columns": get_column_suggestions()  # Now calls the actual function
        }
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "Bank Statement Processor API"}

if __name__ == "__main__":
    logger.info("Starting Bank Statement Processor API...")
    logger.info(f"Configuration: {Config.get_summary()}")
    uvicorn.run(app, host=Config.API_HOST, port=Config.API_PORT, log_level=Config.LOG_LEVEL.lower())