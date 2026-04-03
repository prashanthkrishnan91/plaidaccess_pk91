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

# 1. Setup Plaid Client
configuration = Configuration(
    host=ApiClient.Production if st.secrets["PLAID_ENV"] == "production" else ApiClient.Sandbox,
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
    # This replaces the need for "streamlit-plaid-link"
    html_code = f"""
    <script src="https://cdn.plaid.com/link/v2/stable/link-initialize.js"></script>
    <button id="link-button" style="background-color: #00ADEE; color: white; border: none; padding: 10px 20px; border-radius: 5px; cursor: pointer; font-size: 16px;">
        Connect Robinhood
    </button>
    <script>
    const handler = Plaid.create({{
      token: '{link_token}',
      onSuccess: (public_token, metadata) => {{
        window.parent.postMessage({{
            type: 'streamlit:setComponentValue',
            value: public_token
        }}, '*');
      }},
    }});
    document.getElementById('link-button').onclick = () => handler.open();
    </script>
    """
    
    # Render the button and capture the public_token when returned
    public_token = components.html(html_code, height=60)

    if public_token:
        st.success("Public Token received! Exchanging...")
        exchange_request = ItemPublicTokenExchangeRequest(public_token=public_token)
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        st.subheader("Your Access Token")
        st.code(exchange_response['access_token'])
        st.info("Copy this to your other Robinhood app's secrets.")

except Exception as e:
    st.error(f"Setup Error: {e}")
