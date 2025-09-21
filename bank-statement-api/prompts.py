"""
Prompt configuration file for bank statement processing API
This file contains all prompts used in the application for better maintainability
"""

from typing import List

class BankStatementPrompts:
    """Contains all prompts for bank statement processing"""
    
    @staticmethod
    def get_data_extraction_prompt(user_columns: List[str], json_example: str, html_content: str) -> str:
        """
        Main data extraction prompt for processing bank statement pages
        
        Args:
            user_columns: List of user-defined column names
            json_example: Example JSON format for the expected output
            html_content: HTML content extracted from OCR
            
        Returns:
            Formatted prompt string
        """
        return f"""
You are a strict data extractor for bank statements.

You are provided:
1. An OCR-extracted HTML table of a bank statement page.
2. The image of that page (to correct OCR errors).
3. A fixed schema with column names: {user_columns}

CORE INSTRUCTIONS:
- Extract ONLY actual **transaction rows** from the HTML table.
- If the HTML is incomplete or missing data, use the image to recover the transaction rows.
- If the HTML table has incorrect row-column alignment or malformed structure, cross-check and correct it using the image.
- Use the image **only if the HTML format is empty, broken or misleading**.
- Map the data from HTML table columns to the user-specified columns as accurately as possible.
- If a user column doesn't have corresponding data in the HTML, use empty string ("") or null.

OUTPUT REQUIREMENTS:
- Return the result as a **strict JSON array**, where each element is a JSON object with keys exactly matching: {user_columns}
- Do NOT return a single dictionary with column names – you must return a list of dictionaries (one per transaction).
- Each row must contain meaningful transaction data – avoid filler values like column names or placeholder dashes.
- If there are **no valid transaction rows on the page, return exactly this: `[]` – just an empty array**, not a dictionary or object with keys like `"transactions"`.
- Do NOT wrap the output inside another object. The output must be a raw JSON array only.
- Do NOT hallucinate or invent data.
- Do NOT return explanations, comments, or non-JSON text – just a clean JSON array.

CRITICAL FORMATTING RULES:
- The response **must be a JSON list**.
- Each list item **must be a dictionary** with exactly the keys: {user_columns}
- Do NOT return newlines, boilerplate, or extra metadata.
- Ensure all column names in the output exactly match the provided schema.

DATA MAPPING GUIDELINES:
- Date columns: Extract in the format present in the statement (DD/MM/YYYY, DD-MM-YYYY, etc.)
- Amount columns: Extract numeric values only, remove currency symbols
- Description/Narration: Include full transaction description
- Reference numbers: Include cheque numbers, reference numbers as they appear
- Balance: Extract the running balance amount

Expected Output Format:
{json_example}

HTML page content:
{html_content}
"""

    @staticmethod
    def get_column_validation_prompt() -> str:
        """Prompt for validating column names"""
        return """
Please ensure your column names follow these guidelines:
- Use clear, descriptive names
- Common column types include: Date, Transaction Date, Description, Narration, Particulars, 
  Debit, Credit, Withdrawal, Deposit, Balance, Cheque Number, Reference Number
- Avoid special characters except periods, hyphens, and parentheses
- Use consistent naming convention across all columns
"""

    @staticmethod
    def get_error_recovery_prompt(error_details: str) -> str:
        """Prompt for error recovery scenarios"""
        return f"""
An error occurred during processing: {error_details}

Please check:
1. PDF file is not corrupted or password-protected
2. Column names are properly formatted as a JSON array
3. PDF contains actual bank statement data with tables
4. Network connection is stable for API calls

If the error persists, try with a different PDF file or adjust column names.
"""

    @staticmethod
    def get_preprocessing_instructions() -> str:
        """Instructions for data preprocessing"""
        return """
Data Preprocessing Guidelines:
1. Remove HTML break tags and clean formatting
2. Strip LaTeX math expressions that may interfere with table parsing
3. Normalize whitespace and special characters
4. Preserve table structure during markdown to HTML conversion
5. Maintain data integrity during column mapping
"""

# Example usage and column suggestions for different banks
SUGGESTED_BANK_COLUMNS = {
    "AXIS_BANK": ["Tran Date", "Chq No", "Particulars", "Debit", "Credit", "Balance", "Init. Br"],
    "AU_BANK": ["Date", "Description/Narration", "Value date", "Chq./Ref. No.", "Debit(Dr.)", "Credit(Cr.)", "Balance"],
    "BOB_BANK": ["Serial No", "Transaction Date", "Value Date", "Description", "Cheque Number", "Debit", "Credit", "Balance"],
    "BOI_BANK": ["Transaction Date", "Instrument Id", "Narration", "Debit", "Credit", "Balance"],
    "CENTRAL_BANK": ["Value Date", "Post Date", "Details", "Chq.No.", "Debit", "Credit", "Balance"],
    "HDFC_BANK": ["Date", "Narration", "Chq./Ref.No.", "Value Dt", "Withdrawal Amt.", "Deposit Amt.", "Closing Balance"],
    "ICICI_BANK": ["Date", "Description", "Amount", "Type"],
    "INDUSLND_BANK": ["DATE", "PARTICULARS", "CHQ.NO.", "WITHDRAWALS", "DEPOSITS", "BALANCE"],
    "SBI_BANK": ["Txn Date", "Value Date", "Description", "Ref No./Cheque No.", "Debit", "Credit", "Balance"],
    "GENERIC": ["Date", "Description", "Debit", "Credit", "Balance"]
}

def get_column_suggestions(bank_name: str = None) -> List[str]:
    """
    Get column suggestions for a specific bank or generic format
    
    Args:
        bank_name: Name of the bank (optional)
        
    Returns:
        List of suggested column names
    """
    if bank_name and bank_name.upper() in SUGGESTED_BANK_COLUMNS:
        return SUGGESTED_BANK_COLUMNS[bank_name.upper()]
    return SUGGESTED_BANK_COLUMNS["GENERIC"]