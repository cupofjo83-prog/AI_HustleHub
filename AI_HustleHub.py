# AI_HustleHub.py
# Modular 3-column Streamlit dashboard with function independence,
# batch/individual execution, API usage counter, and ethical scraper.
# Author: RuralJoe + GPT-5 Thinking

import os
import time
import traceback
import pandas as pd
import requests
from bs4 import BeautifulSoup

import streamlit as st

# =========================
# ===== CONFIG / SETUP =====
# =========================

st.set_page_config(
    page_title="AI HustleHub by RuralJoe",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Gemini client (optional) ----
# Best practice: put your key in an env var: export GEMINI_API_KEY="..."
# or add it to .streamlit/secrets.toml as GEMINI_API_KEY="..."
try:
    from google import genai
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
    MODEL_NAME = "gemini-2.5-flash"
    _gemini_client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None
except Exception:
    _gemini_client = None
    MODEL_NAME = "gemini-2.5-flash"

def gemini_available() -> bool:
    return _gemini_client is not None

# ---- Session state: API usage counter + per-run outputs ----
if "api_calls" not in st.session_state:
    st.session_state.api_calls = 0

if "outputs" not in st.session_state:
    st.session_state.outputs = {}  # key -> str or pd.DataFrame

def _count_api_call(ok: bool):
    if ok:
        st.session_state.api_calls += 1

def call_gemini(prompt: str) -> str:
    """Wrapper that calls Gemini and increments usage counter on success."""
    if not gemini_available():
        return "ERROR: Gemini client not initialized. Set GEMINI_API_KEY."
    try:
        resp = _gemini_client.models.generate_content(model=MODEL_NAME, contents=prompt)
        text = (resp.text or "").strip()
        _count_api_call(True)
        return text if text else "ERROR: Empty response from model."
    except Exception as e:
        return f"ERROR: {e}"

# =========================
# ====== UTILITIES =========
# =========================

TOPIC_FILE = "hustle_topic.txt"

def load_topic_from_file() -> str | None:
    if os.path.exists(TOPIC_FILE):
        try:
            with open(TOPIC_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None
    return None

def save_topic_to_file(topic: str):
    try:
        with open(TOPIC_FILE, "w", encoding="utf-8") as f:
            f.write(topic.strip())
    except Exception:
        pass

def df_has_columns(df: pd.DataFrame, cols: list[str]) -> bool:
    return all(c in df.columns for c in cols)

# =========================
# ===== CORE FUNCTIONS =====
# =========================

# 1) Niche / Topic Generator
def fn_topic_generator(topic_override: str | None = None) -> str:
    """Generate a niche topic. If topic_override exists, just echo it politely."""
    if topic_override:
        return f"(Using provided topic)\n{topic_override}"
    prompt = (
        "You are an expert market analyst. Identify a single, highly specific, "
        "low-competition niche for a digital product or content side hustle. "
        "Output ONLY the niche idea itself."
    )
    return call_gemini(prompt)

# 2) AI Ghostwriter (Long-Form)
def fn_long_form(topic: str | None) -> str:
    if not topic:
        topic = load_topic_from_file()
    if not topic:
        return "ERROR: No topic provided and 'hustle_topic.txt' not found."
    prompt = (
        f"As a professional Ghostwriter, create a detailed, 5-section long-form article outline "
        f"for the niche: {topic}. The outline should be SEO-friendly and ready for script creation."
    )
    return call_gemini(prompt)

# 3) AI Ghostwriter (Short-Form)
def fn_short_form(topic: str | None) -> str:
    if not topic:
        topic = load_topic_from_file()
    if not topic:
        return "ERROR: No topic provided and 'hustle_topic.txt' not found."
    prompt = (
        f"Based on the niche: {topic}, generate a 5-point FAQ list and a 3-sentence summary "
        f"for a short-form video (like a TikTok/Reel)."
    )
    return call_gemini(prompt)

# 4) Social Media Captions
def fn_captions(topic: str | None) -> str:
    if not topic:
        topic = load_topic_from_file()
    if not topic:
        return "ERROR: No topic provided and 'hustle_topic.txt' not found."
    prompt = (
        f"Generate three high-impact captions for the niche: {topic}. One for Instagram, "
        f"one for X/Twitter, and one for LinkedIn. Format clearly with platform headers."
    )
    return call_gemini(prompt)

# 5) SEO Product Automator
def fn_product_automator(cpd: str | None, uploaded_csv: pd.DataFrame | None = None) -> pd.DataFrame | str:
    """
    Uses uploaded dataframe or input.csv fallback.
    Requires columns: Title, Features, Keywords
    Adds 'Generated_Description'.
    If CPD provided (Current Product Description), it will be included in the prompt context.
    """
    df: pd.DataFrame | None = None
    if uploaded_csv is not None:
        df = uploaded_csv.copy()
    elif os.path.exists("input.csv"):
        try:
            df = pd.read_csv("input.csv")
        except Exception as e:
            return f"ERROR: Failed to read input.csv: {e}"
    else:
        return "ERROR: No data provided. Upload a CSV or place 'input.csv' in working directory."

    needed = ["Title", "Features", "Keywords"]
    if not df_has_columns(df, needed):
        return f"ERROR: Missing required columns. Need {needed}"

    out = []
    for _, row in df.iterrows():
        title = str(row["Title"])
        features = str(row["Features"])
        keywords = str(row["Keywords"])
        prompt = (
            "You are an expert e-commerce copywriter. Write a compelling, SEO-optimized product description.\n"
            f"Product: {title}\n"
            f"Features: {features}\n"
            f"Keywords: {keywords}\n"
        )
        if cpd:
            prompt += f"Consider this current/previous description for improvement ideas: {cpd}\n"
        prompt += "Output ONLY the new description."
        text = call_gemini(prompt)
        out.append(text)

    df = df.copy()
    df["Generated_Description"] = out
    try:
        df.to_csv("output.csv", index=False)
    except Exception:
        pass
    return df

# 6) Lead Processor / Outreach
def fn_leads_processor(business_name: str | None, uploaded_csv: pd.DataFrame | None = None) -> pd.DataFrame | str:
    """
    Uses uploaded dataframe or leads.csv fallback.
    Requires columns: Business_Name, Product_Focus, AI_Pitch_Sample
    Adds 'Generated_Email' and 'Status'
    If a single business_name is provided without CSVs, we’ll attempt a minimal single-row run.
    """
    df: pd.DataFrame | None = None
    if uploaded_csv is not None:
        df = uploaded_csv.copy()
    elif os.path.exists("leads.csv"):
        try:
            df = pd.read_csv("leads.csv")
        except Exception as e:
            return f"ERROR: Failed to read leads.csv: {e}"
    elif business_name:
        # Single-row fallback with placeholders
        df = pd.DataFrame(
            [{"Business_Name": business_name, "Product_Focus": "N/A", "AI_Pitch_Sample": "Custom AI services."}]
        )
    else:
        return "ERROR: No leads data found. Upload a CSV or place 'leads.csv' in working directory."

    needed = ["Business_Name", "Product_Focus", "AI_Pitch_Sample"]
    if not df_has_columns(df, needed):
        return f"ERROR: Missing required columns. Need {needed}"

    emails = []
    for _, row in df.iterrows():
        bname = str(row["Business_Name"])
        focus = str(row["Product_Focus"])
        pitch = str(row["AI_Pitch_Sample"])
        prompt = (
            "You are a professional outreach specialist. Draft a personalized, high-conversion cold email pitch.\n"
            f"Target Business: {bname}\n"
            f"Their Focus: {focus}\n"
            f"Your Offer (based on their focus): {pitch}\n"
            "Start professionally. Mention their focus area, then integrate your offer naturally.\n"
            "End with a clear, low-friction CTA. Sign off as RuralJoe. Output ONLY the email body."
        )
        text = call_gemini(prompt)
        emails.append(text)

    df = df.copy()
    df["Generated_Email"] = emails
    df["Status"] = "Processed"
    try:
        df.to_csv("processed_leads.csv", index=False)
    except Exception:
        pass
    return df

# 7) Ethical Scraper / Data Collector
def fn_scraper(url: str, acknowledge: bool) -> dict | str:
    """
    Adds a non-default User-Agent and requires user acknowledgement to check robots.txt/TOS.
    Returns a dict with basic page intel (title, meta, top headers, top links).
    """
    if not url:
        return "ERROR: WEBSITE (URL) is required."
    if not acknowledge:
        return ("ERROR: Please acknowledge you are responsible for checking the target site's robots.txt "
                "and Terms before scraping.")

    headers = {
        "User-Agent": "AI_HustleHubBot/1.0 (+contact: you@example.com)"
    }
    try:
        r = requests.get(url, headers=headers, timeout=15)
        r.raise_for_status()
    except Exception as e:
        return f"ERROR: Request failed: {e}"

    soup = BeautifulSoup(r.text, "html.parser")

    title = (soup.title.string.strip() if soup.title and soup.title.string else "")
    meta_desc = ""
    meta = soup.find("meta", attrs={"name": "description"}) or soup.find("meta", attrs={"property": "og:description"})
    if meta and meta.get("content"):
        meta_desc = meta["content"][:300]

    # Top headings
    h_tags = []
    for tag in soup.find_all(["h1", "h2", "h3"])[:10]:
        txt = (tag.get_text(separator=" ", strip=True) or "")[:120]
        if txt:
            h_tags.append(f"{tag.name.upper()}: {txt}")

    # Top links (same host or overall top few)
    links = []
    for a in soup.find_all("a", href=True)[:15]:
        txt = (a.get_text(separator=" ", strip=True) or "")[:80]
        href = a["href"]
        links.append({"text": txt, "href": href})

    return {
        "status": "ok",
        "title": title,
        "meta_description": meta_desc,
        "headers_preview": h_tags,
        "links_preview": links,
        "http_status": r.status_code,
        "final_url": r.url,
    }

# =========================
# ======= UI LAYOUT =======
# =========================

# Sidebar: session info + API counter
with st.sidebar:
    st.markdown("### ⚙️ Session")
    st.write(f"Model: `{MODEL_NAME}`")
    if gemini_available():
        st.success("Gemini client: ready")
    else:
        st.warning("Gemini client: not initialized")
    st.markdown("---")
    st.markdown("### 📟 API Usage")
    st.metric("Successful API Calls (this session)", st.session_state.api_calls)
    st.caption("Counts only successful model responses.")

st.title("🧰 AI HustleHub — Modular Suite")

# ---- Three columns (1:1:3) ----
col1, col2, col3 = st.columns([1, 1, 3], vertical_alignment="top")

# ================================
# Column 1: Universal Input Panel
# ================================
with col1:
    st.subheader("🔧 Universal Inputs")

    WEBSITE = st.text_input(":WEBSITE (URL to Scrape)", placeholder="https://example.com/trends")
    TOPIC = st.text_input(":TOPIC (Primary Niche)", placeholder="e.g., 'AI-powered Etsy listing optimizer'")
    CPD = st.text_area(":CPD (Current Product Description)", height=120, placeholder="Paste existing product description (optional)")
    BUSINESS_NAME = st.text_input(":BUSINESS NAME (for Leads)", placeholder="e.g., 'Acme Outdoors'")

    st.markdown("---")
    st.caption("If :TOPIC is blank, functions will try to read 'hustle_topic.txt' automatically.")

    st.markdown("**CSV Inputs (optional)**")
    up_products = st.file_uploader("input.csv (Products)", type=["csv"], key="upload_products")
    up_leads = st.file_uploader("leads.csv (Leads)", type=["csv"], key="upload_leads")

    df_products = pd.read_csv(up_products) if up_products is not None else None
    df_leads = pd.read_csv(up_leads) if up_leads is not None else None

    st.markdown("---")
    # Topic save/load helpers
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Save :TOPIC to hustle_topic.txt"):
            if TOPIC:
                save_topic_to_file(TOPIC)
                st.success("Saved.")
            else:
                st.warning("Enter a :TOPIC first.")
    with c2:
        if st.button("📂 Load Topic from File"):
            t = load_topic_from_file()
            if t:
                st.info(f"Loaded: **{t}**")
            else:
                st.warning("No topic file found.")

# ================================================
# Column 2: Function Selection & Execution Panel
# ================================================
with col2:
    st.subheader("🧩 Select & Run Tools")

    # --- 1) Niche / Topic Generator ---
    cb_topic = st.checkbox("1) Niche / Topic Generator")
    if st.button("💡 Generate Niche / Topic"):
        out = fn_topic_generator(TOPIC if TOPIC else None)
        st.session_state.outputs["topic"] = out

    st.markdown("---")

    # --- 2) Long Form ---
    cb_long = st.checkbox("2) Ghostwriter — Long Form")
    if st.button("📝 Generate Long-Form Outline"):
        out = fn_long_form(TOPIC if TOPIC else None)
        st.session_state.outputs["long_form"] = out

    st.markdown("---")

    # --- 3) Short Form ---
    cb_short = st.checkbox("3) Ghostwriter — Short Form")
    if st.button("🎬 Generate Short-Form Script Prep"):
        out = fn_short_form(TOPIC if TOPIC else None)
        st.session_state.outputs["short_form"] = out

    st.markdown("---")

    # --- 4) Captions ---
    cb_caps = st.checkbox("4) Social Media Captions")
    if st.button("📸 Generate Captions"):
        out = fn_captions(TOPIC if TOPIC else None)
        st.session_state.outputs["captions"] = out

    st.markdown("---")

    # --- 5) Product Automator ---
    cb_prod = st.checkbox("5) SEO Product Automator")
    if st.button("🛒 Generate Product Descriptions"):
        out = fn_product_automator(CPD if CPD else None, df_products)
        st.session_state.outputs["products"] = out

    st.markdown("---")

    # --- 6) Lead Processor ---
    cb_leads = st.checkbox("6) Lead Processor / Outreach")
    if st.button("📧 Generate Outreach Emails"):
        out = fn_leads_processor(BUSINESS_NAME if BUSINESS_NAME else None, df_leads)
        st.session_state.outputs["leads"] = out

    st.markdown("---")

    # --- 7) Ethical Scraper ---
    cb_scrape = st.checkbox("7) Ethical Scraper / Data Collector")
    st.warning("Before scraping: **You are responsible** for checking robots.txt and site Terms.")
    ack_scrape = st.checkbox("I understand and agree to check robots.txt and Terms.", value=False)

    if st.button("🌐 Generate Scrape / Data Snapshot"):
        out = fn_scraper(WEBSITE, ack_scrape)
        st.session_state.outputs["scraper"] = out

    st.markdown("---")

    # --- Batch execution ---
    if st.button("🚀 Execute All Selected"):
        try:
            if cb_topic:
                st.session_state.outputs["topic"] = fn_topic_generator(TOPIC if TOPIC else None)

            if cb_long:
                st.session_state.outputs["long_form"] = fn_long_form(TOPIC if TOPIC else None)

            if cb_short:
                st.session_state.outputs["short_form"] = fn_short_form(TOPIC if TOPIC else None)

            if cb_caps:
                st.session_state.outputs["captions"] = fn_captions(TOPIC if TOPIC else None)

            if cb_prod:
                st.session_state.outputs["products"] = fn_product_automator(CPD if CPD else None, df_products)

            if cb_leads:
                st.session_state.outputs["leads"] = fn_leads_processor(BUSINESS_NAME if BUSINESS_NAME else None, df_leads)

            if cb_scrape:
                st.session_state.outputs["scraper"] = fn_scraper(WEBSITE, ack_scrape)

            st.success("All selected functions executed.")
        except Exception as e:
            st.error(f"Batch execution error: {e}")
            st.code(traceback.format_exc())

# =================================
# Column 3: Dynamic Output Display
# =================================
with col3:
    st.subheader("📤 Outputs")

    # Topic
    if "topic" in st.session_state.outputs:
        st.markdown("#### 1) Niche / Topic Generator")
        t_out = st.session_state.outputs["topic"]
        st.code(t_out)
        if isinstance(t_out, str) and t_out and not t_out.startswith("ERROR"):
            # Auto-save best effort
            save_topic_to_file(t_out)

    # Long Form
    if "long_form" in st.session_state.outputs:
        st.markdown("#### 2) Ghostwriter — Long Form")
        st.code(st.session_state.outputs["long_form"])

    # Short Form
    if "short_form" in st.session_state.outputs:
        st.markdown("#### 3) Ghostwriter — Short Form")
        st.code(st.session_state.outputs["short_form"])

    # Captions
    if "captions" in st.session_state.outputs:
        st.markdown("#### 4) Social Media Captions")
        st.code(st.session_state.outputs["captions"])

    # Product Automator
    if "products" in st.session_state.outputs:
        st.markdown("#### 5) SEO Product Automator")
        prod_out = st.session_state.outputs["products"]
        if isinstance(prod_out, pd.DataFrame):
            st.dataframe(prod_out, use_container_width=True)
            st.caption("Saved to output.csv (if write-permitted).")
        else:
            st.code(str(prod_out))

    # Leads
    if "leads" in st.session_state.outputs:
        st.markdown("#### 6) Lead Processor / Outreach")
        leads_out = st.session_state.outputs["leads"]
        if isinstance(leads_out, pd.DataFrame):
            st.dataframe(leads_out, use_container_width=True)
            st.caption("Saved to processed_leads.csv (if write-permitted).")
        else:
            st.code(str(leads_out))

    # Scraper
    if "scraper" in st.session_state.outputs:
        st.markdown("#### 7) Ethical Scraper / Data Collector")
        s_out = st.session_state.outputs["scraper"]
        if isinstance(s_out, dict):
            st.json(s_out)
        else:
            st.code(str(s_out))

# ===== Footer =====
st.markdown("---")
st.caption("Built for flexible, independent execution. Stay ethical with scraping. 🚦")

