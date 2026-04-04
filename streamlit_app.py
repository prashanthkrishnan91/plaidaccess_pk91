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

# 3. Custom Javascript Component for Plaid Link
if link_token:
    # Hardcode your app URL to avoid the 'SecurityError' when trying to read window.top
    app_url = "https://plaidaccesspk91-yve3ncusxtuvh7npvjh4wu.streamlit.app/"
    
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
                (function() {{
                    const handler = Plaid.create({{
                        token: '{link_token}',
                        onSuccess: (public_token, metadata) => {{
                            // FIX: We SET window.top.location but we DO NOT READ it.
                            // This bypasses the Cross-Origin security error.
                            window.top.location.href = "{app_url}?public_token=" + public_token;
                        }},
                        onExit: (err, metadata) => {{
                            if (err != null) console.error('Plaid Exit Error:', err);
                        }}
                    }});

                    document.getElementById('link-button').onclick = function() {{
                        handler.open();
                    }};
                }})();
            </script>
        </body>
    </html>
    """
    components.html(html_code, height=60)
