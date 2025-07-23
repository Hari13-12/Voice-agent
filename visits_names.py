from state_model import State
from datetime import date
from requests import  Session


async def visit_details_list(state: State):
    user_id = state.user_id
    access_token = state.access_token
    print("User_id in state:", user_id)
    print("Access_token in state:", access_token)
    # state.response = "There is no visit details to display"
    s = Session()
    today = date.today()
    today = today.strftime("%Y-%m-%d")
    # print("Date: ",today)
    url = state.url
    API_ENDPOINT = url+"/services/apexrest/APTLDataRequest"
    print("API_ENDPOINT:",API_ENDPOINT)

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
        
        ]
    }
    response = s.post(API_ENDPOINT, json=body, headers=headers)
    print("Response:",response)
    rec = response.json().get("records", [])
    # print("Input:",state["messages"][-1].content)
    accountid = []
    accountname = []
    for i in range(len(rec)):
        if rec[i]["parentRecord"]["Status"] == "Planned":
            accountid.append(rec[i]["parentRecord"]["AccountId"])
            accountname.append(rec[i]["parentRecord"]["AccountName"])
    print("Visit API")
    print(accountname)
    return accountname
    