from state_model import State
from llm_manager import LLMManger
from datetime import date
from requests import  Session
from access_token import get_salesforce_access_token
from langchain_core.messages import HumanMessage,SystemMessage
import pprint 

def visit_details(state: State, user_input:str):
    llm = LLMManger()
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
            {"name": "planneddate", "value": today},
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
    # print("Shop Details",accountname)
    prompt = """
*You are a helpful assistant that manages my visit list, which contains the following shops I plan to visit next:
visit_list = {visits_list}

Your task is to answer any questions I have about this list, such as:
Respond to my questions in a friendly, conversational way, like a friend helping me plan my errands

"What is my next visit?" → Reply with the first item in the list.

"Where should I go next?" → Suggest the next pending visit (first item).

"Whats left on my visit list?" → List all remaining shops in order.

"Have I been to [X] yet?" → Check if [X] is visited (assume items are removed after visiting).

"How many places are left?" → Count and return the number of pending visits.

"Whats after [X]?" → Return the shop immediately after [X] in the list.

Assume the list is ordered and mutable (changes as I visit/update). Keep answers concise and action-oriented.
If the list is empty, say: "Your visit list is empty!"
"""
    prompt = prompt.format(visits_list = accountname )
    system_prompt = SystemMessage(content= prompt)
        
    input_message = HumanMessage(content=user_input)
    response = llm.invoke([system_prompt, input_message])
    state.response = response.content
    return state
