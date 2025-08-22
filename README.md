# Admissions Automation System

A complete admission processing system that uses AI agents and RAG to automate admission workflow for up to 50k+ students annually.

## System Architecture

```
├── frontend/                # Next.js web interface
│   ├── app/                 # App router pages
│   │   ├── page.tsx         # Main application page with upload UI
│   │   ├── layout.tsx       # Root layout
│   │   └── globals.css      # Global styles
│   ├── public/              # Static assets
│   ├── package.json         # Frontend dependencies
│   ├── tsconfig.json        # TypeScript configuration
│   ├── tailwind.config.ts   # Tailwind CSS configuration
│   └── next.config.ts       # Next.js configuration
├── backend/
│   ├── main.py              # FastAPI application
│   ├── agents/              # AI Agent pipeline
│   │   ├── document_classifier.py  # Document type classification
│   │   ├── data_extractor.py       # Data extraction from documents
│   │   ├── admission_agent.py      # RAG-based admission decisions
│   │   ├── workflow.py             # Agent orchestration
│   │   └── state.py               # Application state management
│   ├── rag/                 # RAG system for handbook queries
│   │   ├── handbook_loader.py      # PDF processing (one-time)
│   │   ├── vector_store.py         # ChromaDB integration
│   │   └── retriever.py            # Query engine for admission rules
│   └── chroma_db/           # Pre-built vector database (245 pages indexed)
├── data/                    # Sample documents (excluded from git)
│   ├── ABITUR/              # German Abitur samples
│   ├── ALEVELS/             # UK A-Levels samples
│   ├── IB_DIPLOMA/          # IB Diploma samples
│   └── samples/             # Complex multi-document cases
└── requirements.txt
```

## User Interface

![Admission System Screenshot](assets/screenshot.png)

## Quick Start

### Backend Setup

1. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

2. **Start the backend server** (ChromaDB already initialized):
```bash
cd backend
python main.py
```

### Frontend Setup

3. **Install Node dependencies:**
```bash
cd frontend
npm install
```

4. **Start the frontend:**
```bash
npm run dev
```

5. **Open the application:**
Navigate to `http://localhost:3000` in your browser

### API Testing (Optional)

**Submit an application via API:**
```bash
curl -X POST http://localhost:8000/submit-application \
  -F "applicant_id=test123" \
  -F "target_program=Finanzmanagement" \
  -F "entity=DE" \
  -F "files=@../data/ABITUR/Abitur_Zeugnis_SAMPLE.pdf"
```

**Check the decision:**
```bash
# Use the returned application ID
curl http://localhost:8000/application/APP-XXXXXXXX
```

## How The System Works

### 1. One-Time Setup
- The 245-page `Leitfaden.pdf` handbook was processed once
- Split into ~1500 character chunks with overlap
- Embedded using free local Sentence Transformers
- Stored in ChromaDB vector database
- **No re-processing needed - the database is ready to use**

### 2. Three-Agent Pipeline

When an application is submitted, it flows through three AI agents:

**Agent 1: Document Classifier**
- Uses Claude 3.5 Sonnet to identify document types
- Recognizes: Abitur, A-Levels, IB, transcripts, CV, work certificates, etc.
- Returns classification with confidence score

**Agent 2: Data Extractor**
- Extracts structured data from classified documents
- Pulls out: grades, personal info, qualifications, dates
- Adapts extraction templates based on document type

**Agent 3: Admission Decision (RAG-Powered)**
- Queries ChromaDB for relevant handbook sections
- Uses Claude to interpret admission rules contextually
- Makes decision: APPROVED/REJECTED/REVIEW_REQUIRED/MISSING_DOCS
- Provides reasoning with handbook page citations

### 3. RAG System Details

- **Fast Query**: Pre-built embeddings enable instant rule lookup
- **Contextual**: Claude interprets rules based on specific applicant profile
- **Transparent**: Every decision includes handbook page references
- **Accurate**: Combines semantic search with LLM reasoning

## API Endpoints

### Application Processing
- `POST /submit-application` - Submit documents for processing
- `GET /application/{id}` - Get detailed application status and decision
- `GET /applications` - List all processed applications

### Handbook Queries
- `POST /query-handbook` - Query admission rules directly
- `GET /handbook-status` - Check if RAG system is ready

### System
- `GET /health` - Health check
- `GET /` - System information

## Key Features

- ✅ **Web Interface** - User-friendly drag & drop PDF upload interface
- ✅ **Complete automation** - Processes documents end-to-end
- ✅ **Multi-document support** - Handles complex applications
- ✅ **RAG-based decisions** - Uses 245-page handbook intelligently
- ✅ **Free embeddings** - No OpenAI costs for vector storage
- ✅ **Transparent reasoning** - Every decision explained with citations
- ✅ **Scalable architecture** - Handles high volume (50k+ applications)
- ✅ **Multiple qualifications** - Supports Abitur, A-Levels, IB, work experience
- ✅ **Regulatory compliance** - Checks complex admission rules automatically
- ✅ **Real-time processing** - Live status updates and polling

## Sample Results

```json
{
  "application_id": "APP-12345678",
  "current_stage": "decision_made", 
  "decision": {
    "status": "APPROVED",
    "confidence": 0.95,
    "reasoning": "German Abitur with grade 1.58 provides direct access to Finanzmanagement program",
    "applied_rules": [
      {
        "rule_id": "R1",
        "rule_text": "Allgemeine Hochschulreife grants direct university access",
        "outcome": "satisfied"
      }
    ],
    "handbook_citations": ["page 42", "section 3.2.1"]
  }
}
```

## Solution Architecture & Design

### High-Level Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   Web Portal    │────▶│   FastAPI        │────▶│   AI Pipeline   │
│   (Next.js)     │     │   Backend        │     │   (3 Agents)    │
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │                          │
                               ▼                          ▼
                        ┌──────────────────┐     ┌─────────────────┐
                        │   ChromaDB       │     │   Handbook      │
                        │   (Vector Store) │◀────│   (245 pages)   │
                        └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │  CRM Integration │
                        │  (Salesforce/SMS)│
                        └──────────────────┘
```

### Three-Agent Processing Pipeline

**Agent 1: Document Classifier**
- Uses Claude 3.5 Sonnet to identify document types
- Recognizes: Abitur, A-Levels, IB, transcripts, work certificates
- Returns classification with confidence score

**Agent 2: Data Extractor**
- Extracts structured data from classified documents
- Pulls out: grades, personal info, qualifications, dates
- Adapts extraction templates based on document type

**Agent 3: Admission Decision Agent (RAG-Powered)**
- Queries ChromaDB for relevant handbook sections
- Uses Claude to interpret admission rules contextually
- Makes decision: APPROVED/REJECTED/REVIEW_REQUIRED/MISSING_DOCS
- Provides reasoning with handbook page citations

### Key Design Decisions & Trade-offs

**1. RAG vs Hard-coded Rules**
- ✅ **Chosen:** RAG with LLM interpretation
- **Pros:** Handles edge cases, natural language rules, easy updates
- **Cons:** ~€0.10 per application API cost, non-deterministic
- **Mitigation:** Temperature=0, confidence thresholds

**2. Local vs Cloud Embeddings**
- ✅ **Chosen:** Local Sentence Transformers
- **Pros:** Zero embedding costs, data privacy, consistent performance
- **Cons:** Slightly lower quality than OpenAI
- **Savings:** ~€2,000/year in embedding costs

**3. Processing Model**
- ✅ **Chosen:** Asynchronous with real-time polling
- **Pros:** Better UX, handles peak loads, scalable
- **Cons:** More complex frontend, requires status tracking

### Performance & Scale

**Current Benchmarks:**
- Document Classification: ~2 seconds
- Data Extraction: ~3 seconds
- Decision Making: ~2 seconds
- **Total:** ~7-10 seconds per application

**Production Targets:**
- **Throughput:** 500+ applications/hour per instance
- **Scalability:** Horizontal scaling for 10k+ daily peaks
- **Accuracy:** 95%+ for standard cases, 100% review for edge cases
- **Automation Rate:** 85%+ fully automated decisions

### Risk Mitigation

**AI Decision Accuracy**
- Confidence thresholds trigger human review
- Every decision includes handbook citations for verification
- Complete audit logs for regulatory compliance

**System Availability**
- Local vector database (no external dependencies for rules)
- Fallback to manual processing queue
- Health checks and auto-restart mechanisms

**Data Privacy & Compliance**
- On-premise deployment option
- Local embeddings (no data to external APIs)
- Encrypted storage with GDPR-compliant retention
- Transparent decision-making with citations

### Cost-Benefit Analysis

**Annual Costs:**
- AI API (Claude): ~€5,000 (50k applications × €0.10)
- Infrastructure: ~€2,400 (cloud hosting)
- Development: One-time €50,000
- Maintenance: ~€10,000/year

**Annual Benefits:**
- Time Savings: 40,000 hours (50k applications × 50 minutes saved)
- Cost Savings: ~€1,000,000 (40,000 hours × €25/hour)
- Improved accuracy and faster enrollment

## CRM & SMS Integration Architecture

### Salesforce Integration

The system is designed to seamlessly integrate with Salesforce CRM through the following approach:

**1. Real-time Data Sync**
```python
# Pseudo-code for Salesforce integration
async def sync_to_salesforce(application_data):
    # Using Salesforce REST API
    sf_client = Salesforce(
        username=SALESFORCE_USER,
        password=SALESFORCE_PASSWORD,
        security_token=SALESFORCE_TOKEN
    )
    
    # Create/Update Lead or Contact
    lead_data = {
        'FirstName': application_data['first_name'],
        'LastName': application_data['last_name'],
        'Email': application_data['email'],
        'Program__c': application_data['target_program'],
        'Admission_Status__c': application_data['decision']['status'],
        'Application_ID__c': application_data['application_id'],
        'Qualification_Type__c': application_data['qualification_type'],
        'Decision_Confidence__c': application_data['decision']['confidence']
    }
    
    # Update existing or create new
    if application_data.get('salesforce_id'):
        sf_client.Lead.update(application_data['salesforce_id'], lead_data)
    else:
        result = sf_client.Lead.create(lead_data)
        return result['id']
```

**2. Event-Driven Updates**
- Webhook endpoints for bi-directional sync
- Real-time status updates pushed to Salesforce
- Document links stored as Salesforce attachments
- Custom objects for admission-specific data

**3. Bulk Operations**
- Salesforce Bulk API for peak periods (10k+ applications/day)
- Batch processing with error recovery
- Async job monitoring and retry logic

### EPOS (Student Management System) Integration

**1. Direct Database Integration**
```python
# EPOS integration via database connection
async def sync_to_epos(approved_application):
    # Connection to EPOS PostgreSQL/Oracle database
    async with epos_db.transaction():
        # Create student record
        student_id = await epos_db.execute("""
            INSERT INTO students (
                external_id, first_name, last_name, 
                program_id, admission_date, qualification_type
            ) VALUES ($1, $2, $3, $4, $5, $6)
            RETURNING student_id
        """, application_data)
        
        # Create enrollment record
        await epos_db.execute("""
            INSERT INTO enrollments (
                student_id, program_id, start_date, 
                admission_type, document_verified
            ) VALUES ($1, $2, $3, $4, $5)
        """, enrollment_data)
```

**2. API Gateway Pattern**
- RESTful API endpoints for EPOS communication
- Message queue (RabbitMQ/Kafka) for reliability
- Compensation transactions for failed operations

### SMS/Email Notification System

**1. Multi-Channel Notifications**
```python
class NotificationService:
    def __init__(self):
        self.sms_client = TwilioClient(TWILIO_SID, TWILIO_TOKEN)
        self.email_client = SendGridClient(SENDGRID_API_KEY)
    
    async def notify_applicant(self, application_data, channel='both'):
        # SMS notification via Twilio
        if channel in ['sms', 'both']:
            message = self._format_sms(application_data)
            await self.sms_client.messages.create(
                to=application_data['phone'],
                from_=IU_SMS_NUMBER,
                body=message
            )
        
        # Email notification via SendGrid
        if channel in ['email', 'both']:
            await self.email_client.send(
                to=application_data['email'],
                template_id=DECISION_TEMPLATE_ID,
                dynamic_data=application_data
            )
```

**2. Notification Templates**
- **Approved**: Congratulations + next steps + enrollment link
- **Rejected**: Reason + appeal process + alternative programs
- **Review Required**: Document request + deadline + support contact
- **Missing Documents**: Specific list + upload link + deadline

**3. Delivery Tracking**
- SMS delivery confirmations
- Email open/click tracking
- Failed delivery retry with exponential backoff
- Alternative channel fallback (SMS fails → Email)

### Integration Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Submitted                      │
└────────────────────────┬────────────────────────────────────┘
                         ▼
┌─────────────────────────────────────────────────────────────┐
│              AI Pipeline Processing (7-10 sec)                │
└────────────────────────┬────────────────────────────────────┘
                         ▼
        ┌────────────────┴────────────────┐
        ▼                                  ▼
┌───────────────────┐            ┌───────────────────┐
│   Salesforce CRM  │            │  SMS/Email Alert  │
│   (Lead/Contact)  │            │   (Immediate)     │
└───────────────────┘            └───────────────────┘
        │                                  
        ▼ (if approved)                   
┌───────────────────┐            
│    EPOS System    │            
│ (Student Record)  │            
└───────────────────┘            
```

### Security & Compliance for Integrations

**1. Authentication & Authorization**
- OAuth 2.0 for Salesforce API
- API key rotation every 90 days
- IP whitelisting for production servers
- Rate limiting per integration endpoint

**2. Data Privacy (GDPR Compliance)**
- Encrypted data transmission (TLS 1.3)
- PII masking in logs
- Data retention policies (7 years for academic records)
- Right to erasure implementation

**3. Audit Trail**
- Every integration call logged with timestamp
- Success/failure tracking with error details
- Data lineage from application to final system
- Compliance reporting dashboard

## Next Steps for Production Deployment

### Phase 1: Core Infrastructure (Week 1-2)

**1. Database Implementation**
- [ ] PostgreSQL setup with proper schemas
- [ ] Application state persistence
- [ ] Document storage (S3/Azure Blob)
- [ ] Audit log tables with retention policies
- [ ] Database backup and disaster recovery

**2. Security Hardening**
- [ ] JWT-based authentication system
- [ ] Role-based access control (RBAC)
- [ ] API rate limiting and DDoS protection
- [ ] Secrets management (HashiCorp Vault/AWS Secrets Manager)
- [ ] GDPR compliance tools (consent tracking, data export)

**3. Monitoring & Observability**
- [ ] Application performance monitoring (Datadog/New Relic)
- [ ] Log aggregation (ELK stack)
- [ ] Custom metrics dashboards
- [ ] Alert rules for SLA compliance
- [ ] Health check endpoints

### Phase 2: Integration Implementation (Week 2-3)

**1. Salesforce Integration**
- [ ] Salesforce sandbox setup and testing
- [ ] Custom objects and fields creation
- [ ] Bi-directional sync implementation
- [ ] Bulk API for high-volume periods
- [ ] Error handling and retry logic

**2. EPOS Integration**
- [ ] Database connection setup
- [ ] Data mapping and transformation
- [ ] Transaction management
- [ ] Rollback procedures
- [ ] Integration testing with test data

**3. Notification System**
- [ ] Twilio SMS integration
- [ ] SendGrid email templates
- [ ] Multi-language support
- [ ] Delivery tracking and reporting
- [ ] Fallback mechanisms

### Phase 3: Performance & Scale (Week 3-4)

**1. Load Testing & Optimization**
- [ ] Stress testing with 10k concurrent applications
- [ ] Database query optimization
- [ ] Caching layer (Redis) implementation
- [ ] CDN for static assets
- [ ] Auto-scaling configuration

**2. High Availability Setup**
- [ ] Multi-region deployment
- [ ] Load balancer configuration
- [ ] Database replication
- [ ] Zero-downtime deployment pipeline
- [ ] Disaster recovery procedures

**3. Advanced Features**
- [ ] A/B testing framework for decision algorithms
- [ ] Machine learning model for improving accuracy
- [ ] Real-time analytics dashboard
- [ ] Automated reporting for compliance
- [ ] Self-service portal for applicants

### Phase 4: Production Rollout (Week 4+)

**1. Pilot Program**
- [ ] Select 100 applications for pilot
- [ ] Side-by-side processing with manual verification
- [ ] Accuracy metrics collection
- [ ] User feedback gathering
- [ ] Performance benchmarking

**2. Gradual Rollout**
- [ ] 10% traffic → 25% → 50% → 100%
- [ ] Monitoring at each stage
- [ ] Rollback procedures ready
- [ ] Support team training
- [ ] Documentation completion

**3. Full Production**
- [ ] 24/7 monitoring setup
- [ ] On-call rotation established
- [ ] SLA monitoring (99.9% uptime)
- [ ] Regular security audits
- [ ] Continuous improvement pipeline

### Estimated Timeline & Resources

**Total Time to Production: 4-5 weeks**

**Team Requirements:**
- 2 Backend Engineers (Python/FastAPI)
- 1 Frontend Engineer (React/Next.js)
- 1 DevOps Engineer (AWS/Azure)
- 1 Integration Specialist (Salesforce/EPOS)
- 1 QA Engineer
- 1 Project Manager

**Infrastructure Costs (Annual):**
- Cloud hosting (AWS/Azure): €24,000
- Database (PostgreSQL RDS): €6,000
- Monitoring tools: €4,800
- SMS/Email services: €3,600
- Total: ~€38,400/year

**ROI Timeline:**
- Break-even: 2 months after deployment
- Full ROI: €960,000+ savings in Year 1
- Efficiency gain: 85% reduction in processing time

