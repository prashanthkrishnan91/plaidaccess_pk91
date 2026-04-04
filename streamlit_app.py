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
if st.secrets["PLAID_ENV"] == "production":
    host = "https://production.plaid.com"
elif st.secrets["PLAID_ENV"] == "development":
    host = "https://development.plaid.com"
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
    request = LinkTokenCreateRequest(
        products=[Products("investments")],
        client_name="My Financial App",
        country_codes=[CountryCode('US')],
        language='en',
        user=LinkTokenCreateRequestUser(client_user_id='unique-user-id')
    )
    response = client.link_token_create(request)
    return response['link_token']

# --- MAIN LOGIC ---
try:
    link_token = get_link_token()

   # 3. Custom Javascript Component for Plaid Link
if link_token:
    # We use a taller height and explicit sandbox permissions
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
                        // Send token back to the main Streamlit page
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
    # This height ensures the button isn't cut off and the iframe has room to breathe
    components.html(html_code, height=100)
else:
    st.error("No Link Token found. Check your Plaid credentials.")
