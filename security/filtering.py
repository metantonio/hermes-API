"""
Hermes Web Data API - Security Filtering Layer
==============================================
Comprehensive security filtering to prevent credential/key leakage.
"""

import re
import json
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

# ============================================================================
# Security Alert Levels
# ============================================================================

class AlertLevel(Enum):
    """Security alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class SecurityAlert:
    """Security alert structure"""
    timestamp: str
    alert_type: str
    level: str
    message: str
    details: Optional[Dict[str, Any]] = None
    request_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging/serialization"""
        return asdict(self)


@dataclass
class SanitizationResult:
    """Result of sanitization process"""
    original_length: int
    sanitized_length: int
    alerts_generated: int
    credentials_found: List[str]
    dangerous_urls_found: List[str]
    pii_found: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_length": self.original_length,
            "sanitized_length": self.sanitized_length,
            "alerts_generated": self.alerts_generated,
            "credentials_found": self.credentials_found,
            "dangerous_urls_found": self.dangerous_urls_found,
            "pii_found": self.pii_found,
        }


# ============================================================================
# Security Alert Registry
# ============================================================================

class SecurityAlertRegistry:
    """
    Registry for security alerts and events.
    
    Tracks all security-related events during data extraction.
    """
    
    def __init__(self):
        self.alerts: List[SecurityAlert] = []
        self.alert_counts: Dict[str, int] = {}
        self.alert_thresholds: Dict[str, int] = {
            "credential_detected": 1,  # Alert on first occurrence
            "dangerous_url": 3,       # Alert after 3 occurrences
            "pii_detected": 1,        # Alert on first occurrence
            "rate_limit_exceeded": 1,  # Alert on first occurrence
        }
    
    def record_alert(
        self,
        alert_type: str,
        level: str = AlertLevel.INFO.value,
        message: str = "",
        details: Optional[Dict] = None,
        request_id: Optional[str] = None
    ) -> SecurityAlert:
        """
        Record a security alert.
        
        Returns the alert object for logging.
        """
        alert = SecurityAlert(
            timestamp=datetime.now(timezone.utc).isoformat(),
            alert_type=alert_type,
            level=level,
            message=message,
            details=details,
            request_id=request_id
        )
        
        self.alerts.append(alert)
        
        # Track counts
        current_count = self.alert_counts.get(alert_type, 0)
        new_count = current_count + 1
        
        # Check thresholds
        threshold = self.alert_thresholds.get(alert_type, float("inf"))
        if new_count >= threshold:
            # Critical threshold exceeded
            logging.warning(
                f"Security Alert Threshold Exceeded: {alert_type}",
                extra={
                    "alert_type": alert_type,
                    "count": new_count,
                    "threshold": threshold,
                    "request_id": request_id,
                }
            )
        
        self.alert_counts[alert_type] = new_count
        
        return alert
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all alerts"""
        return {
            "total_alerts": len(self.alerts),
            "alert_counts": dict(self.alert_counts),
            "alert_types": list(set(a.alert_type for a in self.alerts)),
            "critical_alerts": len([
                a for a in self.alerts if a.level == AlertLevel.CRITICAL.value
            ]),
            "error_alerts": len([
                a for a in self.alerts if a.level == AlertLevel.ERROR.value
            ]),
        }


# ============================================================================
# Main Security Filter
# ============================================================================

class SecurityFilter:
    """
    Main security filter for data extraction.
    
    Filters and sanitizes data to prevent:
    - API keys and tokens leakage
    - Credentials (passwords, usernames)
    - Private keys
    - Financial data
    - Personal identifiable information (PII)
    - Dangerous URLs and malware links
    """
    
    def __init__(
        self,
        alert_registry: Optional[SecurityAlertRegistry] = None,
        strict_mode: bool = True,
        log_level: str = "INFO"
    ):
        self.alert_registry = alert_registry or SecurityAlertRegistry()
        self.strict_mode = strict_mode
        self.log_level = log_level
        
        # Initialize logging
        self._setup_logging()
        
        # Compile regex patterns for performance
        self._compile_patterns()
        
        # Statistics
        self.stats: Dict[str, int] = {
            "total_processed": 0,
            "sanitized_count": 0,
            "alerts_generated": 0,
            "credentials_removed": 0,
        }
    
    def _setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=getattr(logging, self.log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
    
    def _compile_patterns(self):
        """Compile regex patterns for performance"""
        self.patterns: Dict[str, re.Pattern] = {}
        
        # API Keys
        for pattern_str in ["api_keys", "credentials", "private_keys", "financial", "dangerous"]:
            pattern_str_list = {
                "api_keys": [
                    r'(?i)(api[_-]?key|apikey|access[_-]?key|secret[_-]?key|token|auth[_-]?token)\s*[=:]\s*["\']?([^"\'\s]+)',
                    r'(?i)(sk_live|sk_test|pk_live|pk_test|ghp_)[-\w]+',
                    r'(?i)(aws[_-]?access[_-]?key|aws[_-]?secret)',
                    r'(?i)xox[a-z-]+-[a-z0-9]+',
                    r'(?i)hubspot_access[_-]?token',
                    r'(?i)microsoft[_-]?access[_-]?token',
                    r'(?i)google[_-]?api[_-]?key',
                ],
                "credentials": [
                    r'(?i)(username|user|admin|root)\s*[=:]\s*["\']?\w+["\']?',
                    r'(?i)password\s*[=:]\s*["\']?\w+',
                    r'(?i)passwd\s*[=:]\s*["\']?\w+',
                    r'(?i)secret\s*[=:]\s*["\']?\w+',
                    r'(?i)credential\s*[=:]\s*["\']?\w+',
                    r'(?i)access[_-]?key\s*[=:]\s*["\']?\w+',
                    r'(?i)private[_-]?key\s*[=:]\s*["\']?\w+',
                    r'(?i)api[_-]?secret\s*[=:]\s*["\']?\w+',
                ],
                "private_keys": [
                    r'-----BEGIN (RSA |DSA |EC )?PRIVATE KEY-----',
                    r'-----BEGIN EC PRIVATE KEY-----',
                    r'-----BEGIN PRIVATE KEY-----',
                    r'-----BEGIN PUBLIC KEY-----',
                    r'-----BEGIN CERTIFICATE-----',
                ],
                "financial": [
                    r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
                    r'\b\d{16,19}\b',
                    r'(?i)(credit[_-]?card|account[_-]?number|cvv)\s*[=:]\s*["\']?\d+',
                    r'(?i)(iban)\s*[=:]\s*["\']?[A-Z0-9]+',
                ],
                "dangerous": [
                    r'https?://[-\w]+\.exe[-\w\.]*',
                    r'https?://[-\w]+\.sh[-\w\.]*',
                    r'https?://[-\w]+\.py[-\w\.]*',
                    r'https?://[-\w]+\.bat[-\w\.]*',
                    r'https?://[-\w]+\.cmd[-\w\.]*',
                    r'(?i)file://',
                    r'(?i)mongodb://',
                    r'(?i)postgres://',
                    r'(?i)mysql://',
                    r'(?i)mssql://',
                ],
            }
            
            # Compile each pattern
            for pattern_str in pattern_str_list:
                self.patterns[pattern_str] = [
                    re.compile(p) for p in pattern_str_list[pattern_str]
                ]
        
        # PII patterns
        self.pii_patterns: Dict[str, re.Pattern] = {
            "email": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
            "phone": re.compile(r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b'),
            "ssn": re.compile(r'\b\d{3}-?\d{2}-?\d{4}\b'),
            "date": re.compile(
                r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{2,4}\b',
                re.IGNORECASE
            ),
        }
    
    def filter_content(
        self,
        content: str,
        context: str = "unknown",
        max_length: int = 100000
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """
        Filter and sanitize content.
        
        Returns:
            - Sanitized content
            - List of alerts generated
        """
        if not content:
            return "", []
        
        # Truncate if too long
        if len(content) > max_length:
            logging.warning(
                f"Content truncated from {len(content)} to {max_length} chars",
                extra={
                    "context": context,
                    "original_length": len(content),
                    "max_length": max_length,
                }
            )
            content = content[:max_length]
        
        alerts: List[Dict[str, Any]] = []
        original_length = len(content)
        
        # 1. Check for API keys
        alerts.extend(self._check_api_keys(content, alerts, context))
        
        # 2. Check for credentials
        alerts.extend(self._check_credentials(content, alerts, context))
        
        # 3. Check for private keys
        alerts.extend(self._check_private_keys(content, alerts, context))
        
        # 4. Check for financial data
        alerts.extend(self._check_financial(content, alerts, context))
        
        # 5. Check for dangerous URLs
        alerts.extend(self._check_dangerous_urls(content, alerts, context))
        
        # 6. Check for PII
        alerts.extend(self._check_pii(content, alerts, context))
        
        # Apply filters
        filtered_content = content
        
        # Apply API key filter
        for pattern in self.patterns["api_keys"]:
            filtered_content = re.sub(pattern, "[REDACTED_API_KEY]", filtered_content)
        
        # Apply credentials filter
        for pattern in self.patterns["credentials"]:
            filtered_content = re.sub(pattern, "[REDACTED_CREDENTIAL]", filtered_content)
        
        # Apply private keys filter
        for pattern in self.patterns["private_keys"]:
            filtered_content = re.sub(pattern, "[REDACTED_PRIVATE_KEY]", filtered_content)
        
        # Apply financial filter
        for pattern in self.patterns["financial"]:
            filtered_content = re.sub(pattern, "[REDACTED_FINANCIAL]", filtered_content)
        
        # Apply dangerous URL filter
        for pattern in self.patterns["dangerous"]:
            filtered_content = re.sub(pattern, "[DANGEROUS_URL_REDACTED]", filtered_content)
        
        # Apply PII filter
        filtered_content = self._filter_pii(filtered_content, alerts)
        
        # Generate alerts
        self._generate_alerts(alerts, original_length, filtered_content, context)
        
        # Update stats
        self.stats["total_processed"] += 1
        if alerts:
            self.stats["sanitized_count"] += 1
            self.stats["alerts_generated"] += len(alerts)
            self.stats["credentials_removed"] += sum(
                1 for a in alerts if a["type"] in ["credential", "api_key"]
            )
        
        return filtered_content, alerts
    
    def _check_api_keys(
        self,
        content: str,
        alerts: List[Dict],
        context: str
    ) -> List[Dict]:
        """Check for API keys and tokens"""
        found = []
        
        for i, pattern in enumerate(self.patterns["api_keys"]):
            matches = pattern.findall(content)
            if matches:
                found.append({
                    "type": "api_key",
                    "pattern_index": i,
                    "count": len(matches),
                    "context": context,
                })
                
                # Generate alerts
                for match in matches:
                    if isinstance(match, tuple):
                        # Group match: (key_name, key_value)
                        key_name, key_value = match[:2]
                        alert = {
                            "type": "API_KEY_DETECTED",
                            "message": f"API key detected: {key_name}",
                            "level": AlertLevel.ERROR.value,
                            "details": {
                                "key_name": str(key_name)[:50],
                                "count": len(matches),
                                "context": context,
                            },
                        }
                        alerts.append(alert)
        
        return found if found else []
    
    def _check_credentials(
        self,
        content: str,
        alerts: List[Dict],
        context: str
    ) -> List[Dict]:
        """Check for credentials"""
        found = []
        
        for i, pattern in enumerate(self.patterns["credentials"]):
            matches = pattern.findall(content)
            if matches:
                found.append({
                    "type": "credential",
                    "pattern_index": i,
                    "count": len(matches),
                    "context": context,
                })
                
                for match in matches:
                    alert = {
                        "type": "CREDENTIAL_DETECTED",
                        "message": f"Credential detected",
                        "level": AlertLevel.ERROR.value,
                        "details": {
                            "context": context,
                            "count": len(matches),
                        },
                    }
                    alerts.append(alert)
        
        return found if found else []
    
    def _check_private_keys(
        self,
        content: str,
        alerts: List[Dict],
        context: str
    ) -> List[Dict]:
        """Check for private keys"""
        found = []
        
        for i, pattern in enumerate(self.patterns["private_keys"]):
            if pattern.search(content):
                found.append({
                    "type": "private_key",
                    "pattern_index": i,
                    "context": context,
                })
                
                alert = {
                    "type": "PRIVATE_KEY_DETECTED",
                    "message": "Private key detected",
                    "level": AlertLevel.ERROR.value,
                    "details": {
                        "context": context,
                    },
                }
                alerts.append(alert)
        
        return found if found else []
    
    def _check_financial(
        self,
        content: str,
        alerts: List[Dict],
        context: str
    ) -> List[Dict]:
        """Check for financial data"""
        found = []
        
        for i, pattern in enumerate(self.patterns["financial"]):
            matches = pattern.findall(content)
            if matches:
                found.append({
                    "type": "financial",
                    "pattern_index": i,
                    "count": len(matches),
                    "context": context,
                })
                
                alert = {
                    "type": "FINANCIAL_DATA_DETECTED",
                    "message": "Financial data detected",
                    "level": AlertLevel.WARNING.value,
                    "details": {
                        "context": context,
                        "count": len(matches),
                    },
                }
                alerts.append(alert)
        
        return found if found else []
    
    def _check_dangerous_urls(
        self,
        content: str,
        alerts: List[Dict],
        context: str
    ) -> List[Dict]:
        """Check for dangerous URLs"""
        found = []
        
        for i, pattern in enumerate(self.patterns["dangerous"]):
            matches = pattern.findall(content)
            if matches:
                found.append({
                    "type": "dangerous_url",
                    "pattern_index": i,
                    "count": len(matches),
                    "context": context,
                })
                
                alert = {
                    "type": "DANGEROUS_URL_DETECTED",
                    "message": "Dangerous URL detected",
                    "level": AlertLevel.WARNING.value,
                    "details": {
                        "context": context,
                        "count": len(matches),
                    },
                }
                alerts.append(alert)
        
        return found if found else []
    
    def _check_pii(
        self,
        content: str,
        alerts: List[Dict],
        context: str
    ) -> List[Dict]:
        """Check for PII"""
        found = []
        
        pii_types = [
            ("email", self.pii_patterns["email"]),
            ("phone", self.pii_patterns["phone"]),
            ("ssn", self.pii_patterns["ssn"]),
            ("date", self.pii_patterns["date"]),
        ]
        
        for pii_type, pattern in pii_types:
            matches = pattern.findall(content)
            if matches:
                found.append({
                    "type": "pii",
                    "pii_type": pii_type,
                    "count": len(matches),
                    "context": context,
                })
                
                alert = {
                    "type": f"PII_{pii_type.upper()}_DETECTED",
                    "message": f"PII detected: {pii_type}",
                    "level": AlertLevel.WARNING.value,
                    "details": {
                        "pii_type": pii_type,
                        "count": len(matches),
                        "context": context,
                    },
                }
                alerts.append(alert)
        
        return found if found else []
    
    def _filter_pii(
        self,
        content: str,
        alerts: List[Dict]
    ) -> str:
        """Filter PII from content"""
        # Email addresses
        content = self.pii_patterns["email"].sub("[EMAIL_REDACTED]", content)
        
        # Phone numbers
        content = self.pii_patterns["phone"].sub("[PHONE_REDACTED]", content)
        
        # SSN
        content = self.pii_patterns["ssn"].sub("[SSN_REDACTED]", content)
        
        # Dates
        content = self.pii_patterns["date"].sub("[DATE_REDACTED]", content)
        
        return content
    
    def _generate_alerts(
        self,
        alerts: List[Dict],
        original_length: int,
        filtered_content: str,
        context: str
    ):
        """Generate and log alerts"""
        if not alerts:
            return
        
        # Log summary
        alert_summary = {
            "context": context,
            "total_alerts": len(alerts),
            "types": list(set(a["type"] for a in alerts)),
            "original_length": original_length,
            "filtered_length": len(filtered_content),
        }
        
        logging.info(
            f"Security Filter Applied: {alert_summary}",
            extra={
                "context": context,
                "alerts": json.dumps(alert_summary),
            }
        )
        
        # Send to external alert system if configured
        # self._send_to_alert_system(alerts)
    
    def _send_to_alert_system(self, alerts: List[Dict]):
        """Send alerts to external monitoring system"""
        try:
            import requests
            url = os.getenv("SECURITY_ALERT_URL", "")
            if not url:
                return
            
            payload = {
                "alerts": alerts,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            
            response = requests.post(
                url,
                data=json.dumps(payload),
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            
            if response.status_code != 200:
                logging.warning(f"Alert system error: {response.status_code}")
        except Exception:
            # Don't fail the main request
            pass


# ============================================================================
# Security Filter Registry
# ============================================================================

def create_security_filter(
    alert_registry: Optional[SecurityAlertRegistry] = None,
    strict_mode: bool = True,
    log_level: str = "INFO"
) -> SecurityFilter:
    """
    Factory function to create a security filter.
    
    Args:
        alert_registry: Optional registry for security alerts
        strict_mode: Enable strict security checking
        log_level: Logging level
    
    Returns:
        Configured SecurityFilter instance
    """
    return SecurityFilter(
        alert_registry=alert_registry,
        strict_mode=strict_mode,
        log_level=log_level
    )


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == "__main__":
    # Demo usage
    print("Security Filter Module Loaded")
    print("=" * 60)
    
    # Create a filter
    filter = create_security_filter()
    
    # Test filtering
    test_content = """
    API key: sk_live_abc123xyz
    Password: secret123
    Credit card: 1234-5678-9012-3456
    Email: user@example.com
    Dangerous URL: https://malware.com/payload.exe
    """
    
    print("\nOriginal content:")
    print(test_content)
    
    print("\n" + "-" * 60)
    
    # Filter content
    filtered, alerts = filter.filter_content(test_content, "test")
    
    print("\nFiltered content:")
    print(filtered)
    
    print("\n" + "-" * 60)
    
    print("\nAlerts generated:")
    for alert in alerts:
        print(f"  - {alert['type']}: {alert['message']}")


# ============================================================================
# CredentialFilter - Main filtering class for Hermes Web Data API
# ============================================================================

class CredentialFilter:
    """
    Main credential filter class for Hermes Web Data API.
    
    This class provides the main filtering functionality for detecting
    and sanitizing credentials, API keys, and other sensitive data.
    """

    def __init__(self, settings=None):
        """
        Initialize CredentialFilter.
        
        Args:
            settings: Optional settings object with configuration.
        """
        self.settings = settings
        self.alert_registry = SecurityAlertRegistry()
        self.security_filter = SecurityFilter()
        self.data_extractor = DataExtractor()
        self.filter_string = lambda s, context="": s  # Add filter method as lambda function that accepts context

    def get_settings(self):
        """
        Get the current settings.
        
        Returns:
            Settings object or None if not configured.
        """
        return self.settings

    def filter_content(self, content: str, context: str = "unknown") -> tuple:
        """
        Filter and sanitize content using all configured filters.
        
        Args:
            content: Input content to filter
            context: Context information for logging
            
        Returns:
            Tuple of (filtered_content, alerts)
        """
        if not content:
            return "", []
        
        filtered_content, alerts = self.security_filter.filter_content(
            content, context
        )
        
        # Apply data extraction filtering
        if self.data_extractor:
            extracted_data, extract_alerts = self.data_extractor.extract_data(
                filtered_content, context
            )
            alerts.extend(extract_alerts)
        
        return filtered_content, alerts

    def detect_credentials(self, content: str) -> list:
        """
        Detect credentials in the given content.
        
        Args:
            content: Content to scan for credentials
            
        Returns:
            List of detected credentials with details
        """
        alerts, _ = self.filter_content(content, context="credential_scan")
        return [
            a for a in alerts 
            if a.get("type") in ["CREDENTIAL_DETECTED", "API_KEY_DETECTED"]
        ]

    def get_alert_summary(self) -> dict:
        """
        Get a summary of all security alerts.
        
        Returns:
            Dictionary with alert summary statistics
        """
        return self.alert_registry.get_summary()

    def reset_alerts(self):
        """Reset all stored alerts."""
        self.alert_registry.alerts.clear()
        self.alert_registry.alert_counts.clear()


class DataExtractor:
    """
    Data extractor for finding and classifying data in content.
    
    Extracts and classifies different types of data such as:
    - URLs and domains
    - Email addresses
    - Phone numbers
    - Dates and times
    - Financial data
    """

    def __init__(self):
        """Initialize the data extractor."""
        self.patterns = {
            "urls": [
                re.compile(r'https?://[^\s]+', re.IGNORECASE),
                re.compile(r'ftp://[^\s]+', re.IGNORECASE),
            ],
            "emails": re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', re.IGNORECASE),
            "phones": re.compile(r'\b\d{3}[\s.-]?\d{3}[\s.-]?\d{4}\b'),
            "dates": re.compile(
                r'\b(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+\d{1,2},?\s+\d{2,4}\b',
                re.IGNORECASE
            ),
        }
    
    def extract_data(self, content: str, context: str = "unknown") -> tuple:
        """
        Extract and classify data from content.
        
        Args:
            content: Content to extract data from
            context: Context for logging
            
        Returns:
            Tuple of (extracted_data, alerts)
        """
        alerts = []
        extracted = {}
        
        # Extract URLs
        for pattern in self.patterns["urls"]:
            matches = pattern.findall(content)
            if matches:
                extracted["urls"] = extracted.get("urls", []) + list(matches)
                
                for url in matches:
                    if "malware" in url.lower() or "virus" in url.lower():
                        alerts.append({
                            "type": "MALWARE_URL",
                            "url": url[:100],
                            "level": AlertLevel.WARNING.value
                        })
        
        # Extract emails
        emails = self.patterns["emails"].findall(content)
        if emails:
            extracted["emails"] = emails
            for email in emails:
                # Check if email is suspicious
                if "spam" in email.lower() or "fake" in email.lower():
                    alerts.append({
                        "type": "SUSPICIOUS_EMAIL",
                        "email": email[:100],
                        "level": AlertLevel.INFO.value
                    })
        
        # Extract phone numbers
        phones = self.patterns["phones"].findall(content)
        if phones:
            extracted["phones"] = phones
        
        return extracted, alerts