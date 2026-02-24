# Usage Guide - How to Use Legal AI Chatbot

Complete guide for end users to effectively use the Legal AI Chatbot system.

## Getting Started

### Login / Registration

#### First Time Users

1. Visit http://localhost:5173 (or your deployment URL)
2. Click **"Create Account"** tab
3. Enter:
   - **Email**: Your email address (or any username)
   - **Password**: At least 6 characters (e.g., `MySecurePass123`)
4. Click **"Register"**
5. After successful registration, you're automatically logged in

#### Returning Users

1. Click **"Login"** tab (default)
2. Enter your credentials
3. Click **"Login"**
4. Session persists across browser refreshes

**Default Credentials:**
- Email: `admin`
- Password: `admin123`

---

## 📄 Document Upload

### Uploading a Document

1. Click **"Upload Document"** button in sidebar
2. Select a PDF file (legal contracts, agreements, acts, etc.)
3. Wait for processing (5-10 seconds for typical contracts)
4. See confirmation: "Document uploaded and processed"

### What Happens During Upload

```
Your PDF
  ↓
Text extraction (all pages combined)
  ↓
Intelligent chunking (45-50 logical sections)
  ↓
Vector embedding (mathematical representation)
  ↓
Index creation (enables fast search)
  ↓
Ready for questions!
```

### Supported Formats
- ✅ PDF (.pdf)
- ❌ Word, Excel, images (use PDF format)

### File Size Limits
- Recommended: < 20 MB
- Maximum: 50 MB (best performance)

### Example Documents to Try
- Employment contracts
- Service agreements
- NDA (Non-Disclosure Agreements)
- Lease documents
- Terms & Conditions
- Legal acts (like Aadhaar Act)

---

## ❓ Asking Questions

### How to Ask Effective Questions

#### Natural Language Questions
```
❌ Poor: "liability"
✅ Good: "What is the employee's liability?"

❌ Poor: "penalty clause"
✅ Good: "What penalties apply if I breach this?

❌ Poor: "section 5"
✅ Good: "What does section 5 cover?"
```

#### Legal Reference Questions
System understands direct legal references:
```
✅ "What is section 1 of Aadhaar Act?"
✅ "Tell me about clause 3.2"
✅ "What does Article 5 state?"
✅ "Explain section 1(2) of GDPR"
```

#### Supported Question Types
- **Definition**: "What is indemnity?"
- **Clause Lookup**: "What is section 5?"
- **Finding Issues**: "Are there any termination clauses?"
- **Legal Concepts**: "What is liability cap?"
- **Document Analysis**: "What are the penalties?"

### Question Examples by Domain

#### Employment Law
- "What is the notice period for termination?"
- "What are the employee's obligations?"
- "Is there a non-compete clause?"
- "What benefits are included?"

#### Contract Law
- "What are the liability limits?"
- "Who has indemnification obligations?"
- "What triggers force majeure?"
- "How can this be terminated?"

#### Intellectual Property
- "Who owns the IP created?"
- "What are the confidentiality terms?"
- "Are there licensing restrictions?"

---

## 📊 Understanding Answers

### Answer Components

Each answer includes:

```json
{
  "answer": "The full text answer...",
  "clause_reference": "Section 5",
  "confidence_score": 0.95,
  "answer_source": "retrieval",
  "risk_level": "High",
  "risk_reason": "Contains termination without notice"
}
```

#### Confidence Score (0.0 - 1.0)
- **0.95-1.0**: Very confident (exact match or direct retrieval)
- **0.80-0.95**: Confident (good semantic match)
- **0.60-0.80**: Moderate (reasonable answer)
- **< 0.60**: Low confidence (fallback to general knowledge)

#### Answer Sources
- **retrieval**: Found in your document
- **retrieval_direct_clause**: Direct section/clause lookup
- **reranker**: Fine-tuned model selected
- **gemini_fallback**: General knowledge from Google Gemini (not in your docs)

#### Clause Reference
Shows where the answer came from:
- "Section 5" - Specific section
- "Not Available" - General knowledge
- "Clause 3.14" - Specific clause

---

## 🚨 Risk Analysis

### What is Risk Analysis?

The system scans your entire document and identifies clauses that could pose legal risks:
- **High Risk**: Unfavorable termination terms, unlimited liability
- **Medium Risk**: Financial penalties, strict requirements
- **Low Risk**: Standard clauses, neutral language

### How to Use Risk Analysis

1. Upload a document
2. Click **"Analyze Document"** button
3. View results:

```
Risk Summary:
├─ Total Sections: 45
├─ Risk Sections Found: 8
├─ High Risk: 2
└─ Medium Risk: 6

Risk Details:
├─ Section 3: HIGH - "Employer can terminate without notice"
├─ Section 7: MEDIUM - "Liquidated damages clause"
├─ Section 12: MEDIUM - "Confidential information penalties"
...
```

### Interpreting Risk Levels

**HIGH RISK** 🔴
- Unfavorable termination clauses
- Unlimited liability provisions
- One-sided obligations
- Automatic renewal traps
- **Action**: Review with lawyer, negotiate

**MEDIUM RISK** 🟡
- Financial penalties
- Confidentiality breaches
- Specific performance requirements
- **Action**: Understand implications, set expectations

**LOW RISK** 🟢
- Standard legal language
- Neutral provisions
- Common terms
- **Action**: Note for reference

### Export Risk Analysis

Currently displays in browser. To save:
1. Right-click → Print to PDF
2. Or copy text manually
3. (Feature: Export to CSV coming soon)

---

## 📝 Document Summarization

### Getting a Summary

1. Upload a document
2. Click **"Get Summary"** button
3. Wait 3-8 seconds
4. View automatically generated summary

### What's Included in Summary

The summary covers:
- **Parties**: Who's involved (Company A, Employee, etc.)
- **Document Type**: Employment agreement, Service contract, etc.
- **Purpose**: What's the main goal
- **Key Terms**: Important conditions
- **Obligations**: What each party must do
- **Duration**: How long it lasts

### Summary Example

```
"This is an Employment Agreement between ABC Corporation 
and [Employee]. The agreement outlines the terms of 
employment starting January 1, 2024. The employee will 
receive a base salary, health insurance, and 401(k) 
benefits. Employment is at-will with 30 days notice for 
termination. The employee agrees to confidentiality and 
non-compete terms for 2 years post-employment."
```

---

## 💬 Chat History

### Session Management

- **Auto-save**: Conversation saved in browser
- **New Session**: Click "New Chat" in sidebar
- **Switch Sessions**: Click on previous conversations
- **Clear All**: Click "Clear History" (⚠️ Cannot undo)

### Export Conversation

Currently saved locally. To preserve:
1. Screenshot important Q&As
2. Copy-paste to text file
3. (Feature: Export to JSON coming soon)

---

## 🔐 Account Management

### Changing Settings

**Currently available**:
- Logout button (top right)
- Account email visible in profile

**Coming soon**:
- Change password
- Download conversation history
- Preferences/settings

### Logging Out

1. Click user icon (top right)
2. Click **"Logout"**
3. Session cleared, browser redirected to login

### Security Notes

- ✅ Password is **never** sent in plaintext
- ✅ Token-based authentication (expires after 1 hour)
- ✅ All data stored locally (personal files not transmitted)
- ✅ Documents analyzed on-device first

---

## ⚡ Tips & Tricks

### Search Better

1. **Use keywords from document**: If asking about "Force Majeure", use exact phrase
2. **Ask follow-ups**: "Tell me more about clause X" after initial answer
3. **Be specific**: "liability in case of breach" vs just "liability"
4. **Spell matters**: Try alternatives if first question fails

### Understand Embeddings

The system uses AI to understand meaning, not just keywords:
- ✅ "What happens if I break the agreement?" matches "breach provisions"
- ✅ "Penalties" matches "liquidated damages"
- ✅ "Secrecy" matches "confidentiality"

### Multiple Documents

- Currently analyzes **most recently uploaded** document
- To analyze different document: Upload new one (overwrites)
- (Feature: Multi-document search coming soon)

### Improve Accuracy

1. **Upload clean PDFs** (extracted text, not scans)
2. **Ask specific questions** (vs vague)
3. **Check answer source** (retrieval vs fallback)
4. **Review confidence score** (0.95 > 0.60)

---

## 🆘 Troubleshooting

### Login Issues

**Problem**: "Invalid username or password"
- Check CAPS LOCK
- Verify exact email/username entered
- Try "admin" / "admin123" to verify system works
- Create new account if forgot password

**Problem**: "Unable to connect to authentication service"
- Check backend is running (`python -m uvicorn...`)
- Verify API URL in frontend config
- Check CORS settings

### Upload Issues

**Problem**: "Failed to upload document"
- File must be PDF format
- File size < 50 MB
- PDF must be readable (not scanned image)
- Check disk space available (5GB min)

**Problem**: Backend not processing upload
- Check `backend/uploads/` exists
- Verify FAISS index is working
- Check for disk space issues

### Question/Answer Issues

**Problem**: "No document uploaded"
- Must upload PDF first
- Upload most recent document is analyzed
- Can't ask questions without document

**Problem**: "Answers don't match document"
- Confidence score too low? (< 0.70 = less reliable)
- Answer source is "gemini_fallback"? (general knowledge, not from your doc)
- Try re-phrasing question with document keywords

**Problem**: Consistent "Unable to reach service"
- Check backend running on correct port
- Check GEMINI_API_KEY is set
- Check internet connection

### Risk Analysis Issues

**Problem**: No risk sections found
- Document may not have risk keywords
- Try asking specific questions instead
- Try "What are the penalties?" question

### Performance Issues

**Problem**: Slow responses (> 10 seconds)
- Ollama model might be first-load (downloads on first run)
- System falls back to Gemini if Ollama times out (slower)
- Large documents take longer to process

---

## 📱 Keyboard Shortcuts

Available in chat area:
- **Enter**: Send message
- **Shift+Enter**: New line in message
- **Ctrl+L / Cmd+L**: Clear chat history

---

## 🎓 Learning Resources

### Understanding Legal Documents

1. **Legal Concepts**
   - Liability: Legal responsibility for damages
   - Indemnity: Compensation for loss
   - Breach: Violation of contract terms
   - Force Majeure: Unforeseeable circumstances

2. **Document Types**
   - Employment Agreement: Defines employment terms
   - NDA: Protects confidential information
   - Service Agreement: Outlines service delivery
   - Terms & Conditions: User rights and obligations

### Video Tutorials (Coming Soon)

- How to upload documents
- How to ask effective questions
- Understanding risk analysis
- Interpreting answers

---

## 💡 Best Practices

### For Contract Review

1. **Upload contract**
2. **Run risk analysis** → Identify problem areas
3. **Ask specific questions** → Understand each clause
4. **Check confidence** → Trust answers with 0.85+
5. **Document findings** → Copy important Q&As
6. **Consult lawyer** → For high-risk items

### For Legal Research

1. **Upload reference document** (Act/regulation)
2. **Ask section-specific questions** → "What is section 5?"
3. **Ask definition questions** → "What does X mean?"
4. **Cross-reference** → Ask follow-ups for clarity

### For Compliance

1. **Upload compliance document** (policy, regulation)
2. **Ask obligation questions** → "What must we do?"
3. **Ask penalty questions** → "What's the penalty?"
4. **Document answers** → Export findings

---

## 🔄 Workflow Examples

### Workflow 1: Employment Contract Review

```
1. Login
2. Upload employment_agreement.pdf
3. Click "Analyze Document"
   → See 8 risk sections identified
4. Ask: "What is the notice period to terminate?"
   → Find 3-month notice requirement
5. Ask: "Are there non-compete terms?"
   → Get specific clause details
6. Ask: "What benefits are included?"
   → Review benefits section
7. Make notes of key findings
8. If concerns found, consult HR/lawyer
```

### Workflow 2: Legal Reference Lookup

```
1. Login
2. Upload Aadhaar_Act.pdf
3. Ask: "What is section 1 of Aadhaar Act?"
   → Get section 1 full text
4. Ask: "What is section 3?"
   → Learn about Aadhaar numbers
5. Ask: "What are penalties for violations?"
   → Find applicable penalties
6. Export conversation for reference
```

### Workflow 3: Q&A with Multiple Follow-ups

```
1. Upload service_agreement.pdf
2. Ask: "What is liability cap?"
   → Get answer
3. Ask: "Tell me more about indemnification"
   → Clarifying follow-up
4. Ask: "Who bears the costs?"
   → Related question
5. Ask: "What happens on termination?"
   → Moving to new topic
```

---

## 📞 Support & Feedback

### Getting Help

1. Check this guide first
2. See Troubleshooting section
3. Review example workflows
4. Contact support with:
   - What you tried
   - Exact error message
   - Document involved (if shareable)

### Report Issues

- Email: support@legalai.example
- GitHub Issues: (if open source)
- Include: Screenshot, steps to reproduce, browser info

---

## 🔜 Coming Soon

- Multi-document search
- Export to Word/PDF
- Conversation history download
- Collaborative annotations
- Custom risk rules
- Batch file processing
- Email subscription to updates

---

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**For Support**: See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
