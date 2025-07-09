# API Key Management Guide

This guide explains how to create, manage, and use API keys for the Desktop Search API.

## 🔑 Overview

The Desktop Search API supports two authentication methods:
1. **API Key Authentication** - Simple key-based access
2. **JWT Token Authentication** - Token-based with expiration

## 🚀 Quick Start

### 1. Set Up Admin Key (First Time Only)

Before creating API keys, you need to set an admin key:

```bash
# Set environment variable
export API_KEY="your-super-secret-admin-key-here"

# Or add to your .env file
echo "API_KEY=your-super-secret-admin-key-here" >> .env
```

### 2. Create Your First API Key

#### Using CLI:
```bash
# Create a basic API key
python main.py auth create-key --name "My First Key" --description "For testing"

# Create with specific permissions
python main.py auth create-key \
  --name "Search Only Key" \
  --description "Read-only access for search" \
  --permissions read search \
  --expires-days 30

# Create with admin key (if required)
python main.py auth create-key \
  --name "Admin Key" \
  --description "Full access" \
  --permissions read search index admin \
  --admin-key "your-admin-key"
```

#### Using Frontend:
1. Open the web interface: https://localhost:8443
2. Click on "API Keys" tab
3. Fill in the form:
   - **Name**: Give your key a descriptive name
   - **Description**: Optional description
   - **Expires in**: Days until expiration (optional)
   - **Permissions**: Select required permissions
   - **Admin Key**: Enter if required
4. Click "Create API Key"
5. **IMPORTANT**: Copy and save the API key - it won't be shown again!

### 3. Use Your API Key

#### In API Requests:
```bash
# Using curl
curl -k -H "Authorization: Bearer YOUR_API_KEY" \
  https://localhost:8443/api/v1/searcher/search \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "search_type": "semantic"}'

# Using JavaScript
const response = await fetch('https://localhost:8443/api/v1/searcher/search', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'test',
    search_type: 'semantic'
  })
});
```

## 📋 CLI Commands

### Create API Key
```bash
python main.py auth create-key [OPTIONS]

Options:
  --name, -n TEXT           Name for the API key [required]
  --description, -d TEXT    Description of the API key
  --expires-days, -e INTEGER  Days until expiration (1-365)
  --permissions, -p TEXT    Permissions for the key (multiple allowed)
  --admin-key, -a TEXT      Admin key for authentication
  --api-url TEXT            API base URL [default: https://localhost:8443]
```

### List API Keys
```bash
python main.py auth list-keys [OPTIONS]

Options:
  --admin-key, -a TEXT      Admin key for authentication [required]
  --api-url TEXT            API base URL [default: https://localhost:8443]
```

### Revoke API Key
```bash
python main.py auth revoke-key KEY_ID [OPTIONS]

Options:
  --admin-key, -a TEXT      Admin key for authentication [required]
  --api-url TEXT            API base URL [default: https://localhost:8443]
```

### Validate API Key
```bash
python main.py auth validate-key API_KEY [OPTIONS]

Options:
  --api-url TEXT            API base URL [default: https://localhost:8443]
```

## 🌐 Frontend Interface

### Accessing the API Key Management
1. Start the API server: `python start_https.py`
2. Open: https://localhost:8443
3. Click on "API Keys" tab

### Features Available:
- **Create API Key**: Generate new keys with custom permissions
- **List Keys**: View all existing keys (requires admin key)
- **Revoke Keys**: Delete keys (requires admin key)
- **Validate Keys**: Test if a key is valid

## 🔐 Permissions System

### Available Permissions:
- **`read`**: Read access to system information
- **`search`**: Perform searches on indexed documents
- **`index`**: Create and manage indexes
- **`admin`**: Full administrative access

### Permission Examples:
```bash
# Search-only key
python main.py auth create-key --name "Search Key" --permissions read search

# Index management key
python main.py auth create-key --name "Index Key" --permissions read search index

# Full access key
python main.py auth create-key --name "Admin Key" --permissions read search index admin
```

## 🔄 JWT Token Authentication

### Login with API Key
```bash
# Get JWT token using API key
curl -k -X POST https://localhost:8443/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"api_key": "YOUR_API_KEY"}'
```

### Use JWT Token
```bash
# Use the returned JWT token
curl -k -H "Authorization: Bearer JWT_TOKEN" \
  https://localhost:8443/api/v1/searcher/search \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}'
```

## 🛡️ Security Best Practices

### 1. Key Management
- **Store securely**: Keep API keys in environment variables or secure key management systems
- **Rotate regularly**: Change keys periodically
- **Use least privilege**: Only grant necessary permissions
- **Monitor usage**: Track key usage and revoke unused keys

### 2. Environment Setup
```bash
# Production environment variables
export API_KEY="your-admin-key"
export JWT_SECRET_KEY="your-jwt-secret"
export DEBUG=False
export ALLOWED_ORIGINS="https://yourdomain.com"
```

### 3. Key Naming Convention
Use descriptive names for easy management:
- `search-readonly-2024`
- `admin-full-access`
- `index-management-key`
- `client-app-key`

## 📊 Examples

### Create Different Types of Keys

#### 1. Search-Only Key (Most Common)
```bash
python main.py auth create-key \
  --name "Search App Key" \
  --description "Read-only access for search application" \
  --permissions read search \
  --expires-days 90
```

#### 2. Index Management Key
```bash
python main.py auth create-key \
  --name "Index Manager" \
  --description "For managing document indexes" \
  --permissions read search index \
  --expires-days 30
```

#### 3. Admin Key
```bash
python main.py auth create-key \
  --name "System Admin" \
  --description "Full system access" \
  --permissions read search index admin \
  --admin-key "your-admin-key"
```

### API Usage Examples

#### Search with API Key
```javascript
const API_KEY = 'ds_your_api_key_here';

async function searchDocuments(query) {
  const response = await fetch('http://localhost:8443/api/v1/searcher/search', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      query: query,
      search_type: 'semantic',
      limit: 10
    })
  });
  
  return response.json();
}
```

#### List Directories with API Key
```bash
curl -H "Authorization: Bearer ds_your_api_key_here" \
  http://localhost:8443/api/v1/directories/list
```

## 🚨 Troubleshooting

### Common Issues

#### 1. "Invalid API key" Error
- Check if the key is correct
- Verify the key hasn't expired
- Ensure the key has the required permissions

#### 2. "Admin key required" Error
- Set the `API_KEY` environment variable
- Use the `--admin-key` parameter in CLI commands
- Enter the admin key in the frontend

#### 3. "Permission denied" Error
- Check if your key has the required permissions
- Create a new key with appropriate permissions

#### 4. "Key expired" Error
- Create a new API key
- Check the expiration date when creating keys

### Debug Commands
```bash
# Validate a key
python main.py auth validate-key YOUR_API_KEY

# List all keys (requires admin key)
python main.py auth list-keys --admin-key YOUR_ADMIN_KEY

# Check API health
curl http://localhost:8443/health
```

## 📝 API Reference

### Authentication Endpoints

#### Create API Key
```http
POST /api/v1/auth/create-key
Content-Type: application/json

{
  "name": "string",
  "description": "string (optional)",
  "expires_days": "integer (optional)",
  "permissions": ["string"],
  "admin_key": "string (optional)"
}
```

#### List API Keys
```http
GET /api/v1/auth/list-keys?admin_key=string
```

#### Revoke API Key
```http
DELETE /api/v1/auth/revoke-key/{key_id}?admin_key=string
```

#### Validate API Key
```http
POST /api/v1/auth/validate-key
Content-Type: application/json

{
  "api_key": "string"
}
```

#### Login with API Key
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "api_key": "string"
}
```

## 🔄 Migration from No Auth

If you're upgrading from a version without authentication:

1. **Set admin key**:
   ```bash
   export API_KEY="your-admin-key"
   ```

2. **Create your first API key**:
   ```bash
   python main.py auth create-key --name "Default Key" --permissions read search index admin
   ```

3. **Update your applications** to use the new API key in Authorization headers

4. **Test everything works** before deploying to production

## 📞 Support

For issues with API key management:
1. Check the troubleshooting section above
2. Validate your API key using the CLI or frontend
3. Check the API logs for detailed error messages
4. Ensure all environment variables are set correctly 