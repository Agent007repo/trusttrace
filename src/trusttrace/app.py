"""Loopback-only mock demo. No remote APIs, credentials or real company data."""

from dataclasses import asdict

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from trusttrace.runtime import (
    Passage,
    ReviewQueue,
    explanation,
    mock_generate,
    retrieve,
    validate_suggestion,
)

app = FastAPI(title="TrustTrace synthetic demo")
queue = ReviewQueue()
passages = [
    Passage(
        "synthetic-1",
        "Shipment packages must match the packing list.",
        "Original synthetic case, not a regulation",
        "demo",
        "synthetic",
    )
]


class Query(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@app.get("/", response_class=HTMLResponse)
def index() -> str:
    return """<!doctype html><html lang='en'><meta charset='utf-8'><title>TrustTrace demo</title>
    <style>body{font:18px system-ui;max-width:800px;margin:60px auto;padding:20px}textarea,button{font:inherit;padding:12px}pre{white-space:pre-wrap}</style>
    <h1>TrustTrace synthetic demo</h1><p>One demo tenant. No authentication, legal advice or customs submission. Answers always require review.</p>
    <label>Question about the synthetic shipment<br><textarea id='q'>shipment packages</textarea></label><br><button id='ask'>Retrieve and queue</button><pre id='out'></pre>
    <script>document.getElementById('ask').onclick=async()=>{const r=await fetch('/ask',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:document.getElementById('q').value})});document.getElementById('out').textContent=JSON.stringify(await r.json(),null,2)}</script></html>"""


@app.post("/ask")
def ask(query: Query) -> dict[str, object]:
    found = retrieve(query.text, passages, "demo")
    if not found:
        raise HTTPException(422, "No supporting synthetic passage; abstained")
    suggestion = mock_generate(found)
    validate_suggestion(suggestion, found)
    item = queue.enqueue("demo", suggestion)
    return {"review_item": asdict(item), "explanation": explanation(item)}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": "synthetic-mock"}
