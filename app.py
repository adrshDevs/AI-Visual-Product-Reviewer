import streamlit as st
import boto3
import json
import plotly.express as px
import pandas as pd
import os
import random
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_realistic_price_history(base_price, product_name):
    """Generate 12 months of realistic, non-flat price history anchored to base_price."""
    seed = sum(ord(c) for c in product_name.lower())
    rng = random.Random(seed)
    today = datetime.today()
    months, prices = [], []

    # Generate 11 historical months with variation, then anchor the last to base_price
    start = base_price * rng.uniform(1.12, 1.30)   # product was more expensive a year ago
    current = start

    for i in range(11, 0, -1):   # months 11 down to 1
        month_dt = (today.replace(day=1) - timedelta(days=i * 30)).replace(day=1)
        label = month_dt.strftime("%Y-%m")
        month_num = month_dt.month

        # Seasonal adjustments
        seasonal = 0.0
        if month_num == 11:   seasonal = base_price * 0.06   # Black Friday
        elif month_num == 12: seasonal = base_price * 0.04   # Holiday
        elif month_num == 7:  seasonal = -base_price * 0.05  # Summer sale
        elif month_num == 8:  seasonal = -base_price * 0.07  # Back-to-school

        drift = (base_price - current) * 0.20             # Drift toward base_price
        noise = rng.uniform(-base_price * 0.04, base_price * 0.04)
        current = round(max(base_price * 0.70, min(base_price * 1.40, current + drift + seasonal + noise)), 2)
        months.append(label)
        prices.append(current)

    # Final month = current platform price (anchor)
    months.append(today.replace(day=1).strftime("%Y-%m"))
    prices.append(round(base_price, 2))

    # Safety: if spread is too small, force at least 10% variation on earliest month
    price_range = max(prices) - min(prices)
    if price_range < base_price * 0.08:
        prices[0] = round(base_price * rng.uniform(1.15, 1.30), 2)

    return [{"date": m, "price": p} for m, p in zip(months, prices)]

FIXED_PLATFORMS = [
    {"name": "Amazon",   "domain": "amazon.com",   "search_url": "https://www.amazon.com/s?k={q}"},
    {"name": "Best Buy", "domain": "bestbuy.com",  "search_url": "https://www.bestbuy.com/site/searchpage.jsp?st={q}"},
    {"name": "Walmart",  "domain": "walmart.com",  "search_url": "https://www.walmart.com/search?q={q}"},
    {"name": "Target",   "domain": "target.com",   "search_url": "https://www.target.com/s?searchTerm={q}"},
]

def build_platform_url(platform_name, product_name):
    """Return a reliable search URL for a given platform and product."""
    import urllib.parse
    q = urllib.parse.quote_plus(product_name)
    for p in FIXED_PLATFORMS:
        if p["name"].lower() == platform_name.lower():
            return p["search_url"].format(q=q)
    # Fallback to Google Shopping search
    return f"https://www.google.com/search?q={q}+buy+site:{platform_name.lower().replace(' ', '')}.com"

# Setup page
st.set_page_config(page_title="AI Visual Product Reviewer", page_icon="🛍️", layout="wide")

# Initialize session state
if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None
if "last_queried" not in st.session_state:
    st.session_state.last_queried = None
if "uploaded_image" not in st.session_state:
    st.session_state.uploaded_image = None

st.title("🛍️ AI Visual Product Reviewer")
st.markdown("Search for a product via text, ask questions, or upload an image for a deep-dive AI review.")

# Custom CSS for a more premium look
st.markdown("""
<style>
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
    }
    .stInfo, .stSuccess, .stWarning {
        border-radius: 12px;
        border: none;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    h1, h2, h3 {
        color: #1e293b;
        font-weight: 700 !important;
    }
    .reportview-container .main .block-container {
        padding-top: 2rem;
    }
</style>
""", unsafe_allow_html=True)

def get_platform_logo(name):
    """Returns an HTML img tag for the platform logo."""
    name = name.lower().strip()
    mapping = {
        "amazon": "https://www.google.com/s2/favicons?domain=amazon.com&sz=32",
        "bestbuy": "https://www.google.com/s2/favicons?domain=bestbuy.com&sz=32",
        "best buy": "https://www.google.com/s2/favicons?domain=bestbuy.com&sz=32",
        "walmart": "https://www.google.com/s2/favicons?domain=walmart.com&sz=32",
        "target": "https://www.google.com/s2/favicons?domain=target.com&sz=32",
        "ebay": "https://www.google.com/s2/favicons?domain=ebay.com&sz=32",
        "apple": "https://www.google.com/s2/favicons?domain=apple.com&sz=32",
        "samsung": "https://www.google.com/s2/favicons?domain=samsung.com&sz=32",
        "newegg": "https://www.google.com/s2/favicons?domain=newegg.com&sz=32",
        "bhphoto": "https://www.google.com/s2/favicons?domain=bhphotovideo.com&sz=32",
        "b&h": "https://www.google.com/s2/favicons?domain=bhphotovideo.com&sz=32",
        "costco": "https://www.google.com/s2/favicons?domain=costco.com&sz=32",
        "flipkart": "https://www.google.com/s2/favicons?domain=flipkart.com&sz=32",
        "aliexpress": "https://www.google.com/s2/favicons?domain=aliexpress.com&sz=32",
        "temu": "https://www.google.com/s2/favicons?domain=temu.com&sz=32",
        "shein": "https://www.google.com/s2/favicons?domain=shein.com&sz=32",
        "reddit": "https://www.google.com/s2/favicons?domain=reddit.com&sz=32",
        "youtube": "https://www.google.com/s2/favicons?domain=youtube.com&sz=32",
        "facebook": "https://www.google.com/s2/favicons?domain=facebook.com&sz=32",
        "instagram": "https://www.google.com/s2/favicons?domain=instagram.com&sz=32",
        "twitter": "https://www.google.com/s2/favicons?domain=twitter.com&sz=32",
        "x": "https://www.google.com/s2/favicons?domain=twitter.com&sz=32"
    }
    
    # Try to find a match in the keys
    for key, url in mapping.items():
        if key in name:
            logo_url = url
            break
    else:
        # Fallback to a generic shopping bag icon if no match
        logo_url = "https://cdn-icons-png.flaticon.com/512/1170/1170678.png"
    
    return f'<img src="{logo_url}" width="20" style="vertical-align: middle; margin-right: 8px; border-radius: 4px;">'

def get_bedrock_client():
    aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_session_token = os.getenv("AWS_SESSION_TOKEN")
    aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    aws_profile = os.getenv("AWS_PROFILE")
    
    try:
        # If a specific profile is requested, set up the default session for it.
        # Otherwise, Boto3 will automatically use the default provider chain
        # (environment variables, ~/.aws/credentials, IAM roles, etc.)
        if aws_profile:
            boto3.setup_default_session(profile_name=aws_profile)

        client_kwargs = {
            'service_name': 'bedrock-runtime', 
            'region_name': aws_region,
        }
        
        # Explicit keys override the provider chain if present
        if aws_access_key and aws_secret_key:
            client_kwargs['aws_access_key_id'] = aws_access_key
            client_kwargs['aws_secret_access_key'] = aws_secret_key
            if aws_session_token:
                client_kwargs['aws_session_token'] = aws_session_token
            
        return boto3.client(**client_kwargs)
    except Exception as e:
        st.error(f"Failed to create Bedrock client. Ensure your AWS credentials are correct: {e}")
        return None

def call_nova_pro(image_bytes=None, format_str=None, text_prompt=None):
    client = get_bedrock_client()
    if not client:
        return None
    
    # Base prompt for the structured data
    base_prompt = """Analyze the product based on the provided input (image, text, or both) and provide a comprehensive review in JSON format matching exactly this structure:
{
    "product_name": "Name of the product",
    "category": "Product category",
    "specific_answer": "Directly answer the user's specific request or question from the prompt box here. If no specific question was asked, briefly summarize the product's value proposition.",
    "build_and_features": {
        "build_quality": "High-level summary of construction quality",
        "materials": ["Material 1", "Material 2"],
        "special_details": "Unique features or technical highlights"
    },
    "key_features": ["Feature 1", "Feature 2", "Feature 3"],
    "pros": ["Pro 1", "Pro 2", "Pro 3"],
    "cons": ["Con 1", "Con 2"],
    "rating": 8.5,
    "worth_buying": true,
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
    "price_history": [
        {"date": "2023-01", "price": 249.99}
    ],
    "frequently_bought_together": [
        {"name": "Accessory A", "reason": "Protects the product"}
    ],
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
        "summary": "Most reviews appear genuine; one review shows signs of being fabricated (overly generic, no specifics).",
        "per_review": [
            {"user": "User1", "verdict": "genuine", "reason": "Specific product details mentioned, balanced tone."},
            {"user": "User2", "verdict": "fake", "reason": "Overly promotional, no critical feedback, suspiciously short."}
        ]
    }
}

Return ONLY valid JSON. 
If an image is provided, use it as the primary source of truth. 
If text is provided, use it to refine the search or answer specific user questions.
If ONLY text is provided, perform a product search for that item.
For platforms, ALWAYS return EXACTLY these 4 stores with realistic prices for the identified product: Amazon, Best Buy, Walmart, Target. Do NOT include URLs, we will generate them ourselves. Ensure at least 4 reviews. Provide 12 months of mock price_history.
For better_alternatives, provide at least 3 options with brand, brand_domain, price, url, and reason.
For platform names, use standard recognizable names like Amazon, Best Buy, Walmart, Target, eBay, B&H Photo, Newegg, Flipkart, etc.
For review_authenticity, analyze each review in the reviews array and classify each as 'genuine' or 'fake' with a reason. Provide genuine_count, fake_count, and a confidence_score (0-100) representing percentage of genuine reviews."""

    # Construct messages content
    content_list = []
    
    # Add image if present
    if image_bytes:
        import base64
        encoded_image = base64.b64encode(image_bytes).decode("utf-8")
        content_list.append({
            "image": {
                "format": format_str,
                "source": {"bytes": encoded_image}
            }
        })
    
    # Add text prompt (or base instructions if text_prompt is missing)
    final_text = base_prompt
    if text_prompt:
        final_text = f"USER REQUEST: {text_prompt}\n\nINSTUCTIONS: {base_prompt}"
    content_list.append({"text": final_text})

    body = {
        "messages": [
            {
                "role": "user",
                "content": content_list
            }
        ],
        "system": [{"text": "You are a helpful AI product reviewer. Always output valid JSON."}]
    }

    try:
        response = client.invoke_model(
            modelId="us.amazon.nova-pro-v1:0",
            body=json.dumps(body)
        )
        response_body = json.loads(response.get('body').read())
        output_message = response_body.get("output", {}).get("message", {})
        content = output_message.get("content", [])
        
        text = ""
        for item in content:
            if "text" in item:
                text += item["text"]
                
        text = text.strip()
        if text.startswith("```json"): text = text[7:]
        elif text.startswith("```"): text = text[3:]
        if text.endswith("```"): text = text[:-3]
            
        return json.loads(text.strip())
        
    except Exception as e:
        st.error(f"Error communicating with Bedrock: {e}")
        return None

# --- Product Input Section ---
with st.container():
    st.subheader("🖼️ Product Analysis & Search")
    
    # Image Analyzer on Top
    col_u1, col_u2 = st.columns([4, 1])
    with col_u1:
        standalone_file = st.file_uploader("Upload or drop a product image here", type=["jpg", "jpeg", "png", "webp"], key="standalone_u")
        if standalone_file:
            st.session_state.uploaded_image = standalone_file.getvalue()
        else:
            st.session_state.uploaded_image = None
            
    with col_u2:
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, width=100)
    
    # Interactive Prompt below Image
    with st.expander("✨ Want to know something specific about this product?", expanded=True):
        prompt_text = st.text_area("Ask anything (e.g., 'Is this durable?', 'What's the battery life?', or just type a product name)", placeholder="Type your specific questions or product search terms here...", height=100)
    
    # Unified Action Button
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🚀 Analyze & Search Product", type="primary", use_container_width=True):
        if standalone_file or prompt_text:
            with st.spinner("Analyzing and searching for details..."):
                img_bytes = None
                fmt = None
                if standalone_file:
                    img_bytes = standalone_file.getvalue()
                    fmt = standalone_file.name.split('.')[-1].lower()
                    if fmt == 'jpg': fmt = 'jpeg'
                
                st.session_state.analysis_result = call_nova_pro(img_bytes, fmt, prompt_text)
                st.session_state.last_queried = prompt_text if prompt_text else f"Image: {standalone_file.name}"
        else:
            st.warning("Please upload an image or enter a text query to proceed.")
    



# --- Display Results Section ---
if st.session_state.analysis_result:
    result = st.session_state.analysis_result
    
    # Product Header with Image
    header_col1, header_col2 = st.columns([1, 4])
    with header_col1:
        if st.session_state.uploaded_image:
            st.image(st.session_state.uploaded_image, use_container_width=True)
        else:
            st.markdown("🖼️") # Icon if no image was uploaded (text-only search)

    with header_col2:
        st.info(f"Showing results for: **{st.session_state.last_queried}**")
        st.header(result.get("product_name", "Unknown Product"))
        st.subheader(f"Category: {result.get('category', 'N/A')}")

    st.divider()
    
    # AI Insights — only show when a text prompt/question was asked
    answer = result.get("specific_answer")
    if answer and st.session_state.last_queried and not st.session_state.last_queried.startswith("Image: "):
        st.markdown(f"""
        <div style="background-color: rgba(99, 110, 250, 0.1); padding: 15px; border-radius: 12px; border-left: 5px solid #636EFA; margin-bottom: 20px;">
            <h4 style="margin-top: 0; color: #636EFA;">💡 AI Insights</h4>
            <p style="margin-bottom: 0; font-size: 1.1rem; line-height: 1.4;">{answer}</p>
        </div>
        """, unsafe_allow_html=True)
    
    rating = result.get("rating", 0)
    decision = "✅ Worth Buying" if result.get("worth_buying") else "❌ Think Twice"
    st.metric("Product Rating", f"{rating}/10", delta=decision)
    
    st.divider()
    
    # New Build and Features Section
    bf = result.get("build_and_features", {})
    if bf:
        st.subheader("🛠️ Build & Features")
        bf_col1, bf_col2 = st.columns(2)
        with bf_col1:
            st.markdown(f"""
            <div style="background-color: rgba(255, 165, 0, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 165, 0, 0.2);">
                <h5 style="margin-top:0; color: #cc7a00;">🏗️ Build Quality & Materials</h5>
                <p><b>Quality:</b> {bf.get('build_quality', 'N/A')}</p>
                <p><b>Materials:</b> {', '.join(bf.get('materials', []))}</p>
            </div>
            """, unsafe_allow_html=True)
        with bf_col2:
            st.markdown(f"""
            <div style="background-color: rgba(255, 165, 0, 0.05); padding: 15px; border-radius: 12px; border: 1px solid rgba(255, 165, 0, 0.2);">
                <h5 style="margin-top:0; color: #cc7a00;">💠 Special Details</h5>
                <p>{bf.get('special_details', 'N/A')}</p>
            </div>
            """, unsafe_allow_html=True)

    st.divider()
    
    # Features, Pros, Cons
    col_feat, col_pro, col_con = st.columns(3)
    with col_feat:
        st.subheader("Key Features")
        for feature in result.get("key_features", []):
            st.markdown(f"- {feature}")
    with col_pro:
        st.subheader("Pros")
        for pro in result.get("pros", []):
            st.markdown(f"- ✅ {pro}")
    with col_con:
        st.subheader("Cons")
        for con in result.get("cons", []):
            st.markdown(f"- ❌ {con}")
    
    st.divider()
    
    # Price History — generated realistically from AI's base price
    st.subheader("📈 Price History")
    # Get the base price (lowest price from what AI's platforms reported)
    platforms = result.get("platforms", [])
    base_price = None
    if platforms:
        try:
            base_price = float(min(p.get("price", 9999) for p in platforms))
        except:
            base_price = None
    
    # Fallback: try price_history from AI if present
    if not base_price and result.get("price_history"):
        try:
            base_price = float(result["price_history"][0].get("price", 99.99))
        except:
            base_price = 99.99
    
    if not base_price:
        base_price = 99.99

    product_name = result.get("product_name", "product")
    price_history = generate_realistic_price_history(base_price, product_name)
    if price_history:
        df = pd.DataFrame(price_history)
        if not df.empty and "date" in df.columns and "price" in df.columns:
            df["price"] = pd.to_numeric(df["price"], errors="coerce")
            df = df.dropna(subset=["price"])
            df["date"] = df["date"].astype(str)
            # Find highest and lowest for highlighting
            max_idx = df["price"].idxmax()
            min_idx = df["price"].idxmin()
            max_price = df["price"].max()
            min_price = df["price"].min()
            max_date = df.loc[max_idx, "date"]
            min_date = df.loc[min_idx, "date"]

            # Elegant Area Chart with Splines
            fig = px.area(df, x="date", y="price", markers=True, title="Price Trend (Last 12 Months)")
            
            fig.update_traces(
                line_color='#636EFA', 
                fillcolor='rgba(99, 110, 250, 0.2)', 
                line_shape='spline',
                marker=dict(size=6, color='#636EFA'),
                hovertemplate="<b>Date:</b> %{x}<br><b>Price:</b> $%{y:,.2f}<extra></extra>"
            )

            fig.add_scatter(x=[max_date], y=[max_price], mode='markers+text', marker=dict(color='#FF4B4B', size=12), text=["Peak"], textposition="top center", showlegend=False)
            fig.add_scatter(x=[min_date], y=[min_price], mode='markers+text', marker=dict(color='#28a745', size=12), text=["Lowest"], textposition="bottom center", showlegend=False)
            
            fig.update_layout(
                xaxis_title="", yaxis_title="Price ($)", hovermode="x unified",
                margin=dict(l=0, r=0, t=40, b=0), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)',
                xaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(128,128,128,0.1)', tickprefix="$")
            )
            st.plotly_chart(fig, use_container_width=True)

            col_max, col_min = st.columns(2)
            with col_max:
                st.markdown(f'<div style="background-color: rgba(255, 75, 75, 0.1); border-left: 5px solid #FF4B4B; padding: 10px; border-radius: 5px;"><p style="margin:0; color: #FF4B4B; font-weight: bold; font-size: 0.8rem;">HIGHEST PRICE</p><p style="margin:0; font-size: 1.2rem; font-weight: bold;">${max_price}</p><p style="margin:0; font-size: 0.7rem; opacity: 0.7;">{max_date}</p></div>', unsafe_allow_html=True)
            with col_min:
                st.markdown(f'<div style="background-color: rgba(40, 167, 69, 0.1); border-left: 5px solid #28a745; padding: 10px; border-radius: 5px;"><p style="margin:0; color: #28a745; font-weight: bold; font-size: 0.8rem;">LOWEST PRICE</p><p style="margin:0; font-size: 1.2rem; font-weight: bold;">${min_price}</p><p style="margin:0; font-size: 0.7rem; opacity: 0.7;">{min_date}</p></div>', unsafe_allow_html=True)
    
    st.divider()

    # ── Review Authenticity & AI Confidence ──────────────────────────────────
    auth = result.get("review_authenticity", {})
    if auth:
        st.subheader("🔍 Review Authenticity")
        genuine_count = auth.get("genuine_count", 0)
        fake_count    = auth.get("fake_count", 0)
        confidence    = auth.get("confidence_score", 0)
        total         = genuine_count + fake_count or 1

        auth_col1, auth_col2 = st.columns([1, 2])

        # Left — donut gauge
        with auth_col1:
            import plotly.graph_objects as go
            gauge_color = "#28a745" if confidence >= 70 else ("#ffc107" if confidence >= 40 else "#FF4B4B")
            fig_gauge = go.Figure(go.Pie(
                values=[confidence, 100 - confidence],
                hole=0.72,
                marker_colors=[gauge_color, "rgba(200,200,200,0.15)"],
                textinfo="none",
                hoverinfo="skip",
                sort=False,
            ))
            fig_gauge.add_annotation(
                text=f"<b>{confidence}%</b><br><span style='font-size:11px;color:#888'>Genuine</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=22, color=gauge_color),
            )
            fig_gauge.update_layout(
                showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                height=220,
                annotations=[dict(
                    text=f"<b>{confidence}%</b><br><span style='font-size:11px;color:#888'>Genuine</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=22, color=gauge_color),
                )]
            )
            st.plotly_chart(fig_gauge, use_container_width=True)

            # Summary stats below the gauge
            st.markdown(
                f"""
                <div style="display:flex; gap:10px; justify-content:center; margin-top:-10px;">
                    <div style="text-align:center; background:rgba(40,167,69,0.1); border-radius:10px; padding:10px 18px;">
                        <div style="font-size:1.6rem; font-weight:700; color:#28a745;">{genuine_count}</div>
                        <div style="font-size:0.75rem; color:#666;">Genuine</div>
                    </div>
                    <div style="text-align:center; background:rgba(255,75,75,0.1); border-radius:10px; padding:10px 18px;">
                        <div style="font-size:1.6rem; font-weight:700; color:#FF4B4B;">{fake_count}</div>
                        <div style="font-size:0.75rem; color:#666;">Fake</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Right — per-review breakdown + summary
        with auth_col2:
            summary = auth.get("summary", "")
            if summary:
                st.markdown(
                    f"""
                    <div style="background:rgba(99,110,250,0.08); border-left:4px solid #636EFA;
                                padding:12px 16px; border-radius:8px; margin-bottom:14px;">
                        <b style="color:#636EFA;">AI Assessment</b><br>
                        <span style="font-size:0.92rem;">{summary}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            per_review = auth.get("per_review", [])
            for pr in per_review:
                verdict = pr.get("verdict", "genuine").lower()
                is_fake = verdict == "fake"
                badge_color  = "#FF4B4B" if is_fake else "#28a745"
                badge_bg     = "rgba(255,75,75,0.1)" if is_fake else "rgba(40,167,69,0.1)"
                badge_icon   = "🚫" if is_fake else "✅"
                verdict_label = "FAKE" if is_fake else "GENUINE"
                st.markdown(
                    f"""
                    <div style="background:{badge_bg}; border:1px solid {badge_color}40;
                                border-radius:10px; padding:10px 14px; margin-bottom:8px;
                                display:flex; align-items:flex-start; gap:12px;">
                        <span style="font-size:1.3rem;">{badge_icon}</span>
                        <div>
                            <b>{pr.get('user', 'Unknown')}</b>
                            <span style="margin-left:8px; background:{badge_color}; color:white;
                                         font-size:0.65rem; font-weight:700; padding:2px 6px;
                                         border-radius:4px;">{verdict_label}</span>
                            <div style="font-size:0.82rem; color:#555; margin-top:4px;">{pr.get('reason', '')}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        st.divider()

    # Reviews and Platforms
    col_rev, col_plat, col_alt = st.columns(3)
    with col_rev:
        st.subheader("💬 User Reviews")
        for r in result.get("reviews", []):
            platform = r.get('platform', 'Unknown')
            logo = get_platform_logo(platform)
            st.markdown(f'<div style="background-color: rgba(0, 104, 201, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 10px; border: 1px solid rgba(0, 104, 201, 0.1);"><p style="margin:0;">{logo} <b>{r.get("user")} on {platform}</b>: {r.get("rating")}/5 ⭐</p><p style="margin:10px 0 0 0; font-size: 0.9rem; font-style: italic;">"{r.get("text")}"</p></div>', unsafe_allow_html=True)
    
    with col_plat:
        st.subheader("🛒 Trusted Stores")
        for p in result.get("platforms", []):
            name = p.get('name', 'Unknown')
            logo = get_platform_logo(name)
            st.markdown(f'<div style="background-color: rgba(33, 195, 84, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid rgba(33, 195, 84, 0.1);"><p style="margin:0;">{logo} <b><a href="{p.get("url", "#")}" style="text-decoration: none; color: inherit;">{name}</a></b> - Score: {p.get("trust_score")}/10</p><p style="margin:5px 0;">Price: <b>${p.get("price")}</b></p><a href="{p.get("url", "#")}" target="_blank" style="display: inline-block; padding: 5px 12px; background-color: #28a745; color: white; text-decoration: none; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">🔗 Buy Now</a></div>', unsafe_allow_html=True)
        
        st.subheader("📦 Often Bought With")
        for item in result.get("frequently_bought_together", []):
            st.markdown(f"- **{item.get('name')}** ({item.get('reason')})")

    with col_alt:
        st.subheader("💡 Better Alternatives")
        for alt in result.get("better_alternatives", []):
            domain = alt.get('brand_domain', '')
            logo_url = f"https://www.google.com/s2/favicons?domain={domain}&sz=64" if domain else "https://cdn-icons-png.flaticon.com/512/1170/1170678.png"
            st.markdown(f"""
            <div style="background-color: rgba(255, 193, 7, 0.05); padding: 15px; border-radius: 12px; margin-bottom: 15px; border: 1px solid rgba(255, 193, 7, 0.2);">
                <div style="display: flex; align-items: center; margin-bottom: 10px;">
                    <img src="{logo_url}" width="40" style="border-radius: 8px; margin-right: 12px;">
                    <div>
                        <h5 style="margin: 0; color: #856404;">{alt.get('name')}</h5>
                        <p style="margin: 0; font-weight: bold; color: #28a745;">${alt.get('price')}</p>
                    </div>
                </div>
                <p style="font-size: 0.85rem; margin-bottom: 10px;"><i>{alt.get('reason')}</i></p>
                <a href="{alt.get('url', '#')}" target="_blank" style="display: inline-block; padding: 5px 12px; background-color: #ffc107; color: #212529; text-decoration: none; border-radius: 6px; font-size: 0.8rem; font-weight: 600;">🔗 View Product</a>
            </div>
            """, unsafe_allow_html=True)

