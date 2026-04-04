import streamlit as st
import streamlit.components.v1 as components
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.configuration import Configuration
from plaid.api_client import ApiClient

# 1. Setup Page
st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

# 2. Client Initialization
def get_plaid_client():
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
        return plaid_api.PlaidApi(ApiClient(configuration))
    except Exception as e:
        st.error(f"Configuration Error: {e}")
        return None

client = get_plaid_client()

# 3. Success Flow: Exchange Public Token
# Catch the token from the URL after the Plaid redirect
if "public_token" in st.query_params:
    public_token = st.query_params["public_token"]
    st.info("🔄 Received Public Token. Exchanging for Access Token...")
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        st.success("✅ Access Token Generated Successfully!")
        st.subheader("Your Access Token:")
        st.code(exchange_response['access_token'])
        
        if st.button("Start New Connection"):
            st.query_params.clear()
            st.rerun()
        st.stop()
    except Exception as e:
        st.error(f"Exchange failed: {e}")
        if st.button("Reset App"):
            st.query_params.clear()
            st.rerun()

# 4. Generate Link Token
@st.cache_data(show_spinner="Preparing Plaid...")
def get_link_token():
    if not client: return None
    try:
        # CRITICAL: This URL must match your Plaid Dashboard exactly
        redirect_uri = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"
        
        request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name="Plaid Access Generator",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique-user-id'),
            redirect_uri=redirect_uri
        )
        response = client.link_token_create(request)
        return response['link_token']
    except Exception as e:
        st.error(f"Plaid Link Token Error: {e}")
        return None

# 5. Main UI
if client:
    link_token = get_link_token()
    if link_token:
        # Use a hardcoded URL for the redirect to bypass 'null' origin security errors
        app_url = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"
        
        html_code = f"""
        <html>
            <head>
                <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
                <style>
                    #link-button {{
                        background-color: #00ADEE;
                        color: white;
                        border: none;
                        padding: 14px 24px;
                        border-radius: 8px;
                        cursor: pointer;
                        font-size: 16px;
                        font-weight: bold;
                        width: 100%;
                        transition: 0.2s;
                    }}
                    #link-button:hover {{ background-color: #008fca; }}
                </style>
            </head>
            <body style="margin: 0;">
                <button id="link-button">Connect to Robinhood</button>
                <script>
                    (function() {{
                        const handler = Plaid.create({{
                            token: '{link_token}',
                            onSuccess: (public_token, metadata) => {{
                                // Direct window redirect to bypass iframe postMessage restrictions
                                window.top.location.href = "{app_url}?public_token=" + public_token;
                            }},
                            onExit: (err, metadata) => {{
                                if (err != null) console.error('Plaid Exit:', err);
                            }}
                        }});
                        document.getElementById('link-button').onclick = () => handler.open();
                    }})();
                </script>
            </body>
        </html>
        """
        components.html(html_code, height=80)
    else:
        st.warning("Could not generate Plaid Link token. Check app logs.")
