import os
import io
import json
import base64
import random
import asyncio
import urllib.parse
from datetime import datetime, timedelta
from typing import Union, List, Optional
from PIL import Image

from google import genai
from google.genai import types
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Load .env from parent directory (project root)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="IntelliBuy API")

# Shared Gemini client — created once at startup to avoid per-request overhead
_GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
_gemini_client: Optional[genai.Client] = genai.Client(api_key=_GEMINI_API_KEY) if _GEMINI_API_KEY else None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

dist_dir = os.path.join(os.path.dirname(__file__), "..", "dist")
if os.path.exists(dist_dir):
    assets_dir = os.path.join(dist_dir, "assets")
    if os.path.exists(assets_dir):
        app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# ── Helpers ────────────────────────────────────────────────────────────────────

FIXED_PLATFORMS = [
    {"name": "Amazon",   "search_url": "https://www.amazon.com/s?k={q}"},
    {"name": "Best Buy", "search_url": "https://www.bestbuy.com/site/searchpage.jsp?st={q}"},
    {"name": "Walmart",  "search_url": "https://www.walmart.com/search?q={q}"},
    {"name": "Target",   "search_url": "https://www.target.com/s?searchTerm={q}"},
]


def build_platform_url(platform_name: str, product_name: str) -> str:
    q = urllib.parse.quote_plus(product_name)
    for p in FIXED_PLATFORMS:
        if p["name"].lower() == platform_name.lower():
            return p["search_url"].format(q=q)
    return f"https://www.google.com/search?q={q}+buy+site:{platform_name.lower().replace(' ', '')}.com"


def generate_realistic_price_history(base_price: float, product_name: str):
    seed = sum(ord(c) for c in product_name.lower())
    rng = random.Random(seed)
    today = datetime.today()
    months, prices = [], []

    current = base_price * rng.uniform(1.12, 1.30)

    for i in range(11, 0, -1):
        month_dt = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        label = month_dt.strftime("%Y-%m")
        month_num = month_dt.month

        seasonal = 0.0
        if month_num == 11:   seasonal =  base_price * 0.06
        elif month_num == 12: seasonal =  base_price * 0.04
        elif month_num == 7:  seasonal = -base_price * 0.05
        elif month_num == 8:  seasonal = -base_price * 0.07

        drift = (base_price - current) * 0.20
        noise = rng.uniform(-base_price * 0.04, base_price * 0.04)
        current = round(max(base_price * 0.70, min(base_price * 1.40, current + drift + seasonal + noise)), 2)
        months.append(label)
        prices.append(current)

    months.append(today.replace(day=1).strftime("%Y-%m"))
    prices.append(round(base_price, 2))

    price_range = max(prices) - min(prices)
    if price_range < base_price * 0.08:
        prices[0] = round(base_price * rng.uniform(1.15, 1.30), 2)

    return [{"date": m, "price": p} for m, p in zip(months, prices)]


BASE_PROMPT = """Analyze the product based on the provided input (image, text, or both) and provide a comprehensive review in JSON format matching exactly this structure:
{
    "product_name": "Name of the product",
    "category": "Product category",
    "specific_answer": "Directly answer the user's specific request or question. If no specific question was asked, briefly summarize the product's value proposition.",
    "build_and_features": {
        "build_quality": "High-level summary of construction quality",
        "materials": ["Material 1", "Material 2"],
        "special_details": "Unique features or technical highlights"
    },
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["Con 1", "Con 2"],
    "rating": 4.5,
    "worth_buying": true,
    "average_price": 199.99,
    "reviews": [
        {"user": "User1", "platform": "Amazon", "text": "Detailed review text.", "rating": 5},
        {"user": "User2", "platform": "BestBuy", "text": "Detailed review text.", "rating": 4}
    ],
    "platforms": [
        {"name": "Amazon",   "trust_score": 9.5, "price": 199.99},
        {"name": "Best Buy", "trust_score": 9.0, "price": 199.99},
        {"name": "Walmart",  "trust_score": 8.5, "price": 189.99},
        {"name": "Target",   "trust_score": 8.8, "price": 195.99}
    ],
    "price_history": [{"date": "2023-01", "price": 249.99}],
    "frequently_bought_together": [{"name": "Accessory A", "reason": "Protects the product"}],
    "better_alternatives": [
        {
            "name": "Alternative Name",
            "brand": "Brand Name",
            "brand_domain": "brand.com",
            "price": 179.99,
            "url": "https://www.amazon.com/s?k=alternative+name",
            "reason": "Direct comparison or value proposition."
        }
    ],
    "review_authenticity": {
        "genuine_count": 3,
        "fake_count": 1,
        "confidence_score": 75,
        "summary": "Most reviews appear genuine; one review shows signs of being fabricated.",
        "key_signals": [
            "Consistent sentiment across multiple platforms",
            "High percentage of verified purchase indicators",
            "Natural language variations in positive feedback",
            "Detection of suspicious templated language in 1 review"
        ],
        "per_review": [
            {"user": "User1", "platform": "Amazon", "verdict": "genuine", "text": "Great product, works as expected.", "reason": "Specific product details mentioned, balanced tone."},
            {"user": "User2", "platform": "BestBuy", "verdict": "fake", "text": "AMAZING!!! BEST EVER!!!", "reason": "Overly promotional, no critical feedback, suspiciously short."}
        ]
    },
    "is_new_product": true
}

Return ONLY valid JSON.
If an image is provided, use it as the primary source of truth.
If text is provided, determine if it is a follow-up question about the product in the image or a completely NEW product search.
Set "is_new_product" to true if the user is asking about a different product than what is shown/previously discussed, or if no image is provided.
Set "is_new_product" to false if the user is asking a refinement or follow-up question about the product in the image.
For platforms, ALWAYS return EXACTLY these 4 stores: Amazon, Best Buy, Walmart, Target. Do NOT include URLs. Ensure at least 4 reviews. For price_history, search and analyze recent web pricing records for this product over the past 12 months and provide research-grounded monthly historical prices in YYYY-MM format matching exact array format [{"date": "YYYY-MM", "price": 199.99}].
For better_alternatives, provide at least 3 options with brand, brand_domain, price, url, and reason.
For platform names, use standard recognizable names like Amazon, Best Buy, Walmart, Target, eBay, B&H Photo, Newegg, Flipkart, etc.
For review_authenticity, analyze each review and classify as 'genuine' or 'fake' with a reason. Provide genuine_count, fake_count, and confidence_score (0-100)."""


def call_gemini(image_bytes: Optional[bytes], format_str: Optional[str], text_prompt: Optional[str]) -> dict:
    api_key = (os.getenv("GEMINI_API_KEY") or "").strip()
    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="GEMINI_API_KEY environment variable is not configured. Please add GEMINI_API_KEY=your_key to your .env file."
        )

    # Reuse the shared client if key matches, otherwise create a new one
    client = _gemini_client if (_gemini_client and api_key == _GEMINI_API_KEY) else genai.Client(api_key=api_key)
    content_list = []

    if image_bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail((1024, 1024))
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=80)
            image_bytes = buf.getvalue()
            format_str = "jpeg"
        except Exception:
            pass
        mime = f"image/{format_str}" if format_str else "image/jpeg"
        content_list.append(types.Part.from_bytes(data=image_bytes, mime_type=mime))

    final_text = BASE_PROMPT
    if text_prompt:
        final_text = f"USER REQUEST: {text_prompt}\n\nINSTRUCTIONS: {BASE_PROMPT}"
    content_list.append(final_text)

    try:
        response = client.models.generate_content(
            model="gemini-3.5-flash",
            contents=content_list,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                system_instruction="You are a helpful AI product reviewer. Always output valid JSON matching the exact requested JSON schema. Be concise and direct.",
                temperature=0.1,
                max_output_tokens=2000,
            )
        )
        output_text = response.text.strip()
        if output_text.startswith("```json"):
            output_text = output_text[7:]
        elif output_text.startswith("```"):
            output_text = output_text[3:]
        if output_text.endswith("```"):
            output_text = output_text[:-3]

        return json.loads(output_text.strip())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gemini API error: {str(e)}")

def call_groq(image_bytes: Optional[bytes], format_str: Optional[str], text_prompt: Optional[str]) -> dict:
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)
    groq_api_key = (os.getenv("GROQ_API_KEY") or "").strip()
    if not groq_api_key:
        raise ValueError("GROQ_API_KEY is not configured")

    from groq import Groq
    client = Groq(api_key=groq_api_key)

    content_list = []
    if image_bytes:
        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.thumbnail((1024, 1024))
            buf = io.BytesIO()
            img.convert("RGB").save(buf, format="JPEG", quality=80)
            image_bytes = buf.getvalue()
            format_str = "jpeg"
        except Exception:
            pass
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        mime = f"image/{format_str}" if format_str else "image/jpeg"
        content_list.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:{mime};base64,{encoded}"
            }
        })

    final_text = BASE_PROMPT
    if text_prompt:
        final_text = f"USER REQUEST: {text_prompt}\n\nINSTRUCTIONS: {BASE_PROMPT}"
    
    content_list.append({"role": "user", "content": final_text})

    models = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]

    last_err = None
    for model_name in models:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a helpful AI product reviewer. Always output valid JSON matching the exact requested JSON schema."},
                    {"role": "user", "content": final_text}
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=3000
            )
            output_text = response.choices[0].message.content.strip()
            if output_text.startswith("```json"): output_text = output_text[7:]
            elif output_text.startswith("```"): output_text = output_text[3:]
            if output_text.endswith("```"): output_text = output_text[:-3]

            return json.loads(output_text.strip())
        except Exception as e:
            last_err = e
            continue

    raise Exception(f"Groq API error: {str(last_err)}")


def call_llm(image_bytes: Optional[bytes], format_str: Optional[str], text_prompt: Optional[str]) -> dict:
    # 1. Image uploaded: use Gemini Vision (can actually see the image)
    if image_bytes:
        try:
            return call_gemini(image_bytes, format_str, text_prompt)
        except HTTPException:
            raise
        except Exception as e:
            print(f"Gemini Vision failed: {e}")
            if not text_prompt:
                raise HTTPException(
                    status_code=429,
                    detail="Gemini Vision quota exhausted. Please add a product name in the text field and try again."
                )
            image_bytes = None

    # 2. Text-only: use Gemini directly
    try:
        return call_gemini(None, None, text_prompt)
    except Exception as e:
        print(f"Gemini text call failed: {e}")

    raise HTTPException(
        status_code=500,
        detail="Unable to analyze product. Please check your API key or try again shortly."
    )


# ── Route ──────────────────────────────────────────────────────────────────────

@app.post("/api/analyze")
async def analyze(
    prompt: str = Form(default=""),
    image: Optional[UploadFile] = File(default=None),
):
    img_bytes = None
    fmt = None
    if image and image.filename:
        img_bytes = await image.read()
        ext = image.filename.rsplit(".", 1)[-1].lower()
        fmt = "jpeg" if ext == "jpg" else ext

    result = await asyncio.to_thread(call_llm, img_bytes, fmt, prompt or None)

    # Enrich platforms with generated search URLs
    product_name = result.get("product_name", "product")
    for p in result.get("platforms", []):
        p["url"] = build_platform_url(p.get("name", ""), product_name)

    # Preserve Gemini's web-grounded price history; fallback only if empty
    platforms = result.get("platforms", [])
    base_price = 99.99
    if platforms:
        try:
            base_price = float(min(p.get("price", 9999) for p in platforms))
        except Exception:
            pass
    result["average_price"] = base_price
    if not result.get("price_history") or not isinstance(result.get("price_history"), list) or len(result.get("price_history")) < 3:
        result["price_history"] = generate_realistic_price_history(base_price, product_name)

    # Dynamic image sync: Use category placeholder only if no image was uploaded by user
    if not img_bytes:
        category = result.get("category", "product")
        search_term = f"{category},product"
        safe_term = urllib.parse.quote_plus(search_term)
        result["product_image_url"] = f"https://loremflickr.com/800/600/{safe_term}"
    else:
        result["product_image_url"] = None

    return result


if os.path.exists(dist_dir):
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="API endpoint not found")
        file_path = os.path.join(dist_dir, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(dist_dir, "index.html"))

