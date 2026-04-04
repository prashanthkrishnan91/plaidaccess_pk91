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

# 1. Page Configuration
st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

# 2. Setup Plaid Client
try:
    if st.secrets.get("PLAID_ENV") == "production":
        host = "https://production.plaid.com"
    else:
        host = "https://sandbox.plaid.com"

    configuration = Configuration(
        host=host,
        api_key={
            'clientId': st.secrets["PLAID_CLIENT_ID"],
            'secret': st.secrets["PLAID_SECRET"],
        }
    )
    api_client = ApiClient(configuration)
    client = plaid_api.PlaidApi(api_client)
except Exception as e:
    st.error(f"Configuration Error: {e}")
    st.stop()

# 3. Handle Token Exchange (When redirecting back from Plaid)
if "public_token" in st.query_params:
    public_token = st.query_params["public_token"]
    st.info("🔄 Received Public Token. Exchanging for Access Token...")
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        st.success("✅ Success! Access Token Generated.")
        st.subheader("Your Access Token:")
        st.code(exchange_response['access_token'])
        
        if st.button("Start New Connection"):
            st.query_params.clear()
            st.rerun()
        st.stop()
    except Exception as exchange_err:
        st.error(f"Exchange failed: {exchange_err}")

# 4. Define Link Token Generator
@st.cache_data(show_spinner="Preparing Plaid Connection...")
def generate_link_token():
    try:
        # This MUST match your Plaid Dashboard Redirect URI exactly
        redirect_uri = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"
        
        request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name="Plaid Access PK91",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique-user-id'),
            redirect_uri=redirect_uri
        )
        response = client.link_token_create(request)
        return response['link_token']
    except Exception as e:
        st.error(f"Plaid API Error: {e}")
        return None

# 5. Main Execution Flow
link_token = generate_link_token()

if link_token:
    # Hardcode the redirect to avoid 'SecurityError' (Invalid target origin)
    app_url = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"
    
    html_code = f"""
    <html>
        <head>
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        </head>
        <body style="margin: 0; padding: 0;">
            <button id="link-button" style="background-color: #00ADEE; color: white; border: none; padding: 14px; border-radius: 6px; cursor: pointer; font-size: 16px; width: 100%; font-family: sans-serif; font-weight: bold; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                Connect to Robinhood
            </button>
            <script>
                (function() {{
                    const handler = Plaid.create({{
                        token: '{link_token}',
                        onSuccess: (public_token, metadata) => {{
                            // We SET window.top.location but we DO NOT READ it.
                            // This bypasses the Cross-Origin 'null' origin error.
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
    st.warning("Could not initialize Plaid. Please check your credentials in Streamlit Secrets.")
