"""
Base Parser Class
Provides common utilities for invoice parsing
"""

import re
from abc import ABC, abstractmethod
from typing import Dict, Optional
from datetime import datetime
from dateutil.relativedelta import relativedelta


# GST State Code to State Name mapping (India)
GST_STATE_CODES = {
    "01": "Jammu & Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "25": "Daman & Diu",
    "26": "Dadra & Nagar Haveli",
    "27": "Maharashtra",
    "28": "Andhra Pradesh",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman & Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh (New)",
    "38": "Ladakh",
}


class BaseParser(ABC):
    """Base class for invoice parsers with common utility methods."""
    
    @abstractmethod
    def parse(self, text: str, filename: str) -> Dict:
        """Parse invoice text and return extracted data."""
        pass
    
    def extract_field(self, text: str, pattern: str, group: int = 1) -> Optional[str]:
        """
        Extract a field value using regex pattern.
        
        Args:
            text: Text to search in
            pattern: Regex pattern with capture group
            group: Which capture group to return (default 1)
            
        Returns:
            Extracted value or None
        """
        match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE | re.DOTALL)
        if match:
            return match.group(group).strip()
        return None
    
    def clean_amount(self, value: Optional[str]) -> str:
        """Remove commas from amount strings."""
        if value:
            return value.replace(",", "")
        return ""
    
    def format_date(self, date_str: Optional[str]) -> str:
        """
        Format date string to DD/MM/YYYY format.
        
        Args:
            date_str: Date in various formats (DD.MM.YYYY, DD-Mon-YYYY, etc.)
            
        Returns:
            Formatted date string or original if parsing fails
        """
        if not date_str:
            return ""
        
        # Try various date formats
        formats = [
            "%d.%m.%Y",      # 12.12.2025
            "%d-%m-%Y",      # 12-12-2025
            "%d/%m/%Y",      # 12/12/2025
            "%d-%b-%Y",      # 12-Dec-2025
            "%d-%B-%Y",      # 12-December-2025
            "%Y-%m-%d",      # 2025-12-12
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(date_str.strip(), fmt)
                return dt.strftime("%d/%m/%Y")
            except ValueError:
                continue
        
        # Return as-is if no format matched
        return date_str.replace(".", "/")
    
    def parse_invoice_period(self, period_str: Optional[str]) -> tuple:
        """
        Parse invoice period string into from/to dates and billing frequency.
        
        Args:
            period_str: Period string like "01.11.2025 - 30.11.2025" or "01-Aug-2025 to 31-Aug-2025"
            
        Returns:
            Tuple of (from_date, to_date, billing_frequency)
        """
        if not period_str:
            return "", "", ""
        
        # Common date separators
        separators = [" - ", " to ", "-", "–"]
        
        from_date = ""
        to_date = ""
        
        for sep in separators:
            if sep in period_str:
                parts = period_str.split(sep, 1)
                if len(parts) == 2:
                    from_date = self.format_date(parts[0].strip())
                    to_date = self.format_date(parts[1].strip())
                    break
        
        # Calculate billing frequency
        billing_frequency = self.calculate_billing_frequency(from_date, to_date)
        
        return from_date, to_date, billing_frequency
    
    def calculate_billing_frequency(self, from_date: str, to_date: str) -> str:
        """
        Calculate billing frequency based on invoice period.
        
        Args:
            from_date: Start date in DD/MM/YYYY format
            to_date: End date in DD/MM/YYYY format
            
        Returns:
            Billing frequency string (Monthly, Quarterly, etc.)
        """
        if not from_date or not to_date:
            return ""
        
        try:
            start = datetime.strptime(from_date, "%d/%m/%Y")
            end = datetime.strptime(to_date, "%d/%m/%Y")
            
            # Calculate difference in months
            rdelta = relativedelta(end, start)
            total_months = rdelta.years * 12 + rdelta.months
            
            # Add 1 because period is inclusive
            if rdelta.days > 0:
                total_months += 1
            
            if total_months <= 1:
                return "Monthly"
            elif total_months <= 3:
                return "Quarterly"
            elif total_months <= 6:
                return "Half-Yearly"
            elif total_months <= 12:
                return "Yearly"
            else:
                return f"{total_months} Months"
                
        except ValueError:
            return ""
    
    def generate_ledger_name(self, period_from: str, period_to: str) -> str:
        """
        Generate ledger name in format: "Bulk SMS Charges - Oct-25 to Dec-25"
        
        Args:
            period_from: Start date in DD/MM/YYYY format
            period_to: End date in DD/MM/YYYY format
            
        Returns:
            Formatted ledger name
        """
        if not period_from or not period_to:
            return "Bulk SMS Charges"
        
        try:
            start = datetime.strptime(period_from, "%d/%m/%Y")
            end = datetime.strptime(period_to, "%d/%m/%Y")
            
            # Format as "Oct-25 to Dec-25"
            start_str = start.strftime("%b-%y")
            end_str = end.strftime("%b-%y")
            
            return f"Bulk SMS Charges - {start_str} to {end_str}"
        except ValueError:
            return "Bulk SMS Charges"
    
    def get_state_from_gst(self, gst_number: Optional[str]) -> str:
        """
        Extract state name from GST number's first 2 digits.
        
        Args:
            gst_number: 15-character GST number (e.g., "27AABCZ7217Q1ZM")
            
        Returns:
            State name (e.g., "Maharashtra")
        """
        if not gst_number or len(gst_number) < 2:
            return ""
        
        state_code = gst_number[:2]
        return GST_STATE_CODES.get(state_code, "")
    
    def extract_gst_state(self, place_of_supply: Optional[str], gst_number: Optional[str] = None) -> str:
        """
        Extract state name from place of supply or GST number.
        
        Args:
            place_of_supply: String like "06 Haryana" or "Maharashtra,27"
            gst_number: GST number to extract state code from
            
        Returns:
            State name only (without code)
        """
        # First try to get from GST number
        if gst_number and len(gst_number) >= 2:
            state = self.get_state_from_gst(gst_number)
            if state:
                return state
        
        # Fallback to place of supply parsing
        if not place_of_supply:
            return ""
        
        # Remove state code (first 2 digits) if present
        cleaned = re.sub(r'^\d{2}\s*', '', place_of_supply.strip())
        # Remove trailing numbers/commas
        cleaned = re.sub(r'[,\s]*\d+$', '', cleaned)
        
        return cleaned.strip()
