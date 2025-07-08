import os
import io
import json
import tempfile
import logging
from typing import Optional, List, Dict, Any, Generator
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Google Drive API scopes - read-only access
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

# Check for Google Drive API availability
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
    from googleapiclient.http import MediaIoBaseDownload
    GOOGLE_DRIVE_AVAILABLE = True
except ImportError:
    GOOGLE_DRIVE_AVAILABLE = False
    logger.warning("Google Drive API dependencies not available")

class SecureTokenStorage:
    """Secure storage for Google Drive authentication tokens."""
    
    def __init__(self):
        self.key = self._get_or_create_key()
        self.cipher = self._create_cipher()
    
    def _get_or_create_key(self) -> bytes:
        """Get or create encryption key using system keyring."""
        try:
            import keyring
            key = keyring.get_password("desktop-search", "encryption_key")
            if not key:
                # Generate new key
                import base64
                from cryptography.fernet import Fernet
                key = base64.urlsafe_b64encode(Fernet.generate_key()).decode()
                keyring.set_password("desktop-search", "encryption_key", key)
            return key.encode()
        except ImportError:
            # Fallback to file-based key storage if keyring not available
            logger.warning("keyring not available, using file-based key storage")
            return self._get_or_create_file_key()
    
    def _get_or_create_file_key(self) -> bytes:
        """Fallback key storage in file."""
        key_file = os.path.join(os.path.expanduser('~'), '.config', 'desktop-search', '.key')
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            import base64
            from cryptography.fernet import Fernet
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def _create_cipher(self):
        """Create encryption cipher."""
        try:
            from cryptography.fernet import Fernet
            return Fernet(self.key)
        except ImportError:
            logger.warning("cryptography not available, using plain text storage")
            return None
    
    def save_token(self, token_data: str, filepath: str) -> bool:
        """Save encrypted token to file."""
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if self.cipher:
                encrypted_data = self.cipher.encrypt(token_data.encode())
                with open(filepath, 'wb') as f:
                    f.write(encrypted_data)
            else:
                # Fallback to plain text if encryption not available
                with open(filepath, 'w') as f:
                    f.write(token_data)
            
            # Set restrictive permissions
            os.chmod(filepath, 0o600)
            return True
        except Exception as e:
            logger.error(f"Error saving token: {e}")
            return False
    
    def load_token(self, filepath: str) -> Optional[str]:
        """Load and decrypt token from file."""
        try:
            if not os.path.exists(filepath):
                return None
            
            if self.cipher:
                with open(filepath, 'rb') as f:
                    encrypted_data = f.read()
                return self.cipher.decrypt(encrypted_data).decode()
            else:
                # Fallback to plain text if encryption not available
                with open(filepath, 'r') as f:
                    return f.read()
        except Exception as e:
            logger.error(f"Error loading token: {e}")
            return None

class GoogleDriveClient:
    """
    Client for interacting with Google Drive API with secure token storage.
    """
    
    def __init__(self, credentials_path: Optional[str] = None, token_path: Optional[str] = None):
        """
        Initialize Google Drive client.
        
        Args:
            credentials_path: Path to credentials.json file
            token_path: Path to store authentication token
        """
        if not GOOGLE_DRIVE_AVAILABLE:
            raise RuntimeError("Google Drive API dependencies not available")
        
        self.credentials_path = credentials_path or os.path.join(os.path.expanduser('~'), '.config', 'desktop-search', 'credentials.json')
        self.token_path = token_path or os.path.join(os.path.expanduser('~'), '.config', 'desktop-search', 'token.json')
        self.service = None
        self.token_storage = SecureTokenStorage()
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Drive API using secure token storage."""
        creds = None
        
        # Try to load existing token
        if os.path.exists(self.token_path):
            try:
                token_data = self.token_storage.load_token(self.token_path)
                if token_data:
                    creds = Credentials.from_authorized_user_info(json.loads(token_data), SCOPES)
            except Exception as e:
                logger.warning(f"Error loading existing token: {e}")
        
        # If no valid credentials available, let the user log in
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.warning(f"Error refreshing token: {e}")
                    creds = None
            
            if not creds:
                if not os.path.exists(self.credentials_path):
                    raise FileNotFoundError(
                        f"Credentials file not found at {self.credentials_path}. "
                        "Please download credentials.json from Google Cloud Console "
                        "and place it in the specified location."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, SCOPES)
                creds = flow.run_local_server(port=0)
            
            # Save the credentials securely
            self.token_storage.save_token(creds.to_json(), self.token_path)
        
        self.service = build('drive', 'v3', credentials=creds)
        logger.info("Successfully authenticated with Google Drive API")
    
    def list_files(self, folder_id: Optional[str] = None, query: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List files from Google Drive.
        
        Args:
            folder_id: ID of the folder to list files from (None for root)
            query: Additional query string to filter files
            
        Returns:
            List of file metadata dictionaries
        """
        if not self.service:
            raise RuntimeError("Not authenticated with Google Drive API")
        
        try:
            # Build the query
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            else:
                query_parts.append("'root' in parents")
            
            # Only include files (not folders) and exclude trashed files
            query_parts.append("mimeType != 'application/vnd.google-apps.folder'")
            query_parts.append("trashed = false")
            
            if query:
                query_parts.append(query)
            
            full_query = " and ".join(query_parts)
            
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=full_query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)',
                    pageToken=page_token
                ).execute()
                
                results.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                
                if page_token is None:
                    break
            
            logger.info(f"Found {len(results)} files in Google Drive")
            return results
            
        except HttpError as error:
            logger.error(f"Error listing files: {error}")
            return []
    
    def download_file(self, file_id: str, destination_path: Optional[str] = None) -> Optional[str]:
        """
        Download a file from Google Drive.
        
        Args:
            file_id: ID of the file to download
            destination_path: Path to save the file (None for temporary file)
            
        Returns:
            Path to the downloaded file, or None if download failed
        """
        if not self.service:
            raise RuntimeError("Not authenticated with Google Drive API")
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            file_name = file_metadata.get('name', 'unknown_file')
            mime_type = file_metadata.get('mimeType', '')
            
            # Determine destination path
            if destination_path:
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                final_path = destination_path
            else:
                # Create temporary file
                temp_dir = tempfile.mkdtemp(prefix='desktop_search_gdrive_')
                final_path = os.path.join(temp_dir, file_name)
            
            # Download the file
            request = self.service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                if status:
                    logger.debug(f"Download {int(status.progress() * 100)}%")
            
            # Save to file
            with open(final_path, 'wb') as f:
                f.write(fh.getvalue())
            
            logger.info(f"Downloaded file: {file_name} to {final_path}")
            return final_path
            
        except HttpError as error:
            logger.error(f"Error downloading file {file_id}: {error}")
            return None
    
    def get_file_content(self, file_id: str) -> Optional[str]:
        """
        Get the text content of a file directly (for Google Docs, etc.).
        
        Args:
            file_id: ID of the file to get content from
            
        Returns:
            Text content of the file, or None if failed
        """
        if not self.service:
            raise RuntimeError("Not authenticated with Google Drive API")
        
        try:
            # Get file metadata
            file_metadata = self.service.files().get(fileId=file_id).execute()
            mime_type = file_metadata.get('mimeType', '')
            
            # Handle Google Docs
            if mime_type == 'application/vnd.google-apps.document':
                return self._get_google_doc_content(file_id)
            elif mime_type == 'application/vnd.google-apps.spreadsheet':
                return self._get_google_sheet_content(file_id)
            elif mime_type == 'application/vnd.google-apps.presentation':
                return self._get_google_presentation_content(file_id)
            else:
                # For other files, download and extract text
                temp_path = self.download_file(file_id)
                if temp_path:
                    try:
                        from pkg.file_parsers.parsers import get_text_from_file
                        content, _ = get_text_from_file(temp_path)
                        # Clean up temporary file
                        os.remove(temp_path)
                        os.rmdir(os.path.dirname(temp_path))
                        return content
                    except Exception as e:
                        logger.error(f"Error extracting text from downloaded file: {e}")
                        return None
                return None
                
        except HttpError as error:
            logger.error(f"Error getting file content {file_id}: {error}")
            return None
    
    def _get_google_doc_content(self, file_id: str) -> Optional[str]:
        """Get content from Google Docs."""
        try:
            # Export as plain text
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return fh.getvalue().decode('utf-8')
            
        except HttpError as error:
            logger.error(f"Error getting Google Doc content: {error}")
            return None
    
    def _get_google_sheet_content(self, file_id: str) -> Optional[str]:
        """Get content from Google Sheets."""
        try:
            # Export as CSV
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='text/csv'
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return fh.getvalue().decode('utf-8')
            
        except HttpError as error:
            logger.error(f"Error getting Google Sheet content: {error}")
            return None
    
    def _get_google_presentation_content(self, file_id: str) -> Optional[str]:
        """Get content from Google Presentations."""
        try:
            # Export as plain text
            request = self.service.files().export_media(
                fileId=file_id,
                mimeType='text/plain'
            )
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            
            done = False
            while done is False:
                status, done = downloader.next_chunk()
            
            return fh.getvalue().decode('utf-8')
            
        except HttpError as error:
            logger.error(f"Error getting Google Presentation content: {error}")
            return None
    
    def search_files(self, query: str, folder_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Search for files in Google Drive.
        
        Args:
            query: Search query string
            folder_id: ID of the folder to search in (None for all)
            
        Returns:
            List of matching file metadata dictionaries
        """
        if not self.service:
            raise RuntimeError("Not authenticated with Google Drive API")
        
        try:
            # Build the query
            query_parts = []
            
            if folder_id:
                query_parts.append(f"'{folder_id}' in parents")
            else:
                query_parts.append("'root' in parents")
            
            # Add search terms
            query_parts.append(f"fullText contains '{query}'")
            query_parts.append("trashed = false")
            
            full_query = " and ".join(query_parts)
            
            results = []
            page_token = None
            
            while True:
                response = self.service.files().list(
                    q=full_query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, modifiedTime, parents)',
                    pageToken=page_token
                ).execute()
                
                results.extend(response.get('files', []))
                page_token = response.get('nextPageToken', None)
                
                if page_token is None:
                    break
            
            logger.info(f"Found {len(results)} files matching query: {query}")
            return results
            
        except HttpError as error:
            logger.error(f"Error searching files: {error}")
            return []


def setup_google_drive_credentials(credentials_path: str) -> bool:
    """
    Set up Google Drive credentials by copying the credentials file to the default location.
    
    Args:
        credentials_path: Path to the credentials.json file
        
    Returns:
        True if setup was successful, False otherwise
    """
    try:
        default_credentials_path = os.path.join(os.path.expanduser('~'), '.config', 'desktop-search', 'credentials.json')
        os.makedirs(os.path.dirname(default_credentials_path), exist_ok=True)
        
        import shutil
        shutil.copy2(credentials_path, default_credentials_path)
        
        logger.info(f"Credentials copied to {default_credentials_path}")
        return True
        
    except Exception as e:
        logger.error(f"Error setting up credentials: {e}")
        return False


def get_google_drive_files(folder_id: Optional[str] = None, query: Optional[str] = None) -> Generator[Dict[str, Any], None, None]:
    """
    Generator function to get files from Google Drive.
    
    Args:
        folder_id: ID of the folder to list files from (None for root)
        query: Additional query string to filter files
        
    Yields:
        File metadata dictionaries
    """
    if not GOOGLE_DRIVE_AVAILABLE:
        logger.error("Google Drive API not available")
        return
    
    try:
        client = GoogleDriveClient()
        files = client.list_files(folder_id=folder_id, query=query)
        
        for file_info in files:
            yield file_info
            
    except Exception as e:
        logger.error(f"Error accessing Google Drive: {e}")
        return 