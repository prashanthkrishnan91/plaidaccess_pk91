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

st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")
st.title("🏦 Plaid Access Token Generator")

# 1. Setup Plaid Client Configuration
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

# 2. Generate Link Token
@st.cache_data(show_spinner="Generating Link Token...")
def get_link_token():
    try:
        request = LinkTokenCreateRequest(
            products=[Products("investments")],
            client_name="My Financial App",
            country_codes=[CountryCode('US')],
            language='en',
            user=LinkTokenCreateRequestUser(client_user_id='unique-user-id')
        )
        response = client.link_token_create(request)
        return response['link_token']
    except Exception as e:
        st.error(f"Error generating Link Token: {e}")
        return None

# --- MAIN LOGIC ---
link_token = get_link_token()

if link_token:
    # 3. Custom Javascript Component for Plaid Link
    html_code = f"""
    <html>
        <head>
            <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
        </head>
        <body style="margin: 0;">
            <button id="link-button" style="background-color: #00ADEE; color: white; border: none; padding: 12px; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%; font-family: sans-serif;">
                Connect Robinhood
            </button>
            <script>
                const handler = Plaid.create({{
                    token: '{link_token}',
                    onSuccess: (public_token, metadata) => {{
                        const url = new URL(window.parent.location.href);
                        url.searchParams.set('public_token', public_token);
                        window.parent.location.href = url.href;
                    }},
                    onExit: (err, metadata) => {{
                        if (err != null) console.error(err);
                    }}
                }});
                document.getElementById('link-button').onclick = function() {{
                    handler.open();
                }};
            </script>
        </body>
    </html>
    """
    components.html(html_code, height=100, scrolling=False)

# 4. Check for public_token in URL and exchange it
if "public_token" in st.query_params:
    public_token = st.query_params["public_token"]
    st.success("Public Token received! Exchanging...")
    
    try:
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        st.subheader("Your Access Token")
        st.code(exchange_response['access_token'])
        st.info("Copy this to your other Robinhood app's secrets.")
        
        if st.button("Clear Token from Screen"):
            st.query_params.clear()
            st.rerun()
            
    except Exception as exchange_error:
        st.error(f"Exchange Error: {exchange_error}")
