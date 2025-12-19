# 📚 TREEEX WhatsApp Business API - Documentation Index

Welcome to the TREEEX WhatsApp Business API documentation! This index will help you find exactly what you need.

## 🎯 Quick Navigation

### For First-Time Users
👉 Start here: **[README.md](./README.md)** - Get a quick overview and understand what the API does

### For Frontend Developers
👉 Go to: **[FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)** - Copy-paste ready code examples and integration guide

### For Complete API Reference
👉 Check: **[API_REFERENCE.mdx](./API_REFERENCE.mdx)** - Detailed documentation of all 29 endpoints

### For System Understanding
👉 Read: **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture diagrams and data flows

---

## 📖 Documentation Files

### 1. 🚀 [README.md](./README.md)
**Best for:** Everyone, especially new team members

**Contains:**
- API overview
- Quick start guide
- Authentication examples
- Common use cases
- Rate limits & security
- Technology stack

**Read this if you want to:**
- Understand what the API does
- Get started quickly
- See basic code examples
- Learn about security

---

### 2. 💻 [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md)
**Best for:** Frontend developers, React developers

**Contains:**
- Complete API client implementation
- React hooks examples
- UI component examples (Login, Send Message)
- Error handling patterns
- File upload examples
- Pagination examples
- Environment setup

**Read this if you want to:**
- Integrate the API into your frontend
- See practical code examples
- Build UI components
- Handle authentication in React
- Upload files or import contacts

**Key Sections:**
- ✅ Ready-to-use API client class
- ✅ Authentication flow (signup, signin)
- ✅ 5 common use cases with code
- ✅ React component examples
- ✅ Error handling guide

---

### 3. 📘 [API_REFERENCE.mdx](./API_REFERENCE.mdx)
**Best for:** Detailed endpoint reference, API specification

**Contains:**
- **29 documented endpoints**
- **46 data schemas**
- Request/response examples for every endpoint
- Curl and JavaScript examples
- Parameter tables
- Response codes
- Schema definitions

**Read this if you want to:**
- See all available endpoints
- Understand request/response formats
- Find specific endpoint parameters
- Copy curl or JavaScript examples
- Reference data schemas

**Organized by:**
- 🔐 Authentication (4 endpoints)
- 🏢 Workspaces (7 endpoints)
- 📞 Phone Numbers (6 endpoints)
- 💬 Messages (4 endpoints)
- 🖼️ Media (5 endpoints)
- 📝 Templates (5 endpoints)
- 👥 Contacts (6 endpoints)
- 📊 Campaigns (8 endpoints)
- 🔔 Webhooks (2 endpoints)

---

### 4. 🏗️ [ARCHITECTURE.md](./ARCHITECTURE.md)
**Best for:** Backend developers, system architects, DevOps

**Contains:**
- System architecture diagrams
- Request flow diagrams
- Data model relationships
- Authentication flow
- Message lifecycle
- Campaign workflow
- Technology stack
- RBAC permissions
- Rate limits & quotas

**Read this if you want to:**
- Understand how the system works
- See data flow diagrams
- Learn about the tech stack
- Understand permissions
- See message status lifecycle
- Plan integrations

**Includes 9 Mermaid diagrams:**
1. System architecture
2. Authentication flow
3. Send message flow
4. Media upload flow
5. Webhook processing
6. Data model (ERD)
7. RBAC permissions
8. Message status lifecycle
9. Campaign workflow

---

### 5. 🔧 [generate_docs.py](./generate_docs.py)
**Best for:** Maintainers, backend developers

**Purpose:**
- Automatically generates documentation from OpenAPI spec
- Updates API_REFERENCE.mdx
- Can be run anytime API changes

**Usage:**
```bash
# Make sure server is running first
python run.py

# In another terminal
python docs/generate_docs.py
```

---

### 6. 📄 [openapi.json](./openapi.json)
**Best for:** Tools, automation, API clients

**Purpose:**
- Machine-readable API specification
- OpenAPI 3.1 format
- Can be imported into Postman, Insomnia, etc.
- Used by generate_docs.py

**Usage:**
- Import into Postman for testing
- Generate SDKs
- Validate requests
- Auto-generate client libraries

---

### 7. 🗄️ [DATABASE_CHANGES.md](./DATABASE_CHANGES.md)
**Best for:** Backend developers, DBAs

**Purpose:**
- Documents database schema changes
- Migration notes
- Existing file (not part of this documentation update)

---

## 🎓 Learning Path

### Path 1: Frontend Developer (New to the API)
```
1. README.md (Overview)
   ↓
2. FRONTEND_GUIDE.md (Integration guide)
   ↓
3. API_REFERENCE.mdx (Specific endpoints as needed)
```

### Path 2: Backend Developer (Understanding the system)
```
1. README.md (Overview)
   ↓
2. ARCHITECTURE.md (System design)
   ↓
3. API_REFERENCE.mdx (Endpoint details)
   ↓
4. openapi.json (API specification)
```

### Path 3: Product Manager / Designer
```
1. README.md (Overview)
   ↓
2. ARCHITECTURE.md (User flows, diagrams)
   ↓
3. API_REFERENCE.mdx (Feature capabilities)
```

---

## 🔍 Find What You Need

### I want to...

#### **Authenticate users**
→ [FRONTEND_GUIDE.md - Step 1: Authentication](#)
→ [API_REFERENCE.mdx - Authentication section](#)

#### **Send a WhatsApp message**
→ [FRONTEND_GUIDE.md - Use Case 1](#)
→ [API_REFERENCE.mdx - Messages section](#)

#### **Upload an image**
→ [FRONTEND_GUIDE.md - Use Case 2](#)
→ [API_REFERENCE.mdx - Media section](#)

#### **Import contacts**
→ [FRONTEND_GUIDE.md - Use Case 3](#)
→ [API_REFERENCE.mdx - Contacts section](#)

#### **Create a campaign**
→ [FRONTEND_GUIDE.md - Use Case 4](#)
→ [API_REFERENCE.mdx - Campaigns section](#)

#### **Understand the architecture**
→ [ARCHITECTURE.md](#)

#### **See all endpoints**
→ [API_REFERENCE.mdx](#)
→ [README.md - API Structure](#)

#### **Handle errors**
→ [FRONTEND_GUIDE.md - Error Handling](#)
→ [ARCHITECTURE.md - Error Codes](#)

#### **Set up pagination**
→ [FRONTEND_GUIDE.md - Pagination Example](#)

#### **Manage workspaces**
→ [API_REFERENCE.mdx - Workspaces](#)

#### **Update documentation**
→ [generate_docs.py](#)

---

## 📊 Documentation Statistics

| Metric | Value |
|--------|-------|
| **Total Endpoints** | 29 |
| **Data Schemas** | 46 |
| **Code Examples** | 58+ |
| **Documentation Files** | 7 |
| **Diagrams** | 9 |
| **Total Size** | ~330 KB |

---

## 🛠️ Tools & Resources

### Interactive Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Recommended Tools
- **API Testing**: Postman, Insomnia
- **Markdown Viewer**: VSCode with MDX extension
- **Diagram Rendering**: Mermaid plugins
- **HTTP Client**: Thunder Client, REST Client

---

## 🔄 Keeping Documentation Updated

The documentation is auto-generated from the OpenAPI specification:

1. **When you change the API:**
   ```bash
   # Server must be running
   python run.py
   ```

2. **Generate new docs:**
   ```bash
   python docs/generate_docs.py
   ```

3. **Review changes:**
   - Check `API_REFERENCE.mdx`
   - Update `FRONTEND_GUIDE.md` if needed
   - Update `ARCHITECTURE.md` for major changes

---

## 📞 Support

- **API Issues**: Check API_REFERENCE.mdx for endpoint details
- **Integration Help**: See FRONTEND_GUIDE.md for examples
- **Architecture Questions**: Review ARCHITECTURE.md
- **General Questions**: Start with README.md

---

## 🌟 Quick Links

| Document | Size | Last Updated | Purpose |
|----------|------|--------------|---------|
| [API_REFERENCE.mdx](./API_REFERENCE.mdx) | 97 KB | 2025-12-19 | Complete endpoint reference |
| [README.md](./README.md) | 6.7 KB | 2025-12-19 | Overview & quick start |
| [FRONTEND_GUIDE.md](./FRONTEND_GUIDE.md) | 16 KB | 2025-12-19 | Frontend integration |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 17 KB | 2025-12-19 | System architecture |
| [openapi.json](./openapi.json) | 169 KB | 2025-12-19 | OpenAPI specification |
| [generate_docs.py](./generate_docs.py) | 20 KB | 2025-12-19 | Doc generator |

---

## ✨ What's New

### Latest Update (2025-12-19)
- ✅ Created comprehensive MDX documentation
- ✅ Added 58+ code examples (curl + JavaScript)
- ✅ Added 9 Mermaid architecture diagrams
- ✅ Created frontend integration guide
- ✅ Added React hooks and component examples
- ✅ Documented all 29 endpoints and 46 schemas
- ✅ Added auto-update capability

---

**Happy coding! 🚀**

For questions or suggestions about this documentation, contact the backend team.
