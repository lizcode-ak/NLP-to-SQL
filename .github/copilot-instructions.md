# Copilot Instructions

This is a fullstack SQL Natural Language Interface project combining:
- **Frontend**: React-based ChatGPT-like UI for querying databases
- **Backend**: Python Flask API for NLP-to-SQL conversion and database operations
- **Database**: MySQL with local file import (CSV/Excel)
- **LLM**: Ollama for local natural language to SQL conversion

## Project Structure

```
├── backend/
│   ├── app.py                 # Flask main application
│   ├── config.py              # Configuration management
│   ├── database.py            # MySQL operations
│   ├── nlp_to_sql.py          # NLP to SQL conversion
│   ├── requirements.txt       # Python dependencies
│   ├── .env.example           # Environment variables template
│   └── uploads/              # Temporary file storage
├── frontend/
│   ├── public/
│   │   └── index.html        # HTML entry point
│   ├── src/
│   │   ├── App.jsx           # Main React component
│   │   ├── App.css           # App styles
│   │   ├── index.js          # React entry point
│   │   ├── index.css         # Global styles
│   │   └── components/
│   │       ├── ChatMessage.jsx    # Message display
│   │       ├── ChatInput.jsx      # Input handling
│   │       └── Sidebar.jsx        # Session management
│   └── package.json          # Node dependencies
└── README.md                 # Project documentation
```

## For Copilot

When working with this project:

1. **Backend modifications**: Edit files in `backend/` folder
   - Any NLP logic changes go in `nlp_to_sql.py`
   - Database operations are in `database.py`
   - API endpoints are in `app.py`

2. **Frontend modifications**: Edit files in `frontend/src/` folder
   - Component logic in `src/components/`
   - Styling in `*.css` files
   - Main app logic in `App.jsx`

3. **Configuration**: Use `backend/.env` for environment variables
   - Never commit `.env` with real credentials
   - Use `.env.example` as template

4. **Running the project**:
   - Backend runs on port 5000
   - Frontend runs on port 3000
   - MySQL should be running locally
   - Ollama service should be running on port 11434

5. **Adding features**:
   - Backend API changes: Add endpoint to `app.py` and corresponding handler
   - Frontend UI changes: Create/modify components in `src/components/`
   - Database schema changes: Modify `database.py` methods

## Key Technologies

- **React 18**: Frontend framework
- **Flask**: Python backend framework
- **MySQL**: Database engine
- **Ollama**: Local LLM inference
- **Axios**: HTTP client

## Development Workflow

1. Make code changes
2. Test backend: Verify API endpoints with curl/Postman
3. Test frontend: Check React component rendering
4. Verify database: Ensure MySQL operations work
5. Test LLM integration: Verify Ollama connectivity
