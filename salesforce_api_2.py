from state import State
from datetime import date
from requests import Session
import logging
from error_handler import ErrorHandler
 
# Configure logging
logger = logging.getLogger(__name__)
 
async def visit_details_list(state: State):
    try:
        user_id = state.user_id
        access_token = state.access_token
        print("User_id in state:", user_id)
        print("Access_token in state:", access_token)
       
        # Validate required parameters
        if not user_id or not access_token:
            logger.error("Missing required parameters: user_id or access_token")
            return ["No visit details available - missing authentication"]
       
        s = Session()
        today = date.today()
        today = today.strftime("%Y-%m-%d")
        API_ENDPOINT = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"
 
        headers = {
            "Authorization": "Bearer " + access_token,
            "Content-Type": "application/json",
        }
        body = {
            "keyword": "MarketVisit",
            "conditionName": "Planned_Date_Filter",
            "parameters": [
                {"name": "planneddate", "value": today},
                {"name": "UserId", "value": user_id},
            ],
        }
        print(body)
       
        # Make API request with error handling
        response = s.post(API_ENDPOINT, json=body, headers=headers)
        print("Response:", response)
       
        # Handle HTTP errors
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return [f"Unable to fetch visit details (Error {response.status_code})"]
       
        # Parse response with error handling using ErrorHandler
        try:
            response_data = ErrorHandler.handle_api_response(response, default_value=[])
            if not response_data:
                logger.error("Failed to parse API response")
                return ["No visit details available - API response error"]
           
            # Handle different response formats
            if isinstance(response_data, dict):
                rec = response_data.get("records", [])
            elif isinstance(response_data, list):
                rec = response_data  # If response is already a list
            else:
                logger.error(f"Unexpected response format: {type(response_data)}")
                return ["No visit details available - unexpected data format"]
           
            accountid = []
            accountname = []
           
            # Process records with error handling
            for i in range(len(rec)):
                try:
                    # Use safe_get to avoid KeyError exceptions
                    parent_record = rec[i].get("parentRecord", {})
                    status = ErrorHandler.safe_get(rec[i], "parentRecord.Status")
                   
                    if status == "Planned":
                        account_id = ErrorHandler.safe_get(rec[i], "parentRecord.AccountId", "")
                        account_name = ErrorHandler.safe_get(rec[i], "parentRecord.AccountName", "")
                        accountid.append(account_id)
                        accountname.append(account_name)
                except (KeyError, TypeError, IndexError) as e:
                    logger.error(f"Error processing record {i}: {str(e)}")
                    continue
           
            if not accountname:
                return ["List is empty"]
               
            return accountname
           
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            return ["Unable to parse visit details"]
           
    except Exception as e:
        logger.error(f"Unexpected error in visit_details_list: {str(e)}")
        logger.error(ErrorHandler.format_exception())
        return ["An error occurred while fetching visit details"]
 
 
async def fetch_orders_by_account_id(state: State, account_id: str):
    logger.info("Inside fetch_orders_by_account_id")
    logger.info(f"Account ID: {account_id}")
    try:
        user_id = state.user_id
        access_token = state.access_token
        url = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"
   
        payload = {
            "keyword": "Order",
            "conditionName": "AccountId_Filter",
            "parameters": [
                {"name": "userId", "value": user_id},
                {"name": "AccountId", "value": account_id["Id"]},
                {"name": "OrderType", "value": "Order"}
            ]
        }
   
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
        s = Session()
        # response = requests.post(url, json=payload, headers=headers)
        response = s.post(url, json=payload, headers=headers)
        print("Response:", response)
 
        if response.status_code != 200:
            logger.error(f"API error: {response.status_code} - {response.text}")
            return [f"Unable to fetch visit details (Error {response.status_code})"]
 
        try:
 
            response_data = ErrorHandler.handle_api_response(response, default_value=[])
            if not response_data:
                logger.info("Failed to parse API response")
            orders = []
            for r in response_data.get("records", []):
                parent = r.get("parentRecord", {})
                items = r.get("childRecords", [])
       
                orders.append({
                    "orderNumber": parent.get("OrderNumber"),
                    "orderDate": parent.get("EffectiveDate"),
                    "totalAmount": parent.get("TotalAmount"),
                    "items": [
                        {
                            "productName": i.get("ProductName"),
                            "quantity": i.get("Quantity"),
                            "unitPrice": i.get("UnitPrice"),
                            "totalPrice": i.get("TotalPrice")
                        }
                        for i in items
                    ]}
                )
            logger.info(f"Fetched orders: {orders}")
            return orders
 
        except ValueError as e:
            logger.error(f"JSON parsing error: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            return ["Unable to parse visit details"]
   
    except Exception as e:
        logger.error(f"Unexpected error in fetch_orders_by_account_id: {str(e)}")
        return ["An error occurred while fetching orders"]
   
 
async def fetch_customer_details_by_account_id(state: State,
        account_id: str
    ):
    logger.info("Inside fetch_customer_details_by_account_id")
    logger.info(f"Account ID: {account_id}")
    try:
        access_token = state.access_token
        url = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"
     
        payload = {
            "keyword": "Account",
            "conditionName": "AccountId_Filter",
            "parameters": [
                {"name": "AccountId", "value": account_id}
            ]
        }
 
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
 
        # response = requests.post(url, json=payload, headers=headers)
        # response.raise_for_status()
        # data = response.json()
        s = Session()
        response = s.post(url, json=payload, headers=headers)
        data = ErrorHandler.handle_api_response(response, default_value=[])
        print("Response:", response)
        if not data.get("records"):
            return None
 
        parent = data["records"][0].get("parentRecord", {})
 
        return {
            "id": parent.get("Id"),
            "name": parent.get("Name"),
            "accountNumber": parent.get("AccountNumber"),
            "type": parent.get("Type"),
            "industry": parent.get("Industry"),
            "yearStarted": parent.get("YearStarted"),
            "website": parent.get("Website"),
            "contactPersonName": parent.get("Contact_Person_Name"),
            "email": parent.get("Email"),
            "phone": parent.get("Phone"),
            "whatsappNumber": parent.get("WhatsApp_Number"),
            "rating": parent.get("Rating"),
            "ownerId": parent.get("OwnerId"),
            "locationLat": parent.get("Location_Lat"),
            "locationLong": parent.get("Location_Long"),
            "pan": parent.get("PAN"),
            "gstin": parent.get("GSTIN"),
            "taxId": parent.get("Tax_Id"),
            "bankAccountNo": parent.get("Bank_Account_No"),
            "bankIFSCCode": parent.get("Bank_IFSC_Code"),
            "adhaar": parent.get("Adhaar"),
            "gstType": parent.get("GST_Type"),
            "billingStreet": parent.get("BillingStreet"),
            "billingCity": parent.get("BillingCity"),
            "billingPostalCode": parent.get("BillingPostalCode"),
            "billingState": parent.get("BillingState"),
            "billingCountry": parent.get("BillingCountry"),
            "shippingStreet": parent.get("ShippingStreet"),
            "shippingCity": parent.get("ShippingCity"),
            "shippingPostalCode": parent.get("ShippingPostalCode"),
            "shippingState": parent.get("ShippingState"),
            "shippingCountry": parent.get("ShippingCountry"),
            "category": parent.get("Category"),
            "classification": parent.get("Classification"),
            "market": parent.get("Market"),
            "beatId": parent.get("BeatId"),
            "beatName": parent.get("BeatName"),
            "irrigationType": parent.get("Irrigation_Type"),
            "totalAcreage": parent.get("Total_Acreage"),
            "storeOpeningTime": parent.get("Store_Opening_Time"),
            "status": parent.get("Status")
        }
   
    except Exception as e:
        logger.error(f"Unexpected error in fetch_customer_details_by_account_id: {str(e)}")
        return None
 
async def place_order_api(session, state: State,payload: dict):
    try:
        logger.info("Creating a lead for the order")
        logger.info(f"Payload: {payload}")
        access_token = state.access_token
        SALESFORCE_COMPOSITE_URL = (
            "https://platform-computing-1141--uatraymond.sandbox.my.salesforce.com"
            "/services/data/v64.0/composite/"
        )
 
        payload = {
            "compositeRequest": [
                {
                    "method": "POST",
                    "url": "/services/data/v64.0/sobjects/Lead",
                    "referenceId": "refLead",
                    "body": {
                        "LastName":  payload["customer_name"],
                        "Company": payload["account_id"],
                        "MobilePhone": payload["cart"][0]["qty"],
                        "Promotion_Feedback__c": payload["cart"][0]["product_id"],
                    },
                }
            ]
        }
 
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
 
        async with session.post(
            SALESFORCE_COMPOSITE_URL,
            json=payload,
            headers=headers,
        ):
            logger.info("Lead created successfully")
            pass   # intentionally ignore response
 
    except Exception as e:
        logger.error(f"Error while creating lead {e}")
 
 
 
 