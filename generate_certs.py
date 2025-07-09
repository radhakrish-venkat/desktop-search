#!/usr/bin/env python3
"""
Generate self-signed SSL certificates for development
"""

import os
import subprocess
import sys
from pathlib import Path

def generate_self_signed_cert():
    """Generate self-signed SSL certificate for development"""
    
    # Create certs directory
    certs_dir = Path("certs")
    certs_dir.mkdir(exist_ok=True)
    
    key_file = certs_dir / "key.pem"
    cert_file = certs_dir / "cert.pem"
    
    print("🔐 Generating self-signed SSL certificates...")
    
    # Check if OpenSSL is available
    try:
        subprocess.run(["openssl", "version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ OpenSSL not found. Please install OpenSSL first:")
        print("   Ubuntu/Debian: sudo apt-get install openssl")
        print("   macOS: brew install openssl")
        print("   Windows: Download from https://slproweb.com/products/Win32OpenSSL.html")
        sys.exit(1)
    
    # Generate private key
    print("📝 Generating private key...")
    subprocess.run([
        "openssl", "genrsa", "-out", str(key_file), "2048"
    ], check=True)
    
    # Generate certificate
    print("📜 Generating certificate...")
    subprocess.run([
        "openssl", "req", "-new", "-x509", "-key", str(key_file),
        "-out", str(cert_file), "-days", "365", "-subj",
        "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    ], check=True)
    
    # Set proper permissions
    os.chmod(key_file, 0o600)
    os.chmod(cert_file, 0o644)
    
    print("✅ SSL certificates generated successfully!")
    print(f"   Key file: {key_file}")
    print(f"   Cert file: {cert_file}")
    print("\n⚠️  Note: These are self-signed certificates for development only.")
    print("   For production, use certificates from a trusted CA.")
    
    return key_file, cert_file

def generate_production_cert_instructions():
    """Print instructions for production certificates"""
    print("\n🌐 For Production HTTPS Setup:")
    print("=" * 50)
    print("1. Get SSL certificates from a trusted CA:")
    print("   - Let's Encrypt (free): https://letsencrypt.org/")
    print("   - Cloudflare (free): https://cloudflare.com/")
    print("   - Your hosting provider")
    print()
    print("2. Place certificates in the 'certs' directory:")
    print("   - certs/key.pem (private key)")
    print("   - certs/cert.pem (certificate)")
    print()
    print("3. Set proper permissions:")
    print("   chmod 600 certs/key.pem")
    print("   chmod 644 certs/cert.pem")
    print()
    print("4. Update environment variables:")
    print("   export SSL_KEY_FILE=./certs/key.pem")
    print("   export SSL_CERT_FILE=./certs/cert.pem")

if __name__ == "__main__":
    try:
        key_file, cert_file = generate_self_signed_cert()
        generate_production_cert_instructions()
        
        print(f"\n🚀 To start the server with HTTPS:")
        print(f"   uvicorn api.main:app --ssl-keyfile {key_file} --ssl-certfile {cert_file}")
        print(f"   Or use: python start_https.py")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error generating certificates: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1) 