import re
import sqlite3
from app.db import get_users_db

class PaymentService:
    @staticmethod
    def verify_manual_code(user_uuid, mpesa_code):
        """
        Validates M-Pesa code format and checks for duplicates.
        Returns: (success: bool, message: str)
        """
        if not mpesa_code:
            return False, "Please enter a transaction code."
            
        # 1. Sanitize
        code = mpesa_code.strip().upper()

        # 2. Regex Check (10 Chars, Alphanumeric)
        # Standard M-Pesa codes are 10 chars, e.g., 'SBF23...' or 'RHE...'
        if not re.match(r'^[A-Z0-9]{10}$', code):
            return False, "Invalid Code Format. Must be 10 characters (e.g., SBF...)"

        # 3. Duplicate Check
        db = get_users_db()
        try:
            # Check if code exists
            cur = db.execute("SELECT id FROM transactions WHERE mpesa_code = ?", (code,))
            if cur.fetchone():
                return False, "This transaction code has already been used."
                
            # 4. Success - Log it (Status=PENDING by default, but explicit here)
            db.execute("INSERT INTO transactions (user_uuid, mpesa_code, status, amount) VALUES (?, ?, 'PENDING', 50)", (user_uuid, code))
            db.commit()
            
            return True, "Payment Submitted. Pending Verification."
        except sqlite3.Error as e:
            return False, f"Database error: {str(e)}"
