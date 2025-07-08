import logging
import re
import os
from typing import Optional, Union

class SanitizedFormatter(logging.Formatter):
    """
    Log formatter that sanitizes sensitive information from log messages.
    """
    
    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt, datefmt)
        
        # Patterns for sensitive information
        self.sensitive_patterns = [
            # Home directories
            r'/home/[^/\s]+',
            r'/Users/[^/\s]+', 
            r'C:\\Users\\[^\\\s]+',
            r'C:/Users/[^/\s]+',
            
            # Configuration directories
            r'~/.config/[^/\s]+',
            r'~/.ssh/[^/\s]+',
            
            # File paths with sensitive names
            r'[^/\s]*password[^/\s]*',
            r'[^/\s]*secret[^/\s]*',
            r'[^/\s]*token[^/\s]*',
            r'[^/\s]*key[^/\s]*',
            r'[^/\s]*credential[^/\s]*',
            
            # Email addresses
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            
            # API keys (common patterns)
            r'[A-Za-z0-9]{32,}',  # Long alphanumeric strings
            r'sk-[A-Za-z0-9]{20,}',  # OpenAI-style keys
            r'ghp_[A-Za-z0-9]{36}',  # GitHub tokens
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.sensitive_patterns]
    
    def format(self, record):
        """Format log record with sensitive information redacted."""
        # Get the original message
        message = super().format(record)
        
        # Redact sensitive information
        for pattern in self.compiled_patterns:
            message = pattern.sub('[REDACTED]', message)
        
        return message

class SecureLogger:
    """
    Secure logger that prevents sensitive information from being logged.
    """
    
    def __init__(self, name: str, level: int = logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Remove existing handlers to avoid duplicates
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Add sanitized formatter
        handler = logging.StreamHandler()
        handler.setFormatter(SanitizedFormatter(
            fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message with sanitization."""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message with sanitization."""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message with sanitization."""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message with sanitization."""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message with sanitization."""
        self.logger.critical(message, *args, **kwargs)
    
    def get_logger(self) -> logging.Logger:
        """Get the underlying logger for compatibility."""
        return self.logger

def setup_secure_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up secure logging for a module.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level
        
    Returns:
        Configured secure logger (standard logging.Logger with sanitized formatter)
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Add sanitized formatter
    handler = logging.StreamHandler()
    handler.setFormatter(SanitizedFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)
    
    return logger

def sanitize_path(path: str) -> str:
    """
    Sanitize a file path for logging.
    
    Args:
        path: File path to sanitize
        
    Returns:
        Sanitized path with sensitive parts redacted
    """
    if not path:
        return path
    
    # Redact home directory
    home = os.path.expanduser('~')
    if path.startswith(home):
        path = path.replace(home, '~', 1)
    
    # Redact sensitive directory names
    sensitive_dirs = ['password', 'secret', 'token', 'key', 'credential', 'ssh']
    for sensitive_dir in sensitive_dirs:
        if sensitive_dir in path.lower():
            # Replace the sensitive part with [REDACTED]
            pattern = re.compile(re.escape(sensitive_dir), re.IGNORECASE)
            path = pattern.sub('[REDACTED]', path)
    
    return path

def log_file_operation(operation: str, filepath: str, logger: Optional[Union[logging.Logger, SecureLogger]] = None):
    """
    Log file operations with sanitized paths.
    
    Args:
        operation: Operation being performed (e.g., 'reading', 'writing')
        filepath: Path to the file
        logger: Logger to use (creates one if None)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    elif isinstance(logger, SecureLogger):
        logger = logger.get_logger()
    
    sanitized_path = sanitize_path(filepath)
    logger.info(f"{operation.capitalize()} file: {sanitized_path}")

def log_error_with_context(error: Exception, context: str = "", logger: Optional[Union[logging.Logger, SecureLogger]] = None):
    """
    Log errors with context but without sensitive information.
    
    Args:
        error: Exception that occurred
        context: Additional context about the error
        logger: Logger to use (creates one if None)
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    elif isinstance(logger, SecureLogger):
        logger = logger.get_logger()
    
    # Sanitize the context before logging
    sanitized_context = sanitize_path(context)
    error_msg = f"Error in {sanitized_context}: {type(error).__name__}: {str(error)}"
    logger.error(error_msg) 