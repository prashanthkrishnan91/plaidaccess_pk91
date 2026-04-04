import streamlit as st
import streamlit.components.v1 as components
import base64
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

# 1. System Configuration
st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

# Global Constant: MUST match Plaid Dashboard Redirect URI
APP_URL = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"

if 'link_token' not in st.session_state:
    st.session_state.link_token = None

# 2. Initialize Plaid Client
@st.cache_resource
def get_plaid_client():
    env = st.secrets.get("PLAID_ENV", "sandbox")
    host = "https://production.plaid.com" if env == "production" else "https://sandbox.plaid.com"
    conf = Configuration(
        host=host,
        api_key={
            'clientId': st.secrets["PLAID_CLIENT_ID"],
            'secret': st.secrets["PLAID_SECRET"],
        }
    )
    return plaid_api.PlaidApi(ApiClient(conf))

client = get_plaid_client()

# 3. Logic: Exchange Token
if "public_token" in st.query_params:
    public_token = st.query_params["public_token"]
    st.info("🔄 Exchanging public token...")
    try:
        exchange_req = ItemPublicTokenExchangeRequest(public_token=public_token)
        res = client.item_public_token_exchange(exchange_req)
        st.success("✅ Access Token Generated")
        st.code(res['access_token'])
        if st.button("Connect Another Account"):
            st.query_params.clear()
            st.session_state.link_token = None
            st.rerun()
        st.stop()
    except Exception as e:
        st.error(f"Exchange Error: {e}")

# 4. Logic: Generate Link Token
if not st.session_state.link_token:
    try:
        request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name="Plaid Access PK91",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique-id'),
            redirect_uri=APP_URL
        )
        response = client.link_token_create(request)
        st.session_state.link_token = response['link_token']
    except Exception as e:
        st.error(f"API Error: {e}")

# 5. The UI Component (The "100% Reliable" Popup)
if st.session_state.link_token:
    link_token = st.session_state.link_token
    
    # Check for OAuth Return
    received_uri = ""
    if "oauth_state_id" in st.query_params:
        query_string = "&".join([f"{k}={v}" for k, v in st.query_params.items()])
        received_uri = f"{APP_URL}?{query_string}"

    # We build the popup HTML without any Python-side f-string indentation issues
    popup_content = f"""<!DOCTYPE html>
<html>
<head><script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script></head>
<body style="margin:0;display:flex;justify-content:center;align-items:center;height:100vh;font-family:sans-serif;background:#fafafa;">
    <div style="text-align:center;padding:20px;border:1px solid #ddd;background:#fff;border-radius:8px;">
        <h3 id="m">Connecting to Plaid...</h3>
    </div>
    <script>
        const start = () => {{
            if(!window.Plaid) return setTimeout(start, 50);
            const h = Plaid.create({{
                token: '{link_token}',
                {f"receivedRedirectUri: '{received_uri}'," if received_uri else ""}
                onSuccess: (t) => {{ window.opener.location.href = "{APP_URL}?public_token=" + t; window.close(); }},
                onExit: (e) => {{ if(!e) window.close(); else document.getElementById('m').innerText = e.error_message; }}
            }});
            h.open();
        }};
        start();
    </script>
</body>
</html>"""

    # Encode to Base64 to ensure no character mangling
    b64_popup = base64.b64encode(popup_content.encode()).decode()
    
    # The Button Iframe
    button_html = f"""
    <button id="b" style="width:100%;padding:15px;background:#00ADEE;color:#fff;border:none;border-radius:5px;font-size:16px;font-weight:bold;cursor:pointer;">
        Connect to Robinhood
    </button>
    <script>
        document.getElementById('b').onclick = () => {{
            const dataUri = 'data:text/html;base64,{b64_popup}';
            window.open(dataUri, '_blank', 'width=500,height=700');
        }};
    </script>
    """
    components.html(button_html, height=100)
