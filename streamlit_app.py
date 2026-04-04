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
    # Note: Double curly braces {{ }} are used so Python f-strings ignore them
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
                        // Send the token back to Streamlit using postMessage
                        window.parent.postMessage({{
                            type: 'streamlit:set
