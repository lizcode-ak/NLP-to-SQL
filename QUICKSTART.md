# Quick Start Guide - SQL Chatbot

## 🎯 5-Minute Setup

### Prerequisites Check
- [ ] MySQL installed and running
- [ ] Python 3.8+ installed: `python --version`
- [ ] Node.js 14+ installed: `node --version`
- [ ] Ollama installed and running

### Step 1: Setup Ollama (2 min)
```bash
# Start Ollama (keep running in background)
ollama serve

# In another terminal, download model
ollama pull mistral
```

### Step 2: Setup Backend (2 min)
```bash
# Navigate to backend
cd backend

# Create .env from template
copy .env.example .env

# Edit .env with your MySQL password
# MYSQL_PASSWORD=your_password_here

# Install Python packages
pip install -r requirements.txt

# Start backend
python app.py
# Backend runs at http://localhost:5000
```

### Step 3: Setup Frontend (1 min)
```bash
# In another terminal, navigate to frontend
cd frontend

# Install and start
npm install
npm start
# Frontend opens at http://localhost:3000
```

## ✅ Verify Everything Works

1. **Backend Health**: Visit http://localhost:5000/api/health
2. **Database Connection**: Visit http://localhost:5000/api/test-connection
3. **Frontend**: Should load at http://localhost:3000

## 🎮 First Test Run

1. Open http://localhost:3000 in your browser
2. Click the **+** button
3. Upload this sample CSV:
   ```
   Name,Age,Department,Salary
   John,28,Sales,50000
   Jane,32,Engineering,75000
   Bob,45,Management,85000
   ```
4. Ask: "Show me all employees in engineering"
5. See the generated SQL and results!

## 📁 Upload Sample CSV

Create `sample_data.csv`:
```csv
Product,Category,Price,Stock,Revenue
Laptop,Electronics,999,15,14985
Mouse,Electronics,25,100,2500
Keyboard,Electronics,75,50,3750
Desk,Furniture,299,20,5980
Chair,Furniture,199,30,5970
```

Upload and try queries like:
- "What products are in stock?"
- "Show me items under $100"
- "What is the total revenue?"

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend won't start | Check MySQL is running, Python version 3.8+, port 5000 free |
| Frontend blank | Check Network tab in DevTools (F12) for backend errors |
| Ollama connection fails | Run `ollama serve` in another terminal |
| File upload fails | Check file is CSV/XLSX, < 16MB, no special chars in headers |
| No SQL results | Select correct table, verify data imported, check backend logs |

## 🚀 Next Steps

1. Experiment with different data formats and questions
2. Understand how NL gets converted to SQL in `backend/nlp_to_sql.py`
3. Customize the UI in `frontend/src/index.css`
4. Add more features to the API
5. Deploy to cloud (see README.md for production notes)

## 📞 Need Help?

- Check backend output for SQL errors
- Browser Developer Tools (F12) for frontend issues
- Verify all services running and accessible
- Run health checks on backend API

---

**Enjoy your SQL Chatbot! 🎉**
