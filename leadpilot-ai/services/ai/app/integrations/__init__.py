from app.integrations.base import IntegrationError
from app.integrations.slack import SlackAdapter
from app.integrations.hubspot import HubSpotAdapter
from app.integrations.gmail import EmailAdapter
from app.integrations.sheets import GoogleSheetsAdapter
from app.integrations.airtable import AirtableAdapter
from app.integrations.telegram import TelegramAdapter
from app.integrations.shopify import ShopifyAdapter
from app.integrations.vapi import VapiAdapter

# Global adapter singletons
slack_adapter = SlackAdapter()
hubspot_adapter = HubSpotAdapter()
email_adapter = EmailAdapter()
sheets_adapter = GoogleSheetsAdapter()
airtable_adapter = AirtableAdapter()
telegram_adapter = TelegramAdapter()
shopify_adapter = ShopifyAdapter()
vapi_adapter = VapiAdapter()
