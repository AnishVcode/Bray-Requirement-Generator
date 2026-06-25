# Requirement Generator: Technical Documentation & Workflow

## Project Overview
The **Requirement Generator** is an advanced, GenAI-powered engineering assistant designed to automatically analyze software repositories and intelligently generate comprehensive documentation, requirements, and test cases. It acts as an intelligent companion to help understand codebases, reducing the time spent on manual documentation and ensuring comprehensive coverage of edge cases.

## Technology Stack
### Frontend (Client)
- **Framework**: React 18 with Vite
- **UI/UX**: Material UI (MUI) with Framer Motion for animations
- **State & Storage**: React Context API, IndexedDB (`localforage`) for persisting large analysis results locally.

### Backend (Server)
- **Framework**: FastAPI (Python) running on Uvicorn
- **State Management**: In-memory state storage for processing state (designed to be replaceable with Redis/DB in production)

### AI & Cloud Infrastructure
- **LLM Engine**: Azure OpenAI (GPT-4o) for code understanding and generation.
- **Embeddings**: Azure OpenAI (`text-embedding-3-large`) for semantic vectorization.
- **Search & Storage**: Azure AI Search for vector indexing and hybrid search; Azure Blob Storage for persisting reports.

---

## Detailed System Workflow

The following sections detail the end-to-end workflow of the application from the moment a user submits a codebase to the final generation of requirements and interactive chat.

### Phase 1: Repository Ingestion
1. **User Input**: The user interacts with the React frontend to provide a codebase. This can be done either by:
   - Providing a GitHub Repository URL.
   - Uploading a `.zip` archive of the codebase.
2. **API Request**: The frontend makes a request to the backend routers (`/api/repository/github` or `/api/repository/upload`).
3. **Extraction & Cloning**: The `repository_service` handles the request by either cloning the GitHub repo or extracting the uploaded ZIP file. The application state for this repository (`repo_id`) is initialized with a status of `PREPROCESSING` or `CLONING`.

### Phase 2: Code Parsing & Analysis
1. **Parsing Initiation**: The backend updates the processing status to `PARSING` (20% progress).
2. **Code Parser Engine**: The `code_parser` service iterates through all extracted files. For each valid file:
   - It determines the programming language and framework.
   - It performs static analysis to extract structural elements (e.g., routes, models, components, classes, functions).
   - It counts the lines of code and checks for the presence of test files.
3. **Repository Summary Generation**: A comprehensive `RepositorySummary` object is created. This includes detected frameworks, language distribution, total files/lines, and counts of specific element types (models, routes, services, etc.).

### Phase 3: Semantic Chunking
1. **Chunking Initiation**: The backend updates the processing status to `EMBEDDING` (50% progress).
2. **Code Chunking**: The `chunking_service` processes the raw text of each code file. Because LLMs have context window limits, the code is divided into semantic, token-aware chunks. Metadata (like file path, language, and chunk index) is attached to each chunk to maintain its context.

### Phase 4: Vector Embedding & Indexing
1. **Embedding Generation**: The code chunks are passed to the `embedding_service`. It batches the text chunks and sends them to Azure OpenAI (`text-embedding-3-large`) to generate high-dimensional vector embeddings representing the semantic meaning of the code.
2. **Indexing Initiation**: The backend updates the processing status to `INDEXING` (80% progress).
3. **Vector Database Insertion**: The `search_service` initializes or updates an index in Azure AI Search. Each chunk, along with its metadata and generated vector, is packaged into a `SearchDocument` and indexed into the vector store.
4. **Completion**: The repository processing status is marked as `COMPLETED` (100% progress). The summary, chunks, and service references are cached in the application state.

### Phase 5: Requirement Generation
1. **User Request**: From the frontend dashboard, the user selects specific categories they want to generate (e.g., Functional Requirements, API Specifications, Validation Rules, User Stories, Unit Test Scenarios). They can also specify "Target Modules" for focused generation.
2. **API Request**: The frontend calls the `/api/generate/{repo_id}` endpoint.
3. **Context Retrieval**:
   - **Targeted Generation (Map-Reduce)**: If target modules are specified, the backend performs an exhaustive map-reduce. It filters the cached code chunks to only include those matching the specified directory paths.
   - **General Generation (RAG)**: If no target modules are specified, the backend uses Retrieval-Augmented Generation. It generates an embedding for a generic query (e.g., "API routes models services components") and performs a hybrid vector search using Azure AI Search to retrieve the top most relevant chunks.
4. **LLM Invocation**: The `generation_engine` constructs a prompt combining the `RepositorySummary`, the requested categories, and the retrieved code chunks. This is sent to Azure OpenAI (GPT-4o).
5. **Storage & Delivery**: The generated artifacts are returned to the client and temporarily stored in the backend state. The frontend persists these large datasets locally using IndexedDB to prevent browser quota exhaustion.

### Phase 6: Interactive Code Chat (RAG)
1. **User Query**: The user asks a specific question about the codebase in the "Chat with Codebase" UI.
2. **API Request**: The frontend sends the chat history and the latest query to `/api/chat/{repo_id}`.
3. **Semantic Search**:
   - The backend's `embedding_service` generates a vector for the user's latest query.
   - The `search_service` performs a hybrid search against the Azure AI Search index, retrieving the top 10 code chunks most semantically relevant to the question.
4. **Context-Aware Response**: The `chat_engine` builds a prompt containing the system instructions, the retrieved code chunks (as context), and the conversation history. Azure OpenAI (GPT-4o) processes this to generate an accurate, context-aware answer which is returned to the user.

### Phase 7: Exporting
- The final polished requirements and documentation can be exported by the user. The system supports exporting results into standard formats such as Excel, PDF, or Markdown for easy sharing and integration into existing project management tools (like Jira or Azure DevOps).
