import json
import os
import subprocess
import sys

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class EvaluationRequest(BaseModel):
    chats: list
    rubric: dict


@app.post("/evaluate")
async def evaluate(request: EvaluationRequest):
    """
    Evaluate a therapy session using the EVAL.py script
    """
    try:
        # Create temp files for input data (use current working directory so output is easy to find)
        base_dir = os.getcwd()
        chats_file = os.path.join(base_dir, "chats_temp.json")
        rubric_file = os.path.join(base_dir, "rubrics_temp.json")
        output_file = os.path.join(base_dir, "evaluation_output.json")
        details_file = os.path.join(base_dir, "evaluation_details.json")

        # Write input files
        with open(chats_file, "w") as f:
            json.dump({"conversation": request.chats}, f)

        with open(rubric_file, "w") as f:
            json.dump(request.rubric, f)

        # Get the path to EVAL.py (adjust based on your repo structure)
        eval_script = r"C:\Users\Varun Agrawal\Downloads\demo\Varun-behtar\EVAL.py"

        # Run EVAL.py
        cmd = [
            sys.executable,
            eval_script,
            f"--input={chats_file}",
            f"--rubric={rubric_file}",
            "--no-firecrawl",
            "--fast",
            f"--output={output_file}",
            f"--details-file={details_file}",
            "--model=gpt-3.5-turbo",
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode != 0:
            raise HTTPException(
                status_code=500, detail=f"Evaluation failed: {result.stderr}"
            )

        # Read results
        evaluation_details = None
        if os.path.exists(details_file):
            with open(details_file, "r", encoding="utf-8") as f:
                evaluation_details = json.load(f)

        # Ensure the main output JSON also contains the original input conversation
        # Read output (if any), add `input` field, and write back
        out_data = {}
        if os.path.exists(output_file):
            try:
                with open(output_file, "r", encoding="utf-8") as fo:
                    out_data = json.load(fo)
            except Exception:
                out_data = {}
        # Add the original chats under `input` (preserve existing keys)
        out_data["input"] = {"conversation": request.chats}
        with open(output_file, "w", encoding="utf-8") as fo:
            json.dump(out_data, fo, indent=2)

        # Clean up only the temporary input files, keep output files for inspection
        for file in [chats_file, rubric_file, details_file]:
            if os.path.exists(file):
                try:
                    os.remove(file)
                except Exception:
                    pass

        return {
            "details": evaluation_details,
            "output_file": output_file,
            "status": "success",
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=500, detail="Evaluation timeout")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
