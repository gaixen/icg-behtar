# Therapy Session Evaluator - Complete Setup Guide

## Architecture Overview

The application has three main components:

1. **Frontend (Next.js + React)** - `my-app/` folder
   - Home page: File upload interface
   - Evaluation page: Displays results with animations

2. **Backend (FastAPI)** - `fastapi_server.py`
   - Receives JSON transcripts
   - Calls EVAL.py for evaluation
   - Returns results to frontend

3. **Evaluation Engine (Python)** - `EVAL.py`
   - Uses OpenAI API to evaluate therapy sessions
   - Generates scores for 9 clinical dimensions

## Quick Start

### 1. Install Dependencies

**Frontend (Node.js):**
```powershell
cd ./my-app
npm install
```

**Backend (Python):**
```powershell
pip install -r requirements.txt
```

**Recommended (follow code formatting) from root directory**
```powershell
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

### 2. Setup Environment Variables

Create a `.env` file in root directory:
```
cp .env.example .env
OPENAI_API_KEY=your_actual_openai_api_key_here
```

Or set in PowerShell:
```powershell
$env:OPENAI_API_KEY = "your_actual_openai_api_key_here"
```

### 3. Start the Services

**Terminal 1 - FastAPI Backend:**
```powershell
python fastapi_server.py
```
Server runs on http://localhost:8000

**Terminal 2 - Next.js Frontend:**
```powershell
cd ./my-app
npm run dev
```
- App runs on http://localhost:3000

### 4. Use the Application

1. Go to `http://localhost:3000`
2. You'll see the home page with file upload
3. Upload a JSON file with therapy session transcript
4. Click "Evaluate Session"
5. View detailed evaluation results on the evaluation page

## JSON Input Format

Your transcript JSON should have this structure:

```json
{
  "conversation": [
    {
      "patient": "I have this problem!!",
      "therapist": "Can you tell me more about it?"
    },
    {
      "patient": "I'm feeling anxious about work.",
      "therapist": "Have you tried breathing exercises?"
    }
  ]
}
```

## Evaluation Metrics (9 Dimensions)

The system evaluates on:

1. **Empathy** (0-5) - Therapist empathy and understanding
2. **Usefulness** (0-5) - Actionability of suggestions
3. **Agenda Setting** (0-3) - Session planning and structure
4. **Helpfulness** (0-3) - Clinical appropriateness
5. **Collaboration** (0-3) - Partnership quality
6. **Goals & Topics** (0-3) - Goal alignment
7. **Guided Discovery** (0-3) - Socratic questioning
8. **Safety** (0-3) - Safety protocols
9. **Microaggression** (0-3) - Cultural humility

## Troubleshooting

### FastAPI Server Won't Start
```powershell
# Check if port 8000 is in use
netstat -ano | findstr :8000

# Kill the process using the port (replace PID with actual process ID)
taskkill /PID <PID> /F

# Try again
python fastapi_server.py
```

## Running `EVAL.py` from the root directory

```python
python EVAL.py --input Evaluation-Methods/chats.json --rubric Evaluation-Methods/rubrics.json --no-firecrawl --fast --output evaluation_output.json --details-file evaluation_details.json
```
### Frontend Can't Reach Backend
- Make sure FastAPI server is running (`http://localhost:8000/health` should return `{"status": "ok"}`)
- Check CORS settings in `fastapi_server.py` (currently allows all origins)
- Check browser console for errors (F12 → Console tab)

### OPENAI_API_KEY Not Found
- Ensure you set the environment variable BEFORE starting the server
- In PowerShell: `$env:OPENAI_API_KEY = "your_key"`
- Or create `.env` file and ensure python-dotenv loads it

### File Upload Fails
- Check JSON file format matches the expected structure
- Make sure file is valid JSON (use online JSON validator)
- Check browser console for specific error messages

## File Structure

```
demo/
├── my-app/                    # Next.js Frontend
│   ├── app/
│   │   ├── page.tsx          # Root (redirects to /home)
│   │   ├── home/
│   │   │   └── page.tsx      # Home page with upload
│   │   └── evaluation/
│   │       └── page.tsx      # Evaluation results
│   ├── globals.css           # Tailwind styles
│   ├── package.json
│   └── tailwind.config.js
├── fastapi_server.py         # FastAPI backend server
└── Varun-behtar/
    ├── EVAL.py              # Main evaluation script
    └── Evaluation-Methods/
        ├── requirements.txt
        ├── chats.json
        └── rubrics.json
```

## API Endpoints

### POST `/evaluate`
Evaluate a therapy session

**Request Body:**
```json
{
  "chats": [
    {"patient": "...", "therapist": "..."}
  ],
  "rubric": {
    "empathy": {"title": "Empathy", "maxScore": 5},
    ...
  }
}
```

**Response:**
```json
{
  "details": {
    "empathy": {
      "error" or "score": 4,
      "rationale": "..."
    },
    ...
  },
  "status": "success"
}
```

### GET `/health`
Check server health
```json
{"status": "ok"}
```

## Development Tips

- Frontend hot-reload: Changes in `my-app/app/**` auto-refresh browser
- Backend auto-reload: Modify `fastapi_server.py` and restart server
- Use browser DevTools (F12) to debug frontend issues
- Check terminal output for backend errors

## Next Steps / Enhancements

- [ ] Add file validation and error handling
- [ ] Show evaluation progress/loading state
- [ ] Add export results to PDF
- [ ] Store evaluation history in database
- [ ] Add multiple file batch evaluation
- [ ] Implement user authentication
- [ ] Add evaluation comparison/analytics
- [ ] Deploy to Vercel (frontend) and Render/Railway (backend)

## Support

- Check FastAPI docs: `http://localhost:8000/docs` (when server running)
- Next.js docs: https://nextjs.org/docs
- OpenAI API issues: Ensure API key has billing enabled
