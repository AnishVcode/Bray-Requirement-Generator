# Requirement Generator

An advanced, GenAI-powered engineering assistant designed to automate software documentation. It intelligently scans codebases, processes them into semantic embeddings, and generates detailed functional requirements, API specifications, and test cases.

## Project Structure
This is a monorepo consisting of two main components:
- `backend/`: FastAPI Python server that handles code parsing, Azure AI integrations, and generation logic.
- `frontend/`: React + Vite client providing a rich UI, dashboard, and interactive codebase chat.

---

## Prerequisites

Before you begin, ensure you have the following installed:
- **Node.js** (v18 or higher)
- **Python** (v3.11 or higher)
- **Git**

---

## 1. Backend Setup

The backend handles all the AI processing and codebase analysis.

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # On macOS/Linux
   python3 -m venv venv
   source venv/bin/activate

   # On Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install the dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Environment Variables**:
   Copy the example environment file and fill in your required API keys (e.g., Azure OpenAI credentials).
   ```bash
   cp .env.example .env
   ```
   *(Edit `.env` to include your actual API keys before running the server).*

5. **Start the Backend Server**:
   ```bash
   uvicorn app.main:app --port 8000 --reload
   ```
   The backend will now be running at `http://127.0.0.1:8000`.

---

## 2. Frontend Setup

The frontend provides the interactive dashboard to upload codebases and view the generated requirements.

1. **Open a new terminal window** and navigate to the frontend directory from the project root:
   ```bash
   cd frontend
   ```

2. **Install Node modules**:
   ```bash
   npm install
   ```

3. **Start the Development Server**:
   ```bash
   npm run dev
   ```
   The frontend will start up and should be accessible at `http://localhost:3001/` (or the port specified in your terminal).

---

## Usage
1. Make sure **both** the backend and frontend servers are running concurrently in separate terminal windows.
2. Open `http://localhost:3001/` in your browser.
3. Provide a GitHub repository link or upload a `.zip` file of your codebase.
4. Click **Analyze Repository** to let the AI process your code and generate the required documentation!
