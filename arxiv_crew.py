import warnings
warnings.filterwarnings('ignore')

import os, json, re
import argparse
from typing import Type, List
from datetime import datetime, timedelta
import time
import arxiv
import litellm
from pydantic import BaseModel, Field
from crewai import Agent, Task, Crew, LLM
from crewai.tools import BaseTool
from pydantic import BaseModel
import ast

# Fix LiteLLM param check spam
litellm.get_supported_params = lambda *args, **kwargs: {}

# --- CLI parsing ---
parser = argparse.ArgumentParser(description="Fetch and summarize top AI arXiv papers.")
parser.add_argument("--date", type=str, required=True, help="Target date in YYYY-MM-DD format")
parser.add_argument("--output", type=str, default="ai_papers_report.html", help="Output HTML file path")
args = parser.parse_args()

# --- LLM config for Ollama ---
llm = LLM(
    model="llama3",
    base_url="http://localhost:11434",
    api_key="ollama",
    temperature=0.7,
    max_tokens=2048,
    custom_llm_provider="ollama"
)

# --- Arxiv Tool ---
class FetchArxivPapersInput(BaseModel):
    target_date: str = Field(..., description="Date in YYYY-MM-DD")

class FetchArxivPapersTool(BaseTool):
    name: str = "fetch_arxiv_papers"
    description: str = "Fetch top 3 AI papers from arXiv submitted on a given date"
    args_schema: Type[BaseModel] = FetchArxivPapersInput

    def _run(self, target_date: str) -> List[dict]:
        target_dt = datetime.strptime(target_date, "%Y-%m-%d")
        start_date = target_dt.strftime("%Y%m%d%H%M")
        end_date = (target_dt + timedelta(days=1)).strftime("%Y%m%d%H%M")
        categories = ["cs.AI"]
        client = arxiv.Client(page_size=25, delay_seconds=2)
        papers = []

        for cat in categories:
            search_query = f"cat:{cat} AND submittedDate:[{start_date} TO {end_date}]"
            search = arxiv.Search(query=search_query, sort_by=arxiv.SortCriterion.SubmittedDate, max_results=None)
            for i, result in enumerate(client.results(search)):
                if i >= 3: break
                papers.append({
                    "title": result.title,
                    "authors": [a.name for a in result.authors],
                    "summary": result.summary,
                    "url": result.entry_id
                })
        return papers

tool = FetchArxivPapersTool()

# --- Agent ---
researcher = Agent(
    role="AI Researcher",
    goal="Analyze and summarize top AI papers from arXiv.",
    backstory="A seasoned researcher with expertise in understanding research papers and formatting summaries.",
    verbose=True,
    tools=[tool],
    llm=llm
)

class PaperOutput(BaseModel):
    title: str
    authors: list[str]
    summary: str
    url: str

# --- Task ---
task = Task(
    description=(
        f"Use the fetch_arxiv_papers tool to get the top 3 papers from arXiv published on {args.date}. "
        f"For each paper, return a list in the format of PaperOutput, with fields: title, authors, summary, and url."
    ),
    expected_output="List of PaperOutput models describing each paper.",
    output_pydantic_schema=List[PaperOutput],
    agent=researcher
)

# --- Run Crew ---
crew = Crew(agents=[researcher], tasks=[task], verbose=True)
crew_output = crew.kickoff()
task_output = crew_output.tasks_output[0]

import json, re

raw_data = task_output.raw
print(f"\nTony raw data: \n\n{raw_data}\n\n")
raw = raw_data.strip()
# ✅ Loại bỏ code block markdown nếu có
if raw.startswith("```") and raw.endswith("```"):
    raw = raw.strip("```").strip()

# ✅ Thay thế dấu nháy đơn bằng dấu nháy kép một cách an toàn
try:
    # Nếu JSON chuẩn
    papers = json.loads(raw)
except json.JSONDecodeError:
    # Chuyển nháy đơn sang kép nếu cần
    fixed_raw = re.sub(r"'", '"', raw)
    try:
        papers = json.loads(fixed_raw)
    except Exception as e:
        print("❌ Still failed to parse JSON:", e)
        papers = []


html_rows = ""

for paper in papers:
    if isinstance(paper, str):
        try:
            paper = ast.literal_eval(paper)
        except Exception:
            continue

    if not isinstance(paper, dict):
        continue

    title = paper.get("title", "N/A")
    authors = ", ".join(paper.get("authors", []))
    abstract = paper.get("summary", "No summary available")
    link = paper.get("url", "#")

    html_rows += f"""
    <tr>
        <td><a href=\"{link}\" target=\"_blank\">{title}</a></td>
        <td>{authors}</td>
        <td>{abstract}</td>
    </tr>
    """

html_content = f"""
<html>
<head>
    <meta charset=\"UTF-8\">
    <title>AI Research Papers on {args.date}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        a {{ color: #007acc; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <h2>Top AI Research Papers from arXiv on {args.date}</h2>
    <table>
        <tr>
            <th>Title</th>
            <th>Authors</th>
            <th>Abstract</th>
        </tr>
        {html_rows}
    </table>
</body>
</html>
"""

with open(args.output, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"\n✅ Report successfully saved to: {args.output}")

