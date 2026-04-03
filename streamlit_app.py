import streamlit as st
from plaid.api import plaid_api
from plaid.model.link_token_create_request import LinkTokenCreateRequest
from plaid.model.link_token_create_request_user import LinkTokenCreateRequestUser
from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
from plaid.model.products import Products
from plaid.model.country_code import CountryCode
from plaid.configuration import Configuration
from plaid.api_client import ApiClient
from streamlit_plaid_link import streamlit_plaid_link

st.set_page_config(page_title="Plaid Token Generator", page_icon="🏦")

st.title("🏦 Plaid Access Token Generator")
st.info("Use this to get your Access Token for the Robinhood integration.")

# 1. Setup Plaid Client Configuration
# Use st.secrets for your ID and Secret (Set these in Streamlit Cloud Dashboard)
configuration = Configuration(
    host=ApiClient.Production if st.secrets["PLAID_ENV"] == "production" else ApiClient.Sandbox,
    api_key={
        'clientId': st.secrets["PLAID_CLIENT_ID"],
        'secret': st.secrets["PLAID_SECRET"],
    }
)
api_client = ApiClient(configuration)
client = plaid_api.PlaidApi(api_client)

# 2. Generate a Link Token
@st.cache_data(show_spinner="Generating Link Token...")
def get_link_token():
    request = LinkTokenCreateRequest(
        products=[Products("investments")], # Required for Robinhood/Brokerages
        client_name="My Financial App",
        country_codes=[CountryCode('US')],
        language='en',
        user=LinkTokenCreateRequestUser(client_user_id='unique-user-id')
    )
    response = client.link_token_create(request)
    return response['link_token']

try:
    link_token = get_link_token()

    # 3. Display the Plaid Link Button
    # This component handles the JS popup for you
    response = streamlit_plaid(link_token)

    if response and "public_token" in response:
        st.success("Public Token received! Exchanging for Access Token...")
        
        # 4. Exchange Public Token for Access Token
        exchange_request = ItemPublicTokenExchangeRequest(
            public_token=response["public_token"]
        )
        exchange_response = client.item_public_token_exchange(exchange_request)
        
        access_token = exchange_response['access_token']
        item_id = exchange_response['item_id']

        st.subheader("Your Credentials")
        st.code(f"PLAID_ACCESS_TOKEN = '{access_token}'", language="python")
        st.warning("Copy this token and save it in your other app's Secrets. Do not share it!")
        st.write(f"**Item ID:** {item_id}")

except Exception as e:
    st.error(f"Error: {str(e)}")
    st.write("Ensure your Plaid Dashboard has 'investments' enabled and your redirect URIs are configured if using Production.")
