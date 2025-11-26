# AI_HustleHub.py
# Modular per-function Streamlit dashboard with function independence,
# per-tool inputs/outputs, API usage counter, and ethical scraper.
# Author: RuralJoe + GPT-5 Thinking

import os
import time
import traceback
import io

import pandas as pd
import requests
from bs4 import BeautifulSoup

import streamlit as st
from dotenv import load_dotenv
import google.generativeai as genai

# =========================
# ===== CONFIG / SETUP =====
# =========================

st.set_page_config(
    page_title="AI HustleHub by RuralJoe",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- Env + Gemini client ----
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY") or st.secrets.get("GEMINI_API_KEY", None)
MODEL_NAME = "gemini-2.5-flash"  # adjust if needed

_gemini_client = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        _gemini_client = genai.GenerativeModel(MODEL_NAME)
        print("[OK] Gemini client initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize Gemini client: {e}")
        _gemini_client = None
else:
    print("[WARN] GEMINI_API_KEY is not set; Gemini tools will be unavailable.")

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
        resp = _gemini_client.generate_content(prompt)
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

def save_text_download_button(label: str, text: str, filename: str):
    """Offer a download button for text output."""
    if not text:
        return
    buf = io.BytesIO(text.encode("utf-8"))
    st.download_button(
        label,
        data=buf,
        file_name=filename,
        mime="text/plain",
    )

def save_csv_download_button(label: str, df: pd.DataFrame, filename: str):
    """Offer a download button for CSV output."""
    if df is None or df.empty:
        return
    buf = io.BytesIO(df.to_csv(index=False).encode("utf-8"))
    st.download_button(
        label,
        data=buf,
        file_name=filename,
        mime="text/csv",
    )

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
# ========= UI =============
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
    st.markdown("---")
    st.caption("Each tool below has its own input {block} → output {block} on the main page.")

st.title("🧰 AI HustleHub — Per-Tool Panels")

# For visual “{ input } → { output }” mapping, each tool gets a container
# with two columns: LEFT = input {block}, RIGHT = output {block}

st.markdown("### 1) Niche / Topic Generator { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Niche / Topic**")
        topic_input_1 = st.text_input(
            "Topic / Niche (optional)",
            key="topic_gen_input",
            placeholder="Leave blank to auto-generate a niche"
        )
        if st.button("💡 Generate Niche / Topic", key="btn_topic_gen"):
            out = fn_topic_generator(topic_input_1 if topic_input_1 else None)
            st.session_state.outputs["topic"] = out
            st.success("Generated niche/topic.")

            # Auto-save if it's not an error
            if isinstance(out, str) and out and not out.startswith("ERROR"):
                save_topic_to_file(out)

    with out_col:
        st.markdown("**{ Output } Niche / Topic**")
        t_out = st.session_state.outputs.get("topic")
        if t_out:
            st.code(t_out)
            save_text_download_button("💾 Download Topic as .txt", t_out, "topic.txt")
        else:
            st.info("Run the generator to see output here.")

st.markdown("---")

st.markdown("### 2) Ghostwriter — Long Form { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Long-Form**")
        topic_input_long = st.text_input(
            "Topic / Niche",
            key="topic_long_input",
            placeholder="If blank, will try hustle_topic.txt"
        )
        if st.button("📝 Generate Long-Form Outline", key="btn_long_form"):
            out = fn_long_form(topic_input_long if topic_input_long else None)
            st.session_state.outputs["long_form"] = out
            st.success("Generated long-form outline.")

    with out_col:
        st.markdown("**{ Output } Long-Form**")
        long_out = st.session_state.outputs.get("long_form")
        if long_out:
            st.code(long_out)
            save_text_download_button("💾 Download Long-Form as .txt", long_out, "long_form.txt")
        else:
            st.info("Run the long-form tool to see output here.")

st.markdown("---")

st.markdown("### 3) Ghostwriter — Short Form { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Short-Form**")
        topic_input_short = st.text_input(
            "Topic / Niche",
            key="topic_short_input",
            placeholder="If blank, will try hustle_topic.txt"
        )
        if st.button("🎬 Generate Short-Form Prep", key="btn_short_form"):
            out = fn_short_form(topic_input_short if topic_input_short else None)
            st.session_state.outputs["short_form"] = out
            st.success("Generated short-form prep.")

    with out_col:
        st.markdown("**{ Output } Short-Form**")
        short_out = st.session_state.outputs.get("short_form")
        if short_out:
            st.code(short_out)
            save_text_download_button("💾 Download Short-Form as .txt", short_out, "short_form.txt")
        else:
            st.info("Run the short-form tool to see output here.")

st.markdown("---")

st.markdown("### 4) Social Media Captions { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Captions**")
        topic_input_caps = st.text_input(
            "Topic / Niche",
            key="topic_caps_input",
            placeholder="If blank, will try hustle_topic.txt"
        )
        if st.button("📸 Generate Captions", key="btn_caps"):
            out = fn_captions(topic_input_caps if topic_input_caps else None)
            st.session_state.outputs["captions"] = out
            st.success("Generated captions.")

    with out_col:
        st.markdown("**{ Output } Captions**")
        caps_out = st.session_state.outputs.get("captions")
        if caps_out:
            st.code(caps_out)
            save_text_download_button("💾 Download Captions as .txt", caps_out, "captions.txt")
        else:
            st.info("Run the captions tool to see output here.")

st.markdown("---")

st.markdown("### 5) SEO Product Automator { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Products CSV + CPD**")
        cpd_input = st.text_area(
            "Current Product Description (optional)",
            key="cpd_input",
            height=120,
            placeholder="Paste existing product description (optional)"
        )
        up_products = st.file_uploader(
            "Upload input.csv (Products)",
            type=["csv"],
            key="upload_products_per_tool"
        )
        df_products = pd.read_csv(up_products) if up_products is not None else None

        if st.button("🛒 Generate Product Descriptions", key="btn_products"):
            out = fn_product_automator(cpd_input if cpd_input else None, df_products)
            st.session_state.outputs["products"] = out
            st.success("Processed products.")

    with out_col:
        st.markdown("**{ Output } Products**")
        prod_out = st.session_state.outputs.get("products")
        if isinstance(prod_out, pd.DataFrame):
            st.dataframe(prod_out, use_container_width=True)
            st.caption("Saved to output.csv (if write-permitted).")
            save_csv_download_button("💾 Download output.csv", prod_out, "output.csv")
        elif isinstance(prod_out, str):
            st.code(prod_out)
        else:
            st.info("Run the product automator to see output here.")

st.markdown("---")

st.markdown("### 6) Lead Processor / Outreach { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Leads CSV / Business Name**")
        business_name_input = st.text_input(
            "Business Name (optional, single-run)",
            key="business_name_input",
            placeholder="e.g., 'Acme Outdoors'"
        )
        up_leads = st.file_uploader(
            "Upload leads.csv",
            type=["csv"],
            key="upload_leads_per_tool"
        )
        df_leads = pd.read_csv(up_leads) if up_leads is not None else None

        if st.button("📧 Generate Outreach Emails", key="btn_leads"):
            out = fn_leads_processor(
                business_name_input if business_name_input else None,
                df_leads
            )
            st.session_state.outputs["leads"] = out
            st.success("Processed leads.")

    with out_col:
        st.markdown("**{ Output } Leads**")
        leads_out = st.session_state.outputs.get("leads")
        if isinstance(leads_out, pd.DataFrame):
            st.dataframe(leads_out, use_container_width=True)
            st.caption("Saved to processed_leads.csv (if write-permitted).")
            save_csv_download_button("💾 Download processed_leads.csv", leads_out, "processed_leads.csv")
        elif isinstance(leads_out, str):
            st.code(leads_out)
        else:
            st.info("Run the lead processor to see output here.")

st.markdown("---")

st.markdown("### 7) Ethical Scraper / Data Collector { Input → Output }")
with st.container():
    in_col, out_col = st.columns([1, 1.2], vertical_alignment="top")
    with in_col:
        st.markdown("**{ Input } Website URL**")
        WEBSITE = st.text_input(
            "WEBSITE (URL to Scrape)",
            key="website_input",
            placeholder="https://example.com/trends"
        )
        st.warning("Before scraping: **You are responsible** for checking robots.txt and site Terms.")
        ack_scrape = st.checkbox(
            "I understand and agree to check robots.txt and Terms.",
            value=False,
            key="ack_scrape"
        )

        if st.button("🌐 Generate Scrape / Data Snapshot", key="btn_scrape"):
            out = fn_scraper(WEBSITE, ack_scrape)
            st.session_state.outputs["scraper"] = out
            st.success("Scraper run completed.")

    with out_col:
        st.markdown("**{ Output } Scraper Snapshot**")
        s_out = st.session_state.outputs.get("scraper")
        if isinstance(s_out, dict):
            st.json(s_out)
        elif isinstance(s_out, str):
            st.code(s_out)
        else:
            st.info("Run the scraper to see output here.")

# ===== Footer =====
st.markdown("---")
st.caption("Each tool has its own {input} → {output} panel. Stay ethical with scraping. 🚦")
