# API Security Guide

This document outlines the security measures implemented in the Desktop Search API and provides guidance for secure deployment.

## 🔒 Security Features Implemented

### 1. **Authentication & Authorization**
- **JWT Token Authentication**: Secure token-based authentication
- **API Key Authentication**: Alternative simple API key authentication
- **Token Expiration**: Configurable token expiration times
- **Secure Token Storage**: Encrypted token storage

### 2. **Rate Limiting**
- **Request Limiting**: Configurable requests per time window
- **Burst Protection**: Prevents rapid-fire requests
- **IP-based Tracking**: Tracks requests by client IP
- **Configurable Limits**: Adjustable via environment variables

### 3. **Input Validation & Sanitization**
- **Path Validation**: Prevents directory traversal attacks
- **Type Validation**: Pydantic models ensure type safety
- **Content Validation**: File content security checks
- **Size Limits**: Prevents memory exhaustion attacks

### 4. **Security Headers**
- **X-Content-Type-Options**: Prevents MIME type sniffing
- **X-Frame-Options**: Prevents clickjacking
- **X-XSS-Protection**: XSS protection
- **Content-Security-Policy**: Resource loading restrictions
- **Strict-Transport-Security**: HTTPS enforcement
- **Referrer-Policy**: Controls referrer information

### 5. **CORS Configuration**
- **Restricted Origins**: Only allowed origins can access the API
- **Method Restrictions**: Limited HTTP methods
- **Production vs Development**: Different settings for environments

## 🚀 Deployment Security Checklist

### Environment Variables
Set these environment variables for production:

```bash
# Authentication
JWT_SECRET_KEY=your-super-secret-jwt-key-here
API_KEY=your-api-key-here
JWT_EXPIRE_MINUTES=30

# Rate Limiting
RATE_LIMIT_ENABLED=true
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600
RATE_LIMIT_BURST=100

# CORS (Production)
ALLOWED_ORIGINS=https://yourdomain.com,https://app.yourdomain.com

# Server Settings
DEBUG=False
HOST=127.0.0.1
PORT=8443
```

### Production Deployment Steps

1. **Generate Secure Keys**:
   ```bash
   # Generate JWT secret
   openssl rand -hex 32
   
   # Generate API key
   openssl rand -hex 32
   ```

2. **Set Up HTTPS**:
   ```bash
   # Use a reverse proxy (nginx) with SSL
   # Or use uvicorn with SSL certificates
   uvicorn api.main:app --ssl-keyfile=key.pem --ssl-certfile=cert.pem
   ```

3. **Configure Firewall**:
   ```bash
   # Only allow necessary ports
   sudo ufw allow 8443
   sudo ufw enable
   ```

4. **Set File Permissions**:
   ```bash
   # Secure configuration files
   chmod 600 .env
   chmod 700 data/
   ```

## 🔍 Security Testing

### Manual Testing
```bash
# Test rate limiting
for i in {1..15}; do curl -k -X GET https://localhost:8443/health; done

# Test path traversal
curl -k -X POST "https://localhost:8443/api/v1/directories/add?path=../../../etc/passwd"

# Test CORS
curl -k -H "Origin: https://malicious.com" -X GET https://localhost:8443/health

# Test authentication
curl -k -X GET https://localhost:8443/api/v1/directories/list
```

### Automated Testing
Run the security test suite:
```bash
python -m pytest tests/test_security.py -v
```

## 🛡️ Security Best Practices

### For Developers
1. **Never commit secrets**: Use environment variables
2. **Validate all inputs**: Always validate user input
3. **Use HTTPS**: Always use HTTPS in production
4. **Keep dependencies updated**: Regular security updates
5. **Log security events**: Monitor for suspicious activity

### For Administrators
1. **Regular backups**: Backup configuration and data
2. **Monitor logs**: Watch for security events
3. **Update regularly**: Keep system and dependencies updated
4. **Access control**: Limit access to production systems
5. **Incident response**: Have a plan for security incidents

## 🚨 Security Incident Response

### If You Suspect a Breach
1. **Isolate the system**: Stop the API immediately
2. **Preserve evidence**: Don't delete logs or files
3. **Assess damage**: Determine what was accessed
4. **Reset credentials**: Change all API keys and tokens
5. **Update security**: Implement additional measures
6. **Notify stakeholders**: Inform relevant parties

### Common Attack Vectors
- **Path Traversal**: Attempts to access files outside intended directories
- **SQL Injection**: Malicious SQL in input parameters
- **XSS**: Script injection in search queries
- **Rate Limiting Bypass**: Attempts to overwhelm the API
- **Authentication Bypass**: Attempts to access without credentials

## 📊 Security Monitoring

### Log Monitoring
Monitor these log patterns:
- Failed authentication attempts
- Rate limit violations
- Path traversal attempts
- Unusual request patterns
- Error rate spikes

### Metrics to Track
- Authentication success/failure rates
- Rate limiting events
- Request volume by IP
- Error rates by endpoint
- Response times

## 🔧 Security Configuration Examples

### Nginx Reverse Proxy
```nginx
server {
    listen 443 ssl;
    server_name yourdomain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Docker Security
```dockerfile
FROM python:3.11-slim

# Create non-root user
RUN useradd -m -u 1000 appuser

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app

USER appuser
EXPOSE 8443

CMD ["uvicorn", "api.main:app", "--host", "127.0.0.1", "--port", "8443"]
```

## 📞 Security Contact

For security issues:
1. **Do not** create public issues
2. Email: security@yourdomain.com
3. Include detailed reproduction steps
4. Allow reasonable time for response

## 🔄 Security Updates

This security guide is updated regularly. Check for updates:
- Review security advisories for dependencies
- Monitor security news and best practices
- Regular security audits of the codebase
- Update this document as new threats emerge 