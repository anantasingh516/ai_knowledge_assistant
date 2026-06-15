import re
class ComplianceSanitizer:
    def __init__(self):
        self.email_regex = re.compile(r'[\w\.-]+@[\w\.-]+\.\w+')
        self.phone_regex = re.compile(r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b')
        self.id_regex = re.compile(r'\b(?:SRM|ID|REG|EMP)-\d{4,8}\b|\b[A-Z]{2}\d{4,6}\b', re.IGNORECASE)

    def sanitize_text(self, text: str) -> str:
        """Scans and redacts matching patterns to maintain compliance boundaries."""
        if not text:
            return text
        
        text = self.email_regex.sub("[REDACTED_EMAIL]", text)
        text = self.phone_regex.sub("[REDACTED_PHONE]", text)
        text = self.id_regex.sub("[REDACTED_ID]", text)
        
        return text