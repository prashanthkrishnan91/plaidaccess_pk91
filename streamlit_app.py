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

try:
    link_token = get_link_token()

   # 3. Custom Javascript Component for Plaid Link
    html_code = f"""
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <button id="link-button" style="background-color: #00ADEE; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px; width: 100%;">
        Connect Robinhood
    </button>
    <script>
    const handler = Plaid.create({{
      token: '{link_token}',
      onSuccess: (public_token, metadata) => {{
        // Send the token back to Streamlit via the URL
        const url = new URL(window.location.href);
        url.searchParams.set('public_token', public_token);
        window.parent.location.href = url.href;
      }},
    }});
    document.getElementById('link-button').onclick = () => handler.open();
    </script>
"""

# Render the button
    components.html(html_code, height=60)

# Check if the token is in the URL parameters
    query_params = st.query_params
    if "public_token" in query_params:
        public_token = query_params["public_token"]
        
        st.success("Public Token received! Exchanging...")
        
        try:
            exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
            exchange_response = client.item_public_token_exchange(exchange_request)
            
            st.subheader("Your Access Token")
            st.code(exchange_response['access_token'])
            st.info("Copy this to your other Robinhood app's secrets.")
            
            # Clear the param so it doesn't re-run infinitely
            if st.button("Clear Token from Screen"):
                st.query_params.clear()
            
except Exception as e:
    st.error(f"Exchange Error: {e}")
