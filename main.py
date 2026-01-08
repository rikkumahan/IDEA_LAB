import os
import requests
from fastapi import FastAPI
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# This defines what data we expect from the user
class IdeaInput(BaseModel):
    problem: str
    target_user: str
    user_claimed_frequency: str

@app.post("/analyze-idea")
def analyze_idea(data: IdeaInput):
    queries = generate_search_queries(data.problem)

    # 1. Run multiple complaint-related searches
    complaint_results = run_multiple_searches(
        queries["complaint_queries"]
    )

    # 2. Deduplicate
    complaint_results = deduplicate_results(complaint_results)

    # 3. Extract signals
    signals = extract_signals(complaint_results)

    problem_level = classify_problem_level(signals)
    normalized = normalize_signals(signals)

    return {
        "queries_used": queries["complaint_queries"],
        "unique_results_count": len(complaint_results),
        "raw_signals": signals,
        "normalized_signals": normalized,
        "problem_level": problem_level
    }


def generate_search_queries(problem: str):
    complaint_queries = [
        f"{problem} every day",
        f"{problem} wasting time",
        f"frustrating {problem}",
        f"manual {problem}"
    ]

    workaround_queries = [
        f"how to automate {problem}",
        f"{problem} workaround",
        f"{problem} script",
        f"{problem} automation"
    ]

    tool_queries = [
        f"{problem} tool",
        f"{problem} software",
        f"{problem} chrome extension"
    ]

    return {
        "complaint_queries": complaint_queries,
        "workaround_queries": workaround_queries,
        "tool_queries": tool_queries
    }

def serpapi_search(query: str):
    api_key = os.getenv("SERPAPI_KEY")

    params = {
        "engine": "google",
        "q": query,
        "api_key": api_key,
        "google_domain": "google.com",
        "gl": "in",
        "hl": "en",
        "safe": "off",
        "start": "0"
    }

    response = requests.get("https://serpapi.com/search", params=params)

    if response.status_code != 200:
        return {"error": response.text}

    data = response.json()

    results = []

    for item in data.get("organic_results", []):
        results.append({
            "title": item.get("title"),
            "snippet": item.get("snippet"),
            "url": item.get("link")
        })

    return results

WORKAROUND_KEYWORDS = [
    "how to",
    "workaround",
    "automation",
    "script",
    "tool"
]
COMPLAINT_KEYWORDS = [
    "problem",
    "frustrating",
    "wasting time",
    "manual",
    "issue"
]
INTENSITY_KEYWORDS = [
    "urgent",
    "critical",
    "blocking",
    "severe",
    "serious",
    "wasting",
    "costing",
    "unusable",
    "painful",
    "nightmare"
]

def extract_signals(search_results):
    workaround_count = 0
    complaint_count = 0
    intensity_count = 0

    for result in search_results:
        text = (
            (result.get("title") or "") + " " +
            (result.get("snippet") or "")
        ).lower()

        if any(k in text for k in WORKAROUND_KEYWORDS):
            workaround_count += 1

        if any(k in text for k in COMPLAINT_KEYWORDS):
            complaint_count += 1

        if any(k in text for k in INTENSITY_KEYWORDS):
            intensity_count += 1

    return {
        "workaround_count": workaround_count,
        "complaint_count": complaint_count,
        "intensity_count": intensity_count
    }

def run_multiple_searches(queries):
    all_results = []

    for q in queries:
        results = serpapi_search(q)
        if isinstance(results, list):
            all_results.extend(results)

    return all_results

def deduplicate_results(results):
    seen_urls = set()
    unique_results = []

    for r in results:
        url = r.get("url")
        if url and url not in seen_urls:
            seen_urls.add(url)
            unique_results.append(r)

    return unique_results

# Normalizing the count level.
def normalize_level(count):
    if count >= 5:
        return "HIGH"
    elif count >= 2:
        return "MEDIUM"
    else:
        return "LOW"


def normalize_signals(signals):
    return {
        "complaint_level": normalize_level(signals["complaint_count"]),
        "workaround_level": normalize_level(signals["workaround_count"]),
        "intensity_level": normalize_level(signals["intensity_count"])
    }

def classify_problem_level(signals):
    score = (
        3 * signals["intensity_count"] +
        2 * signals["complaint_count"] +
        1 * signals["workaround_count"]
    )

    if score >= 15:
        return "DRASTIC"
    elif score >= 8:
        return "SEVERE"
    elif score >= 4:
        return "MODERATE"
    else:
        return "LOW"
