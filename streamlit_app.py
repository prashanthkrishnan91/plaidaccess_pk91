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

# 1. Page Config & State Initialization
st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

if 'link_token' not in st.session_state:
    st.session_state.link_token = None

app_url = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"

# 2. Setup Plaid Client
try:
    env = st.secrets.get("PLAID_ENV", "sandbox")
    host = "https://production.plaid.com" if env == "production" else "https://sandbox.plaid.com"
    configuration = Configuration(
        host=host,
        api_key={
            'clientId': st.secrets["PLAID_CLIENT_ID"],
            'secret': st.secrets["PLAID_SECRET"],
        }
    )
    client = plaid_api.PlaidApi(ApiClient(configuration))
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# 3. Generate Link Token
def generate_link_token():
    try:
        request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name="Plaid Access PK91",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique-user-id'),
            redirect_uri=app_url
        )
        response = client.link_token_create(request)
        return response['link_token']
    except Exception as e:
        st.error(f"Plaid API Error: {e}")
        return None

# 4. Routing Flow
if "public_token" in st.query_params:
    public_token = st.query_params["public_token"]
    st.info("🔄 Exchanging for Access Token...")
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        st.success("✅ Success! Access Token Generated.")
        st.code(exchange_response['access_token'])
        if st.button("Start New Connection"):
            st.session_state.link_token = None
            st.query_params.clear()
            st.rerun()
    except Exception as err:
        st.error(f"Exchange failed: {err}")
else:
    if not st.session_state.link_token:
        st.session_state.link_token = generate_link_token()
    
    link_token = st.session_state.link_token
    
    if link_token:
        received_uri = ""
        if "oauth_state_id" in st.query_params:
            st.info("🔄 Robinhood authorization received. Finalize connection below.")
            query_string = "&".join([f"{k}={v}" for k, v in st.query_params.items()])
            received_uri = f"{app_url}?{query_string}"
            btn_text = "Finish Robinhood Connection"
        else:
            btn_text = "Connect to Robinhood"

        # 5. The Magic Popup Breakout
        popup_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        </head>
        <body style="font-family:sans-serif; display:flex; justify-content:center; align-items:center; height:100vh; background:#f4f4f4;">
            <div style="text-align:center; background:white; padding:30px; border-radius:8px; box-shadow:0 4px 12px rgba(0,0,0,0.1);">
                <h3 id="msg">Initializing Plaid...</h3>
            </div>
            <script>
                function start() {{
                    if (!window.Plaid) {{ setTimeout(start, 100); return; }}
                    const handler = Plaid.create({{
                        token: '{link_token}',
                        {f"receivedRedirectUri: '{received_uri}'," if received_uri else ""}
                        onSuccess: (public_token) => {{
                            window.location.href = "{app_url}?public_token=" + public_token;
                        }},
                        onExit: (err) => {{ 
                            if (err) document.getElementById('msg').innerHTML = "<span style='color:red;'>Error: " + err.error_message + "</span>"; 
                            else window.close();
                        }}
                    }});
                    handler.open();
                }}
                start();
            </script>
        </body>
        </html>
        """
        
        b64_html = base64.b64encode(popup_html.encode('utf-8')).decode('utf-8')
        
        btn_html = f"""
        <html>
            <body style="margin:0; padding:10px;">
                <button id="btn" style="background-color:#00ADEE; color:white; border:none; padding:16px; border-radius:6px; cursor:pointer; font-size:16px; width:100%; font-weight:bold;">
                    {btn_text}
                </button>
                <script>
                    document.getElementById('btn').onclick = function() {{
                        const w = window.open("", "_blank", "width=500,height=700");
                        const decoded = decodeURIComponent(escape(window.atob('{b64_html}')));
                        w.document.open();
                        w.document.write(decoded);
                        w.document.close();
                    }};
                </script>
            </body>
        </html>
        """
        components.html(btn_html, height=100)
