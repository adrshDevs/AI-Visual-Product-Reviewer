import os
import json
import base64
import random
import urllib.parse
from datetime import datetime, timedelta
from typing import Union, List, Optional

import boto3
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, UploadFile
from fastapi.middleware.cors import CORSMiddleware

# Load .env from parent directory (project root)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "..", ".env"))

app = FastAPI(title="AI Visual Product Reviewer API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5176", "http://127.0.0.1:5176"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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


def get_bedrock_client():
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    aws_profile = os.getenv("AWS_PROFILE")

    if aws_profile:
        boto3.setup_default_session(profile_name=aws_profile)

    client_kwargs = {"service_name": "bedrock-runtime", "region_name": aws_region}

    if aws_access_key and aws_secret_key:
        client_kwargs["aws_access_key_id"] = aws_access_key
        client_kwargs["aws_secret_access_key"] = aws_secret_key
        if aws_session_token:
            client_kwargs["aws_session_token"] = aws_session_token

    return boto3.client(**client_kwargs)


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
For platforms, ALWAYS return EXACTLY these 4 stores: Amazon, Best Buy, Walmart, Target. Do NOT include URLs. Ensure at least 4 reviews. Provide 12 months of mock price_history.
For better_alternatives, provide at least 3 options with brand, brand_domain, price, url, and reason.
For platform names, use standard recognizable names like Amazon, Best Buy, Walmart, Target, eBay, B&H Photo, Newegg, Flipkart, etc.
For review_authenticity, analyze each review and classify as 'genuine' or 'fake' with a reason. Provide genuine_count, fake_count, and confidence_score (0-100)."""


def call_nova_pro(image_bytes: Optional[bytes], format_str: Optional[str], text_prompt: Optional[str]) -> dict:
    client = get_bedrock_client()
    content_list = []

    if image_bytes:
        encoded = base64.b64encode(image_bytes).decode("utf-8")
        content_list.append({"image": {"format": format_str, "source": {"bytes": encoded}}})

    final_text = BASE_PROMPT
    if text_prompt:
        final_text = f"USER REQUEST: {text_prompt}\n\nINSTRUCTIONS: {BASE_PROMPT}"
    content_list.append({"text": final_text})

    body = {
        "messages": [{"role": "user", "content": content_list}],
        "system": [{"text": "You are a helpful AI product reviewer. Always output valid JSON."}],
    }

    response = client.invoke_model(modelId="us.amazon.nova-pro-v1:0", body=json.dumps(body))
    response_body = json.loads(response["body"].read())
    output_text = ""
    for item in response_body.get("output", {}).get("message", {}).get("content", []):
        if "text" in item:
            output_text += item["text"]

    output_text = output_text.strip()
    if output_text.startswith("```json"):
        output_text = output_text[7:]
    elif output_text.startswith("```"):
        output_text = output_text[3:]
    if output_text.endswith("```"):
        output_text = output_text[:-3]

    return json.loads(output_text.strip())


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

    result = call_nova_pro(img_bytes, fmt, prompt or None)

    # Enrich platforms with generated search URLs
    product_name = result.get("product_name", "product")
    for p in result.get("platforms", []):
        p["url"] = build_platform_url(p.get("name", ""), product_name)

    # Replace AI price history with our deterministic one
    platforms = result.get("platforms", [])
    base_price = 99.99
    if platforms:
        try:
            base_price = float(min(p.get("price", 9999) for p in platforms))
        except Exception:
            pass
    result["average_price"] = base_price
    result["price_history"] = generate_realistic_price_history(base_price, product_name)

    # Dynamic image sync: Use a high-quality product placeholder based on category
    if result.get("is_new_product") or not img_bytes:
        category = result.get("category", "product")
        # Add "product" to the category search to get more relevant images
        search_term = f"{category},product"
        safe_term = urllib.parse.quote_plus(search_term)
        # loremflickr is a reliable alternative for generic placeholders by category
        result["product_image_url"] = f"https://loremflickr.com/800/600/{safe_term}"
    else:
        result["product_image_url"] = None

    return result
