# SQL Chatbot - Natural Language Database Interface

A fullstack web application that converts natural language queries to SQL and executes them against your MySQL database. Features a ChatGPT-like UI with CSV/Excel file upload capabilities.

## 🎯 Features

- **Natural Language to SQL**: Convert plain English questions to SQL queries using local LLM (Ollama)
- **File Upload**: Upload CSV or Excel files to automatically create database tables
- **Chat Interface**: ChatGPT-like UI for intuitive interaction
- **Query Display**: See the generated SQL query for every request
- **Results Visualization**: View query results in formatted tables
- **Multi-Session Support**: Manage multiple chat sessions with different datasets
- **Local Execution**: Runs entirely on your machine - no cloud dependencies

## 🛠️ Tech Stack

- **Frontend**: React 18, Axios, CSS3
- **Backend**: Python Flask, MySQL Connector
- **Database**: MySQL Server (local)
- **LLM**: Ollama (local LLM inference engine)
- **NLP**: Local language models via Ollama

## 📋 Prerequisites

Before you begin, ensure you have installed:

1. **Node.js** (v14 or higher): https://nodejs.org/
2. **Python** (v3.8 or higher): https://www.python.org/
3. **MySQL Server**: https://dev.mysql.com/downloads/mysql/
4. **Ollama**: https://ollama.ai/ (for local LLM support)

## 🚀 Setup & Installation

### Step 1: Install Ollama and Download a Model

1. Install Ollama from https://ollama.ai/
2. Run Ollama and download the Mistral model:
   ```bash
   ollama pull mistral
   ```
3. Start Ollama service (it runs on `http://localhost:11434` by default)

### Step 2: Setup Backend

1. Navigate to the backend folder:
   ```bash
   cd backend
   ```

2. Create a `.env` file from the example:
   ```bash
   copy .env.example .env
   ```

3. Edit `.env` with your MySQL credentials:
   ```
   MYSQL_HOST=localhost
   MYSQL_USER=root
   MYSQL_PASSWORD=your_mysql_password
   MYSQL_PORT=3306
   OLLAMA_URL=http://localhost:11434
   OLLAMA_MODEL=mistral
   ```

4. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Start the Flask backend:
   ```bash
   python app.py
   ```
   The backend will run on `http://localhost:5000`

### Step 3: Setup Frontend

1. In a new terminal, navigate to the frontend folder:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start the React development server:
   ```bash
   npm start
   ```
   The frontend will open on `http://localhost:3000`

## 📖 Usage Guide

### 1. **Create a New Session**
   - Click "New Chat" in the sidebar to create a new conversation session
   - Each session gets its own isolated database

### 2. **Upload Data**
   - Click the **+** button in the chat input area
   - Select a CSV or Excel file
   - The system will automatically create a table in your MySQL database
   - You can filter by table at the top of the chat

### 3. **Ask Questions**
   - Type your question in natural language
   - Examples:
     - "Show me all customers from New York"
     - "What is the average salary in the sales department?"
     - "Count how many orders were placed in December"
   
### 4. **View Results**
   - The system displays:
     - The generated SQL query
     - Query results in a formatted table
     - Row count and pagination indicators

### 5. **Manage Multiple Files**
   - Upload multiple CSV/Excel files to the same session
   - Use the table dropdown to switch between tables
   - Ask queries about any table in your session

## 🔄 Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    React Frontend                        │
│           (ChatGPT-like UI on port 3000)               │
└────────────────────────┬────────────────────────────────┘
                        │
                   HTTP/REST
                        │
┌────────────────────────▼────────────────────────────────┐
│                 Flask Backend                           │
│              (API Server on port 5000)                 │
│  - File Upload Handler                                │
│  - Natural Language Processing                        │
│  - SQL Query Validator & Executor                     │
│  - Session Management                                 │
└────────────┬──────────────────────┬────────────────────┘
             │                      │
         Database API          LLM API
             │                  │
    ┌────────▼──────┐   ┌──────▼─────────┐
    │ MySQL Server  │   │ Ollama (Local) │
    │  (localhost)  │   │ Port 11434     │
    └───────────────┘   └────────────────┘
```

## 🔐 Security Notes

- Only SELECT queries are allowed (no DELETE, DROP, ALTER)
- Files are uploaded to a temporary folder and immediately processed
- Session data is stored in-memory (resets when backend restarts)
- For production use:
  - Use environment variables for credentials
  - Implement database authentication tokens
  - Add request rate limiting
  - Store sessions in persistent database
  - Add user authentication

## 🐛 Troubleshooting

### **Backend won't start**
```bash
# Make sure MySQL is running:
mysql -u root -p

# Check Flask version:
pip show Flask

# Clear Python cache:
del /s __pycache__
```

### **Frontend can't connect to backend**
- Ensure backend is running on port 5000
- Check CORS is enabled in Flask (it is by default)
- Open browser console (F12) to see detailed errors

### **Ollama connection fails**
```bash
# Ensure Ollama is running and accessible:
curl http://localhost:11434/api/tags

# If not working, restart Ollama:
ollama serve
```

### **CSV/Excel upload fails**
- Ensure column names don't have special characters
- File should be less than 16MB
- Supported formats: .csv, .xlsx, .xls

### **No results from queries**
- Check if the correct table is selected
- Verify data was imported correctly
- Check backend logs for SQL errors

## 📚 Example Workflow

1. **Start Services**:
   ```bash
   # Terminal 1: Ollama
   ollama serve
   
   # Terminal 2: Backend
   cd backend && python app.py
   
   # Terminal 3: Frontend
   cd frontend && npm start
   ```

2. **Load Data**:
   - Create a CSV file with sample data
   - Upload it via the + button

3. **Query Data**:
   - Ask natural language questions
   - See generated SQL
   - View results

## 📝 API Endpoints

### Sessions
- `POST /api/sessions` - Create new session
- `GET /api/sessions/<session_id>` - Get session details

### File Operations
- `POST /api/upload` - Upload and import CSV/Excel file

### Queries
- `POST /api/chat` - Convert NL to SQL and execute
- `POST /api/query` - Execute custom SQL query

### Utilities
- `GET /api/health` - Health check
- `GET /api/test-connection` - Test database connection

## 🎨 Customization

### Change LLM Model
Edit `backend/.env`:
```
OLLAMA_MODEL=neural-chat  # or any other Ollama model
```

### Customize CSS
Edit `frontend/src/index.css` to change colors and styles

### Modify SQL Query Limits
Edit `backend/nlp_to_sql.py` to add custom query rules

## 🚢 Production Deployment

For production use:
1. Use proper database sessions (Redis/Database)
2. Add authentication layer
3. Implement request logging and monitoring
4. Use environment-based configuration
5. Deploy with proper WSGI server (Gunicorn)
6. Use containerization (Docker)
7. Implement rate limiting and caching

## 📄 License

MIT License - feel free to use for personal projects

## 🤝 Support

If you encounter issues:
1. Check the troubleshooting section
2. Verify all services are running
3. Check backend logs for errors
4. Ensure MySQL credentials are correct

---

**Happy querying! 🎉**
