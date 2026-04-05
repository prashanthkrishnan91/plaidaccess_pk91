import streamlit as st
import requests

# 1. Page Configuration
st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

# 2. State Initialization
if 'link_token' not in st.session_state:
    st.session_state.link_token = None
if 'hosted_link_url' not in st.session_state:
    st.session_state.hosted_link_url = None
if 'access_token' not in st.session_state:
    st.session_state.access_token = None

# 3. Environment Setup
try:
    CLIENT_ID = st.secrets["PLAID_CLIENT_ID"]
    SECRET = st.secrets["PLAID_SECRET"]
    ENV = st.secrets.get("PLAID_ENV", "sandbox")
    BASE_URL = "https://production.plaid.com" if ENV == "production" else "https://sandbox.plaid.com"
except Exception as e:
    st.error("Missing Plaid secrets in Streamlit configuration.")
    st.stop()

# ==========================================
# STEP 1: Generate Hosted Link
# ==========================================
if not st.session_state.link_token and not st.session_state.access_token:
    st.info("Step 1: Generate a secure Plaid connection link.")
    if st.button("Generate Link"):
        with st.spinner("Communicating with Plaid..."):
            payload = {
                "client_id": CLIENT_ID,
                "secret": SECRET,
                "client_name": "Plaid Access PK91",
                "language": "en",
                "country_codes": ["US"],
                "user": {"client_user_id": "streamlit-user"},
                "products": ["investments"],
                "hosted_link": {} 
            }
            try:
                response = requests.post(f"{BASE_URL}/link/token/create", json=payload)
                data = response.json()
                if "error_message" in data:
                    st.error(f"Plaid Error: {data['error_message']}")
                else:
                    st.session_state.link_token = data["link_token"]
                    st.session_state.hosted_link_url = data["hosted_link_url"]
                    st.rerun()
            except Exception as e:
                st.error(f"Request failed: {e}")

# ==========================================
# STEP 2: The User Flow (External Tab)
# ==========================================
if st.session_state.hosted_link_url and not st.session_state.access_token:
    st.success("✅ Secure Link Generated!")
    st.markdown("### Step 2: Connect your account")
    
    button_html = f"""
    <a href="{st.session_state.hosted_link_url}" target="_blank" style="display: block; width: 100%; padding: 15px; background-color: #00ADEE; color: white; text-decoration: none; border-radius: 6px; font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 20px;">
        Connect to Robinhood (Opens in New Tab)
    </a>
    """
    st.markdown(button_html, unsafe_allow_html=True)
    st.warning("Click the button above. Once you see the 'Success' screen in the other tab, close it and return here.")
    
    st.markdown("### Step 3: Finalize Connection")
    if st.button("I have completed the login - Fetch Access Token"):
        with st.spinner("Verifying session status with Plaid..."):
            get_payload = {
                "client_id": CLIENT_ID,
                "secret": SECRET,
                "link_token": st.session_state.link_token
            }
            response = requests.post(f"{BASE_URL}/link/token/get", json=get_payload)
            get_response = response.json()
            
            sessions = get_response.get("link_sessions", [])
            public_token = None
            
            for session in sessions:
                if "on_success" in session and session["on_success"]:
                    public_token = session["on_success"].get("public_token")
                    break
            
            if public_token:
                st.success("✅ Session verified! Exchanging token...")
                exchange_payload = {
                    "client_id": CLIENT_ID,
                    "secret": SECRET,
                    "public_token": public_token
                }
                # FIXED: Consistently use exchange_res and exchange_data
                exchange_res = requests.post(f"{BASE_URL}/item/public_token/exchange", json=exchange_payload)
                exchange_data = exchange_res.json()
                
                if "access_token" in exchange_data:
                    st.session_state.access_token = exchange_data["access_token"]
                    st.rerun()
                else:
                    st.error(f"Exchange Error: {exchange_data.get('error_message')}")
            else:
                st.error("Session not found yet. Did you finish the login in the other tab?")
                with st.expander("Technical Details"):
                    st.json(get_response)

# ==========================================
# STEP 3: Success State
# ==========================================
if st.session_state.access_token:
    st.success("🎉 Access Token Successfully Generated!")
    st.code(st.session_state.access_token)
    
    if st.button("Start New Connection"):
        st.session_state.link_token = None
        st.session_state.hosted_link_url = None
        st.session_state.access_token = None
        st.rerun()
