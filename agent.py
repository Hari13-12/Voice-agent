from dotenv import load_dotenv
import asyncio
from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions, ChatContext
from livekit.plugins import (
    openai,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import Agent, function_tool,  RunContext
from visits_names import visit_details_list
from state_model import State
from livekit.plugins import google
load_dotenv(r"D:\Visit-Agent\.env")
 
class Assistant(Agent):
    def __init__(self, state: State):
        super().__init__(
    instructions="""
    You are a Voice assistant whose sole function is to deliver the visit information to user.
    As an agent, you must always start the conversation with a friendly greeting like 'Hi' or 'Hello', then mention that you are calling to provide visit information and ask how you can help.
   
    **Strict Rules:**
 
    1. **Greetings:**  
    If the user sends greetings (e.g., "Hi", "Hello", "Thanks"), reply politely and briefly (e.g., "Hello! How can I help you?").
 
    2. **Role/Functionality Queries:**  
    If the user asks about your capabilities, purpose, or who you are (e.g., "What can you do?", "Who are you?", "What is your function?"), reply politely like talking to user.
 
    3. **Out-of-Scope Requests:**  
    If the user asks anything unrelated to visit details (e.g., biography, celebrities, recipes, news, opinions, random text, etc.), strictly reply back in a polite manner that you are not capable of answering that question.
 
    4. **Random Queries:**
    If the user voice is random or does not make sense, reply saying that you could not understand.

    5. **Visit-Related Queries:**
               - For ANY question about visits (next visit, remaining visits, specific locations, visit status, etc.),
                 you MUST call the `return_state_response` tool immediately.
               - Never attempt to answer visit questions directly - always use the tool.
               - When responding with visit information, ONLY use the exact visit list provided by the tool.
               - NEVER generate or assume any visit locations - only use what the tool provides.
 
    **Critical Enforcement:**  
    - Never answer, acknowledge, or engage with off-topic queries—even partially.  
    - Never generate creative or default replies.  
    - Only respond according to the rules above.
    - Strictly never answer, acknowledge, or engage with out-of-scope queries—even partially.
    - **Always use the `return_state_response` tool for any question related to visits.**
    - **Never generate or assume visit locations - only use what the tool provides.**
 
    Always ensure that you are a voice assistant responding like a human talking to the user.
    """
)
 
        self.state = state
    async def visit_names(self) -> list[str]:
        return await visit_details_list(self.state)
 
    @function_tool
    async def return_state_response(self, ctx: RunContext):
        """
        You are a specialized tool that provides precise answers about the user's visit list.
        You MUST respond with exact information from the current visit list only.
        The LLM MUST NOT generate or assume any visit locations - it can ONLY use what this tool provides.
 
        Response Rules:
        1. For "next visit" questions:
        - "What is my next visit?" → "Your next visit is: [exact first item]"
        - "Where should I go next?" → "You should go to: [exact first item]"
 
        2. For list questions:
        - "What's left?" → List each remaining visit on separate lines with "-" bullets
        - "How many places left?" → "[number] visits remaining: [list of visits]"
        - "What is third visit?" → "You should go to: [exact third item]"
        - "What is my last visit?" → "You should go to: [exact last item]"
       
        3. For specific location queries:
        - "Have I been to [X]?" → "Yes, [X] is completed." or "No, [X] is still pending: [its position in list]"
        - "What's after [X]?" → "After [X] comes: [next item]" or "[X] is last/no visits left"
       
        4. If the list is empty:
        - ALWAYS respond: "Your visit list is currently empty."
 
        Never:
        - Add extra commentary beyond the required response
        - Make assumptions not in the list
        - Provide general information
        - Repeat the question in your answer
        - Generate or assume any visit locations
       
        Format responses exactly as shown in the examples above.
        """
        try:
            print(" Visit Tool")
            visit_list = await self.visit_names()
            print("Visit List:\n", visit_list)
            visit_str = "\n".join(f"- {v}" for v in visit_list) if visit_list else "No visits available"
            print("Visit STR:\n", visit_str)
            user_input = self.chat_ctx.to_dict()['items'][-1]['content']
 
            return {
                "visit_details": f"""User asked: {user_input}
    Here is your current visit list:
    {visit_str}
 
    Now respond to the user based on their question and the visit list above.
    IMPORTANT: You MUST ONLY use the visit list provided here. NEVER generate or assume any visit locations."""
            }
        except Exception as e:
            return {"visit_details": f"Error fetching visit details: {e}"}
 
async def entrypoint(ctx: agents.JobContext):
 
 
    try:
        state = State()
        state.user_id = "005fK000001oNIbQAM"
        session = AgentSession(
            llm=google.beta.realtime.RealtimeModel(
                voice="Charon",
            )
        )
 
       
       
        assistant = Assistant(state=state)
       
        await session.start(
            room=ctx.room,
            agent=assistant,
            room_input_options=RoomInputOptions(
                noise_cancellation=noise_cancellation.BVC(),
                # allow_interruptions=False,
            ),
        )
 
        await ctx.connect()
 
        await session.generate_reply(
            instructions="Greet the user and offer your assistance."
        )
        print("Partici Ep:",ctx.add_participant_entrypoint)
        print("Partici SIP:",ctx.add_sip_participant)
        print("Decode Token:",ctx.decode_token)
        print("Room Name:", ctx.room.name)
        # print("Room ID:", ctx.room.id)
        # print("Room Type:", ctx.room.type)
        # print("Room Status:", ctx.room.status)
        # print("Room Created At:", ctx.room.created_at)
        # print("Room Updated At:", ctx.room.updated_at)
        # print("Room Participants:", ctx.room.participants)
        
       
    except Exception as e:
        print(f"Error in entrypoint: {e}")
        raise
 
if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
   
 
 