# Requirement Generator: AI-Powered Engineering Assistant

## Slide 1: Introduction
**Project Overview**
The **Requirement Generator** is an advanced, GenAI-powered engineering assistant designed to automatically analyze software repositories and intelligently generate comprehensive documentation, requirements, and test cases.

**Key Value Proposition**
- Drastically reduces time spent on manual documentation.
- Ensures comprehensive coverage of edge cases and validation rules.
- Acts as an intelligent companion to understand legacy or undocumented codebases.

---

## Slide 2: Core Features
**What can it do?**
1. **Intelligent Analysis**: Ingests code via direct upload or GitHub repository link.
2. **Comprehensive Generation**: Automatically extracts and generates:
   - Functional Requirements
   - API Specifications
   - User Stories (Persona-based)
   - Validation Rules
   - Edge Cases & Unit Test Scenarios
3. **Interactive Code Chat**: Ask context-aware questions directly against your codebase.
4. **Rich Export Options**: Download results in Excel, PDF, or Markdown formats for easy sharing.
5. **Persistent History**: Keeps track of all your past analysis generations directly in your browser.

---

## Slide 3: Architecture & Tech Stack
**A modern, robust, and scalable architecture:**

**Frontend (Client)**
- **Framework**: React 18 with Vite for lightning-fast builds.
- **UI/UX**: Material UI (MUI) for a clean, accessible component system, enhanced with Framer Motion for fluid micro-animations.
- **State & Storage**: React Context API, with IndexedDB (`localforage`) for persisting large analysis results locally.

**Backend (Server)**
- **Framework**: FastAPI (Python) for high-performance, asynchronous API routes.
- **Server**: Uvicorn.
- **Processing**: Token-aware chunking and map-reduce flows for handling massive codebases.

**AI & Cloud Infrastructure**
- **LLM Engine**: Azure OpenAI (GPT-4o) for state-of-the-art code understanding and generation.
- **Embeddings**: Azure OpenAI (`text-embedding-3-large`) for semantic search.
- **Search & Storage**: Azure AI Search for vector search indexing, and Azure Blob Storage for persisting generated reports.

---

## Slide 4: User Workflow
**How does it work in practice?**
1. **Input**: The user provides a repository (GitHub URL or ZIP upload).
2. **Processing**: The backend parses the code, chunks it, and generates embeddings.
3. **Generation**: The AI engine maps out the architecture and generates specific artifacts (e.g., User Stories, Test Cases).
4. **Review**: The user explores the generated artifacts in a rich, interactive Dashboard (DataGrids, summary charts).
5. **Refinement**: The user can open the "Chat with Codebase" feature to drill down into specific logic or ask follow-up questions.
6. **Export**: The final polished requirements are exported to standard formats.

---

## Slide 5: Recent Improvements & Reliability
**Built for scale and resilience:**
- **Local Persistence**: Transitioned from standard `localStorage` to **IndexedDB** to safely handle massive datasets (5MB+ of generated requirements) without browser quota crashes.
- **Port Conflict Resolution**: Configured to run on dynamic ports (e.g., Backend on 8001, Frontend on 3000) to ensure seamless operation alongside other local projects (like the Resume Scanner).
- **Responsive UI**: Dark/Light mode support with detailed dialogs for inspecting specific requirement edge cases.

---

## Slide 6: Future Roadmap
- Integration with Jira/Azure DevOps for direct ticket creation.
- Automated PR reviews based on generated functional requirements.
- Real-time collaborative editing of generated requirements.
