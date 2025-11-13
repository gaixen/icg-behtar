import os
import sys
import json
import argparse
import logging
import subprocess
import re
from typing import List, Dict, Any, Union
import importlib.util
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JSONUtils:
    @staticmethod
    def sanitize(text: str) -> str:
        t = re.sub(r"/\*[\s\S]*?\*/", "", text)
        t = re.sub(r"//.*?$", "", t, flags=re.MULTILINE)
        return t

    @staticmethod
    def extract_object(text: str) -> Union[dict, None]:
        m = re.search(r"(\{[\s\S]*\})", text)
        if not m:
            return None
        s = m.group(1)
        try:
            return json.loads(s)
        except Exception:
            s2 = re.sub(r",\s*}", "}", s)
            s2 = re.sub(r",\s*]", "]", s2)
            try:
                return json.loads(s2)
            except Exception:
                return None

class ChatLoader:
    @staticmethod
    def load(input_src: Union[str, dict, list]) -> List[Dict[str, str]]:
        if isinstance(input_src, (dict, list)):
            data = input_src
        else:
            with open(input_src, "r", encoding="utf-8") as fh:
                data = json.load(fh)
        if isinstance(data, dict):
            return [data]
        if isinstance(data, list):
            return data
        raise ValueError("Unsupported chat JSON shape")

class RubricLoader:
    @staticmethod
    def load(rubric_src: Union[str, dict]) -> Dict[str, str]:
        if isinstance(rubric_src, dict):
            return rubric_src
        p = str(rubric_src)
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as fh:
                raw = fh.read().strip()
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {"rubric_1": raw}
        else:
            s = p.strip()
            try:
                parsed = json.loads(s)
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                return {"rubric_1": s}

class JudgesRepository:
    def __init__(self) -> None:
        self.module = None
        jp = Path.cwd() / "Evaluation-Methods" / "judges.py"
        if jp.exists():
            try:
                spec = importlib.util.spec_from_file_location("judges", str(jp))
                m = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(m)  # type: ignore
                self.module = m
            except Exception:
                self.module = None
        self.key_map = {
            "empathy": "empathy_prompt_template",
            "agenda_setting": "agenda_Setting_prompt_template",
            "helpfulness": "helpfulness_prompt_template",
            "collaboration": "collaboration_prompt_template",
            "goals_topics": "goals_prompt_template",
            "guided_discovery": "guilded_discovery_prompt_template",
            "safety": "safety_prompt_template",
            "microaggression": "microaggregation_prompt_template",
        }

    def get_template(self, rubric_key: str) -> Union[str, None]:
        if not self.module:
            return None
        name = self.key_map.get(rubric_key)
        if not name:
            return None
        return getattr(self.module, name, None)

    def is_judges_key(self, rubric_key: str) -> bool:
        return rubric_key in self.key_map

class FirecrawlMCP:
    def __init__(self, timeout: int = 10) -> None:
        self.env = os.environ.copy()
        self.timeout = timeout

    def _candidates(self) -> List[List[str]]:
        cmds: List[List[str]] = []
        local = Path.cwd() / "node_modules" / ".bin" / ("firecrawl-mcp.cmd" if os.name == "nt" else "firecrawl-mcp")
        if local.exists():
            cmds.append([str(local)])
        if os.name == "nt":
            cmds.append(["npx.cmd", "firecrawl-mcp"])
            cmds.append(["firecrawl-mcp.cmd"])
        cmds.append(["npx", "firecrawl-mcp"])
        cmds.append(["firecrawl-mcp"])
        return cmds

    def fetch(self, query: str, max_results: int = 5) -> List[str]:
        for base in self._candidates():
            cmd = base + ["--query", query, "--json"]
            try:
                proc = subprocess.run(cmd, capture_output=True, text=True, check=False, env=self.env, timeout=self.timeout)
            except FileNotFoundError:
                continue
            except subprocess.TimeoutExpired:
                continue
            if proc.returncode != 0 or not proc.stdout:
                continue
            raw = proc.stdout
            try:
                data = json.loads(raw)
            except Exception:
                m = re.search(r"(\{.*\}|\[.*\])", raw, re.S)
                if not m:
                    continue
                try:
                    data = json.loads(m.group(1))
                except Exception:
                    continue
            out: List[str] = []
            if isinstance(data, dict):
                for key in ("results", "items", "documents"):
                    if key in data and isinstance(data[key], list):
                        for item in data[key][:max_results]:
                            if isinstance(item, dict):
                                txt = item.get("text") or item.get("snippet") or item.get("content") or item.get("summary")
                                if txt:
                                    out.append(txt)
                            elif isinstance(item, str):
                                out.append(item)
                        if out:
                            return out[:max_results]
                for v in data.values():
                    if isinstance(v, str):
                        out.append(v)
            elif isinstance(data, list):
                for item in data[:max_results]:
                    if isinstance(item, dict):
                        txt = item.get("text") or item.get("snippet") or item.get("content") or item.get("summary")
                        if txt:
                            out.append(txt)
                    elif isinstance(item, str):
                        out.append(item)
            if out:
                return out[:max_results]
        return []

class OpenAIClient:
    def chat(self, system: str, user: str, model: str, max_tokens: int) -> str:
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY not set")
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                temperature=0.0,
                max_tokens=max_tokens,
            )
            assistant_text = None
            try:
                choice0 = resp.choices[0]
                msg = getattr(choice0, "message", None) if not isinstance(choice0, dict) else choice0.get("message")
                if msg is None:
                    assistant_text = getattr(choice0, "text", None) or (choice0.get("text") if isinstance(choice0, dict) else None)
                else:
                    content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", None)
                    if isinstance(content, list) and len(content) > 0:
                        first = content[0]
                        if isinstance(first, dict):
                            assistant_text = first.get("text") or first.get("content")
                        elif isinstance(first, str):
                            assistant_text = first
                    elif isinstance(content, str):
                        assistant_text = content
            except Exception:
                assistant_text = None
            if not assistant_text:
                try:
                    as_str = json.dumps(resp, default=lambda o: getattr(o, "__dict__", str(o)))
                except Exception:
                    as_str = str(resp)
                parsed = JSONUtils.extract_object(as_str)
                if isinstance(parsed, dict):
                    assistant_text = json.dumps(parsed)
                else:
                    assistant_text = as_str
            return str(assistant_text).strip()
        except Exception:
            try:
                import openai
                openai.api_key = api_key
                resp = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.0,
                    max_tokens=max_tokens,
                )
                try:
                    return resp.choices[0].message.content.strip()
                except Exception:
                    return str(resp)
            except Exception:
                raise RuntimeError("OpenAI call failed")

class Evaluator:
    def __init__(self, mcp: FirecrawlMCP, judges: JudgesRepository, llm: OpenAIClient) -> None:
        self.mcp = mcp
        self.judges = judges
        self.llm = llm

    @staticmethod
    def build_chat_context(exchanges: List[Dict[str, str]]) -> str:
        parts = []
        for i, ex in enumerate(exchanges, start=1):
            p = ex.get("patient", "").strip()
            t = ex.get("therapist", "").strip()
            parts.append(f"Exchange {i} - Patient: {p}")
            parts.append(f"Exchange {i} - Therapist: {t}")
        return "\n".join(parts)

    def evaluate(self, chats: Union[str, dict, list], rubric_src: Union[str, dict], use_firecrawl: bool, model: str, max_web_snippets: int = 5, max_tokens: int = 1500) -> Dict[str, Any]:
        exchanges = ChatLoader.load(chats)
        rubrics = RubricLoader.load(rubric_src)
        chat_context = self.build_chat_context(exchanges)
        scores_out: Dict[str, float] = {}
        details_out: Dict[str, Any] = {}
        for rk, rtext in rubrics.items():
            rk_lookup = "helpfulness" if rk == "usefulness" else rk
            template_text = self.judges.get_template(rk_lookup)
            if template_text and "{file_path}" in template_text:
                prompt_body = template_text.replace("{file_path}", chat_context)
            else:
                prompt_body = (
                    f"You are an expert clinical evaluator.\nRubric ({rk}): {rtext}\n\n"
                    f"Conversation:\n{chat_context}\n\n"
                    "Respond with a single JSON object including at least the score for this rubric and a short rationale."
                )
            web_context_r: List[str] = []
            if use_firecrawl:
                q = f"{rk} evaluation references: " + " ".join((ex.get("patient", "") for ex in exchanges))[:800]
                try:
                    web_context_r = self.mcp.fetch(q, max_results=max_web_snippets)
                except Exception:
                    web_context_r = []
            if web_context_r:
                prompt_body += "\n\nWeb references (for justification):\n" + "\n\n".join(web_context_r)
                prompt_body += "\n\nUse the provided web references to support and cite any factual claims in your rationale."
            system_msg = (
                "You are an expert clinical evaluator. Return ONLY a single JSON object for the requested rubric. "
                "Include numeric score and a concise rationale. Include any citations derived from the provided web references."
            )
            try:
                assistant_text = self.llm.chat(system_msg, prompt_body, model=model, max_tokens=max_tokens)
            except Exception as e:
                scores_out[rk] = 0
                details_out[rk] = {"error": str(e)}
                continue
            parsed = None
            for candidate in (assistant_text, JSONUtils.sanitize(assistant_text)):
                try:
                    parsed = json.loads(candidate)
                    break
                except Exception:
                    pass
            if parsed is None:
                parsed = JSONUtils.extract_object(assistant_text)
            score_val = None
            rationale_val = None
            citations_val = None
            if isinstance(parsed, dict):
                keys = [f"{rk}_score", "helpfulness_score", "empathy_score", "safety_score", "collaboration_score", "agenda_setting_score", "goals_topics_score", "guided_discovery_score", "microaggression_score", "score"]
                for k in keys:
                    if k in parsed:
                        score_val = parsed.get(k)
                        break
                if score_val is None:
                    for v in parsed.values():
                        if isinstance(v, (int, float)):
                            score_val = v
                            break
                for rk_key in ("rationale", "explanation", "reasoning"):
                    if rk_key in parsed:
                        rationale_val = parsed.get(rk_key)
                        break
                if "citations" in parsed and isinstance(parsed.get("citations"), list):
                    citations_val = parsed.get("citations")
            normalized = 0
            try:
                if isinstance(score_val, (int, float)):
                    normalized = score_val
                elif isinstance(score_val, str):
                    normalized = float(score_val) if ('.' in score_val or 'e' in score_val.lower()) else int(score_val)
                elif score_val is None:
                    normalized = 0
                else:
                    normalized = float(score_val)
            except Exception:
                normalized = 0
            lo, hi = (0, 3) if self.judges.is_judges_key(rk_lookup) else (0, 5)
            normalized = max(lo, min(hi, normalized))
            scores_out[rk] = normalized
            details_out[rk] = {
                "raw_response": assistant_text,
                "parsed": parsed,
                "rationale": rationale_val,
                "citations": citations_val,
                "web_references_used": web_context_r,
            }
        
        details_out['conversation'] = exchanges
        return {"scores": scores_out, "details": details_out}

def main():
    parser = argparse.ArgumentParser(description="Evaluate therapy chat JSON against rubrics, optional Firecrawl augmentation.")
    parser.add_argument("--input", "-i", required=True, help="Path to chat JSON file (or pass '-' to read stdin).")
    parser.add_argument("--rubric", "-r", required=True, help="Path to rubric JSON/text OR a JSON string OR a plain rubric text.")
    parser.add_argument("--output", "-o", default="evaluation_output.json", help="Output JSON file path.")
    parser.add_argument("--no-firecrawl", action="store_true", help="Disable Firecrawl augmentation.")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use (requires OPENAI_API_KEY).")
    parser.add_argument("--details-file", "-d", default=None, help="Optional path to write detailed evaluation output (rationales, citations).")
    parser.add_argument("--rubrics-include", default=None, help="Comma-separated rubric keys to evaluate (filters the rubric file).")
    parser.add_argument("--max-web-snippets", type=int, default=5, help="Max web snippets to include per rubric when using Firecrawl.")
    parser.add_argument("--mcp-timeout", type=int, default=10, help="Timeout in seconds for each Firecrawl command attempt.")
    parser.add_argument("--max-tokens", type=int, default=1500, help="Max tokens for the model response per rubric.")
    parser.add_argument("--fast", action="store_true", help="Use faster defaults (smaller model and fewer tokens).")
    args = parser.parse_args()
    if args.input == "-":
        chats = json.load(sys.stdin)
    else:
        chats = args.input
    model = args.model
    max_tokens = args.max_tokens
    if args.fast:
        if model == "gpt-4":
            model = "gpt-4o-mini"
        if max_tokens > 900:
            max_tokens = 900
    evaluator = Evaluator(FirecrawlMCP(timeout=args.mcp_timeout), JudgesRepository(), OpenAIClient())
    rubric_arg: Union[str, dict] = args.rubric
    if args.rubrics_include:
        include = [k.strip() for k in args.rubrics_include.split(",") if k.strip()]
        try:
            loaded = RubricLoader.load(args.rubric)
            filtered = {k: v for k, v in loaded.items() if k in include}
            if filtered:
                rubric_arg = filtered
        except Exception:
            pass
    try:
        result = evaluator.evaluate(
            chats,
            rubric_arg,
            use_firecrawl=(not args.no_firecrawl),
            model=model,
            max_web_snippets=args.max_web_snippets,
            max_tokens=max_tokens,
        )
    except Exception as e:
        logger.error("Evaluation failed: %s", e)
        sys.exit(2)
    scores_only = result.get("scores") if isinstance(result, dict) and "scores" in result else result
    with open(args.output, "w", encoding="utf-8") as fh:
        json.dump(scores_only, fh, indent=2)
    print(f"Wrote scores to {args.output}")
    if args.details_file:
        details = result.get("details") if isinstance(result, dict) else None
        try:
            with open(args.details_file, "w", encoding="utf-8") as dfh:
                json.dump(details, dfh, indent=2)
            print(f"Wrote details to {args.details_file}")
        except Exception as e:
            logger.error("Failed to write details file %s: %s", args.details_file, e)

if __name__ == "__main__":
    main()
