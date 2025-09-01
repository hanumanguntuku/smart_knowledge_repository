"""
Data validation and normalization module
"""
import re
import hashlib
try:
    import langdetect
    LANGDETECT_AVAILABLE = True
except ImportError:
    LANGDETECT_AVAILABLE = False
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from urllib.parse import urlparse
from datetime import datetime
import logging


@dataclass
class ValidationResult:
    """Result of data validation"""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_data: Optional[Dict] = None


class DataValidator:
    """Data validator for document processing"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.min_content_length = 50
        self.max_content_length = 1000000  # 1MB
        self.supported_languages = ['en', 'es', 'fr', 'de', 'it', 'pt']
    
    def validate_document(self, data: Dict) -> ValidationResult:
        """Comprehensive document validation"""
        errors = []
        warnings = []
        normalized_data = data.copy()
        
        try:
            # URL validation
            url_result = self._validate_url(data.get('url', ''))
            if not url_result[0]:
                errors.append(f"Invalid URL: {url_result[1]}")
            
            # Title validation
            title_result = self._validate_title(data.get('title', ''))
            if not title_result[0]:
                errors.extend(title_result[1])
            else:
                normalized_data['title'] = title_result[2]
            
            # Content validation
            content_result = self._validate_content(data.get('content', ''))
            if not content_result[0]:
                errors.extend(content_result[1])
            else:
                normalized_data['content'] = content_result[2]
                # Add computed fields
                normalized_data.update(self._compute_content_metrics(content_result[2]))
            
            # Metadata validation
            metadata = data.get('metadata', {})
            if not isinstance(metadata, dict):
                warnings.append("Invalid metadata format, using empty dict")
                metadata = {}
            normalized_data['metadata'] = metadata
            
            # Add derived fields
            normalized_data.update(self._compute_derived_fields(normalized_data))
            
        except Exception as e:
            errors.append(f"Validation error: {str(e)}")
            self.logger.error(f"Validation failed: {e}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized_data if len(errors) == 0 else None
        )
    
    def _validate_url(self, url: str) -> Tuple[bool, str]:
        """Validate URL format"""
        if not url or not isinstance(url, str):
            return False, "URL is required and must be a string"
        
        try:
            parsed = urlparse(url.strip())
            if not all([parsed.scheme, parsed.netloc]):
                return False, "Invalid URL format"
            if parsed.scheme not in ['http', 'https']:
                return False, "Only HTTP/HTTPS URLs are allowed"
            return True, ""
        except Exception as e:
            return False, f"URL parsing error: {str(e)}"
    
    def _validate_title(self, title: str) -> Tuple[bool, List[str], str]:
        """Validate and normalize title"""
        errors = []
        
        if not title or not isinstance(title, str):
            errors.append("Title is required and must be a string")
            return False, errors, ""
        
        # Normalize title
        normalized_title = self._normalize_text(title.strip())
        
        if len(normalized_title) < 3:
            errors.append("Title must be at least 3 characters long")
        
        if len(normalized_title) > 200:
            errors.append("Title must be less than 200 characters")
        
        return len(errors) == 0, errors, normalized_title
    
    def _validate_content(self, content: str) -> Tuple[bool, List[str], str]:
        """Validate and normalize content"""
        errors = []
        
        if not content or not isinstance(content, str):
            errors.append("Content is required and must be a string")
            return False, errors, ""
        
        # Normalize content
        normalized_content = self._normalize_text(content)
        
        if len(normalized_content) < self.min_content_length:
            errors.append(f"Content too short (minimum {self.min_content_length} characters)")
        
        if len(normalized_content) > self.max_content_length:
            errors.append(f"Content too large (maximum {self.max_content_length} characters)")
        
        return len(errors) == 0, errors, normalized_content
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text content"""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove control characters
        text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
        # Normalize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        return text.strip()
    
    def _compute_content_metrics(self, content: str) -> Dict:
        """Compute content metrics"""
        words = content.split()
        return {
            'word_count': len(words),
            'char_count': len(content),
            'reading_time_minutes': max(1, len(words) // 200)
        }
    
    def _compute_derived_fields(self, data: Dict) -> Dict:
        """Compute additional derived fields"""
        content = data.get('content', '')
        url = data.get('url', '')
        
        # Generate content hash for duplicate detection
        content_hash = hashlib.sha256(content.encode('utf-8')).hexdigest()
        
        # Extract domain
        domain = urlparse(url).netloc if url else 'unknown'
        
        # Detect language
        language = self._detect_language(content)
        
        # Determine content type
        content_type = self._classify_content_type(data)
        
        return {
            'content_hash': content_hash,
            'domain': domain,
            'language': language,
            'content_type': content_type,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'status': 'active'
        }
    
    def _detect_language(self, content: str) -> str:
        """Detect content language"""
        try:
            if not LANGDETECT_AVAILABLE:
                return 'en'  # Default to English if langdetect not available
                
            if len(content.strip()) < 20:
                return 'en'  # Default to English for short content
            
            detected_lang = langdetect.detect(content)
            return detected_lang if detected_lang in self.supported_languages else 'en'
        except:
            return 'en'  # Default to English on detection failure
    
    def _classify_content_type(self, data: Dict) -> str:
        """Classify content type based on URL and content"""
        url = data.get('url', '').lower()
        content = data.get('content', '').lower()
        
        if any(ext in url for ext in ['.pdf', 'pdf']):
            return 'pdf'
        elif any(ext in url for ext in ['.doc', '.docx', 'word']):
            return 'document'
        elif 'wikipedia' in url:
            return 'encyclopedia'
        elif any(indicator in content for indicator in ['abstract:', 'keywords:', 'doi:']):
            return 'research_paper'
        elif any(indicator in content for indicator in ['tutorial', 'how to', 'step by step']):
            return 'tutorial'
        else:
            return 'web_page'
