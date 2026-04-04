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

# Basic App Config
st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

# 1. Setup Plaid Client
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
except Exception:
    st.error("Check your Streamlit Secrets for PLAID_CLIENT_ID and PLAID_SECRET.")
    st.stop()

# 2. Token Exchange Logic (Catch the token from the URL)
if "public_token" in st.query_params:
    public_token = st.query_params["public_token"]
    st.info("🔄 Exchanging public token...")
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        st.success("✅ Access Token Generated!")
        st.subheader("Your Access Token:")
        st.code(exchange_response['access_token'])
        
        if st.button("Start Over"):
            st.query_params.clear()
            st.rerun()
        st.stop()
    except Exception as e:
        st.error(f"Exchange failed: {e}")
        if st.button("Try again"):
            st.query_params.clear()
            st.rerun()

# 3. Generate Link Token
@st.cache_data(show_spinner="Preparing Plaid Link...")
def get_link_token():
    try:
        # CRITICAL: This URL must match your Plaid Dashboard Redirect URIs exactly
        redirect_uri = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"
        
        request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name="Plaid Access PK91",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique-user-id'),
            redirect_uri=redirect_uri  # Required for Robinhood/OAuth
        )
        response = client.link_token_create(request)
        return response['link_token']
    except Exception as e:
        st.error(f"Failed to create link token: {e}")
        return None

# 4. Render Link Button
link_token = get_link_token()

if link_token:
    html_code = f"""
    <html>
        <head>
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        </head>
        <body style="margin: 0; padding: 0;">
            <button id="link-button" style="background-color: #00ADEE; color: white; border: none; padding: 12px; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; font-family: sans-serif; font-weight: bold;">
                Connect Robinhood
            </button>
            <script>
                const handler = Plaid.create({{
                    token: '{link_token}',
                    onSuccess: (public_token, metadata) => {{
                        // We use window.top to escape the 'null' origin iframe
                        const url = new URL(window.top.location.href);
                        url.searchParams.set('public_token', public_token);
                        window.top.location.href = url.href;
                    }},
                    onExit: (err, metadata) => {{
                        if (err != null) console.error('Plaid Exit:', err);
                    }}
                }});
                document.getElementById('link-button').onclick = function() {{
                    handler.open();
                }};
            </script>
        </body>
    </html>
    """
    components.html(html_code, height=60)
