from state_model import State
from datetime import date
from requests import  Session
from access_token import get_salesforce_access_token


async def visit_details_list(state: State):
    # print("Inside VISIT API")
    user_id = state.user_id
    # print("User_id in state:", user_id)
    state.response = "There is no visit details to display"
    s = Session()
    today = date.today()
    today = today.strftime("%Y-%m-%d")
    access_token = get_salesforce_access_token()
    # print("Date: ",today)
    API_ENDPOINT = "https://appstrail-sfa-dev-ed.develop.my.salesforce.com/services/apexrest/APTLDataRequest"

    headers = {
        "Authorization": "Bearer " + access_token,
        "Content-Type": "application/json",
        
    }
    body = {
        "keyword": "MarketVisit",
        "conditionName": "Planned_Date_Filter",
        "parameters": [
            {"name": "planneddate", "value": "2025-07-09"},
            {"name": "UserId", "value": user_id},
        
        ]
    }
    response = s.post(API_ENDPOINT, json=body, headers=headers)
    rec = response.json().get("records", [])
    # pprint.pprint(rec)
    # print("Input:",state["messages"][-1].content)
    accountid = []
    accountname = []
    for i in range(len(rec)):
        if rec[i]["parentRecord"]["Status"] == "Planned":
            accountid.append(rec[i]["parentRecord"]["AccountId"])
            accountname.append(rec[i]["parentRecord"]["AccountName"])
    print("Visit API")
    # print(accountname)
    return accountname
    