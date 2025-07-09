# HTTPS Setup Guide

This guide covers setting up HTTPS for the Desktop Search API, including development and production configurations.

## 🔐 Quick Start (Development)

### 1. Generate Self-Signed Certificates

For development and testing, generate self-signed certificates:

```bash
python generate_certs.py
```

This creates:
- `certs/key.pem` - Private key
- `certs/cert.pem` - Self-signed certificate

### 2. Start HTTPS Server

```bash
python start_https.py
```

The server will be available at: `https://localhost:8443` (static port)

### 3. Access Web Interface

- **API Documentation**: https://localhost:8443/docs
- **Web Interface**: https://localhost:8443
- **Health Check**: https://localhost:8443/health

## 🌐 Production HTTPS Setup

### Option 1: Let's Encrypt (Free)

1. **Install Certbot**:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install certbot
   
   # macOS
   brew install certbot
   ```

2. **Get certificates**:
   ```bash
   sudo certbot certonly --standalone -d yourdomain.com
   ```

3. **Copy certificates**:
   ```bash
   sudo cp /etc/letsencrypt/live/yourdomain.com/privkey.pem ./certs/key.pem
   sudo cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem ./certs/cert.pem
   sudo chown $USER:$USER ./certs/key.pem ./certs/cert.pem
   chmod 600 ./certs/key.pem
   chmod 644 ./certs/cert.pem
   ```

4. **Set up auto-renewal**:
   ```bash
   # Add to crontab
   0 12 * * * /usr/bin/certbot renew --quiet && cp /etc/letsencrypt/live/yourdomain.com/privkey.pem /path/to/your/app/certs/key.pem && cp /etc/letsencrypt/live/yourdomain.com/fullchain.pem /path/to/your/app/certs/cert.pem
   ```

### Option 2: Cloudflare (Free)

1. **Set up Cloudflare** for your domain
2. **Enable SSL/TLS** in Cloudflare dashboard
3. **Set SSL mode** to "Full" or "Full (strict)"
4. **Use Cloudflare's origin certificate**:
   - Download from Cloudflare dashboard
   - Place in `certs/` directory

### Option 3: Commercial Certificates

1. **Purchase SSL certificate** from your provider
2. **Download certificate files**
3. **Convert to PEM format** if needed:
   ```bash
   # Convert .crt to .pem
   openssl x509 -in certificate.crt -out cert.pem -outform PEM
   
   # Convert .p12 to .pem
   openssl pkcs12 -in certificate.p12 -out cert.pem -nodes
   ```

## 🔧 Configuration

### Environment Variables

Set these environment variables for HTTPS:

```bash
# Enable HTTPS
export SSL_ENABLED=true

# Certificate paths (defaults shown)
export SSL_KEY_FILE=./certs/key.pem
export SSL_CERT_FILE=./certs/cert.pem

# Server settings
export HOST=0.0.0.0
export PORT=443  # Standard HTTPS port
```

### Configuration File

Create a `.env` file:

```env
# HTTPS Configuration
SSL_ENABLED=true
SSL_KEY_FILE=./certs/key.pem
SSL_CERT_FILE=./certs/cert.pem

# Server Configuration
HOST=0.0.0.0
PORT=443
DEBUG=false

# Security
JWT_SECRET_KEY=your-secret-key-here
API_KEY=your-admin-api-key-here
```

## 🚀 Starting the Server

### Development Mode

```bash
# Generate certificates first
python generate_certs.py

# Start with HTTPS
python start_https.py
```

### Production Mode

```bash
# Set environment variables
export SSL_ENABLED=true
export DEBUG=false

# Start server
python start_https.py
```

### Using uvicorn directly

```bash
uvicorn api.main:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile ./certs/key.pem \
  --ssl-certfile ./certs/cert.pem
```

## 🔒 Security Best Practices

### Certificate Security

1. **File Permissions**:
   ```bash
   chmod 600 certs/key.pem    # Private key - read/write owner only
   chmod 644 certs/cert.pem   # Certificate - read owner, read group/others
   ```

2. **Directory Permissions**:
   ```bash
   chmod 700 certs/           # Directory - read/write/execute owner only
   ```

3. **Ownership**:
   ```bash
   chown $USER:$USER certs/   # Owned by application user
   ```

### Server Security

1. **Use Strong Ciphers**:
   - TLS 1.2+ only
   - ECDHE-RSA-AES256-GCM-SHA384
   - ECDHE-RSA-AES128-GCM-SHA256

2. **Security Headers**:
   - HSTS (HTTP Strict Transport Security)
   - CSP (Content Security Policy)
   - X-Frame-Options
   - X-Content-Type-Options

3. **Rate Limiting**:
   - Configure appropriate rate limits
   - Monitor for abuse

### Network Security

1. **Firewall Configuration**:
   ```bash
   # Allow HTTPS traffic
   sudo ufw allow 443/tcp
   
   # Redirect HTTP to HTTPS (optional)
   sudo ufw allow 80/tcp
   ```

2. **Reverse Proxy** (Recommended):
   - Use Nginx or Apache as reverse proxy
   - Handle SSL termination at proxy level
   - Forward to application on localhost

## 🔧 Troubleshooting

### Common Issues

1. **Certificate Not Found**:
   ```
   ❌ SSL certificates not found!
   Run: python generate_certs.py
   ```
   **Solution**: Generate certificates or check file paths

2. **Permission Denied**:
   ```
   PermissionError: [Errno 13] Permission denied: './certs/key.pem'
   ```
   **Solution**: Fix file permissions:
   ```bash
   chmod 600 certs/key.pem
   chmod 644 certs/cert.pem
   ```

3. **Port Already in Use**:
   ```
   OSError: [Errno 98] Address already in use
   ```
   **Solution**: Change port or stop conflicting service:
   ```bash
   export PORT=8443
   ```

4. **Browser Security Warning**:
   - Self-signed certificates show security warnings
   - Click "Advanced" → "Proceed to localhost"
   - For production, use trusted CA certificates

### Certificate Validation

Test your certificates:

```bash
# Check certificate details
openssl x509 -in certs/cert.pem -text -noout

# Verify certificate chain
openssl verify certs/cert.pem

# Test SSL connection
openssl s_client -connect localhost:8443 -servername localhost
```

### Logs and Debugging

Enable debug mode for troubleshooting:

```bash
export DEBUG=true
python start_https.py
```

Check logs for SSL-related errors and connection issues.

## 📋 Checklist

### Development Setup
- [ ] Generate self-signed certificates
- [ ] Test HTTPS server startup
- [ ] Verify web interface access
- [ ] Test API endpoints

### Production Setup
- [ ] Obtain trusted SSL certificates
- [ ] Configure proper file permissions
- [ ] Set up auto-renewal (Let's Encrypt)
- [ ] Configure firewall rules
- [ ] Test certificate validation
- [ ] Monitor SSL/TLS configuration
- [ ] Set up reverse proxy (recommended)
- [ ] Configure security headers
- [ ] Test all API endpoints
- [ ] Verify client connections

## 🔗 Additional Resources

- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)
- [Cloudflare SSL/TLS Guide](https://developers.cloudflare.com/ssl/)
- [OpenSSL Documentation](https://www.openssl.org/docs/)
- [FastAPI HTTPS Guide](https://fastapi.tiangolo.com/deployment/https/)
- [Uvicorn SSL Configuration](https://www.uvicorn.org/settings/#ssl)

## 🆘 Support

If you encounter issues:

1. Check the troubleshooting section above
2. Verify certificate validity and permissions
3. Review server logs for error messages
4. Test with a simple HTTPS client
5. Consult the FastAPI and Uvicorn documentation

For security-related issues, ensure you're following all security best practices and using trusted certificates in production. 