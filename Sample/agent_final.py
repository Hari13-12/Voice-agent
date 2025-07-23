from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, Agent, RoomInputOptions, function_tool, RunContext
from livekit.plugins import openai, google, noise_cancellation
from visits_names import visit_details_list
from state_model import State
import json

load_dotenv(r"C:\Users\lenovo\Desktop\Sample\.env")



class Assistant(Agent):
    def __init__(self, state: State) -> None:
        super().__init__(instructions="""Hello, I am a Visit Agent. I'm here to help you with your visit details.
        You must introduce yourself to the user about you.
        You must reply like speaking in phone like a human agent.
        You have a list of visit details and from that list you must reply to the user according to the user's question.
        **INSTRUCTIONS:** 
        - You are not capable of capable of answering any other question than visit details.
        """)
        self.state = state

    async def visit_details(self):
        return await visit_details_list(self.state)

    @function_tool
    async def get_visits(self, ctx: RunContext):
        """ You are a tool helps to return the visit details of the user.
        Instructions:
- If the visit list is empty, reply: "Your visit list is currently empty." (No other text)
- If the user asks for the next visit: reply "Your next visit is: [first visit]"
- If the user asks "Where should I go next?": reply "You should go to: [first visit]"
- If the user asks "What's left?": list remaining visits as:
  - Visit 1
  - Visit 2
- If the user asks "How many places left?": reply "[N] visits remaining: Visit1, Visit2..."
- If the user asks "What is third visit?": reply "You should go to: [third visit]" (if it exists)
- If the user asks "What is my last visit?": reply "You should go to: [last visit]"
- If user asks "Have I been to [X]?":
   - If X is NOT in visit list: reply "Yes, [X] is completed."
   - If X IS in visit list: reply "No, [X] is still pending: position [index]"
- If user asks "What's after [X]?":
   - If X is in list and not last: "After [X] comes: [next visit]"
   - If X is last: "[X] is last/no visits left"
"""
        v = await visit_details_list(self.state)
        print("Tool",v)
        return f"Visit Details {v}"



async def entrypoint(ctx: agents.JobContext):

    await ctx.connect()
    participant = await ctx.wait_for_participant()  # Wait for a client to join
    pm = json.loads(participant.metadata)
    print(pm)
    print("User_id:", pm.get("user_id",""))
    print("Access_token:", pm.get("access_token",""))
    print("URL:",pm.get("url",""))
    state = State()
    state.user_id = pm.get("user_id","")
    state.access_token = pm.get("access_token","")
    state.url = pm.get("url","")
    assistant = Assistant(state=state)
    # print("O_token:",ctx._info.token)
    session = AgentSession(
        llm=google.beta.realtime.RealtimeModel(
            voice="Charon",
            language="en-IN",
        )
    )

    await session.start(
        room=ctx.room,
        agent=assistant,
        room_input_options=RoomInputOptions(
            noise_cancellation=noise_cancellation.BVC(),
        ),
    )

    # await ctx.connect()
    # participant = await ctx.wait_for_participant()  # Wait for a client to join
    # print("PI:",participant.identity)  # The identity field (e.g., 'visits-agent')
    # print("PM:",participant.metadata) 

    await session.generate_reply(
        instructions="Who are you?", allow_interruptions=False
    )

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
