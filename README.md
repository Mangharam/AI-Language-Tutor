# AI Language Tutor

## Day 1 - Text chat with grammar correction

### Run the backend
    cd backend
    python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
    pip install -r requirements.txt
    uvicorn main:app --reload --port 8000

The first request downloads the grammar model (~900 MB), so it is slow once.

### Run the frontend
    cd frontend
    npm install
    npm run dev

Open http://localhost:5173 and try: "She go to school yesterday."

### Day 1 checklist
- [ ] Backend health check works: http://localhost:8000/api/health
- [ ] A wrong sentence returns a correction and a list of changes
- [ ] A correct sentence returns a follow-up question
