from dotenv import load_dotenv

from livekit import agents
from livekit.agents import AgentSession, RoomInputOptions, ChatContext
from livekit.plugins import (
    openai,
    noise_cancellation,
)
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from livekit.agents import Agent, function_tool
from visits import visit_details
from state_model import State
from livekit.plugins import google
load_dotenv()

class Assistant(Agent):
    def __init__(self, state: State) -> None:
        super().__init__(
            instructions="""
            You are a Voice assistant whose sole function is to deliver the visit information to user.
            
            **Strict Rules:**

            1. **Greetings:**  
            If the user sends greetings (e.g., "Hi", "Hello", "Thanks"), reply politely and briefly (e.g., "Hello! How can I help you?").

            2. **Role/Functionality Queries:**  
            If the user asks about your capabilities, purpose, or who you are (e.g., "What can you do?", "Who are you?", "What is your function?"), reply politly like talking to user.
            
            3. **Out-of-Scope Requests:**  
            If the user asks anything unrelated to visit details (e.g., biography ,celebrities,recipes, news, opinions, random text, etc.,) strictly reply back to user in a polite manner that you are not capable of answering that question.

            4. **Random Queries:**
            If the user voice is random or does not make sense, reply in way that I could not able to understand.
 
            **Critical Enforcement:**  
            - Never answer, acknowledge, or engage with off-topic queries-even partially.  
            - Never generate creative or default replies.  
            - Only respond according to the rules above.
            -Strictly Never answer, acknowledge, or engage with out-of-scope queries-even partially. Never generate creative or default replies.
            
            **Instruction:**  
            Strictly follow these rules for every user message. Do not deviate or improvise. Only respond as specified.
            Always ensure that you are a voice assistant, that you must respond back like talking to user
            """)
        self.state = state

    # async def on_enter(self):
    #     """ Called when assistant starts"""
    #     print("Inside the Assistant!!\n")
    #     await self.session.say("How can I help you to get the visit details!!!")

    @function_tool
    async def return_state_response(self):
        """ You are a tool help to say about the visit details of the user like where they should go, where is the next visits, how many visits are there, etc. Whenever the question is related to what is my next visit, where should I go next, How many visits I have, How many times I need to visit this shop always call this tool"""
        try:
            user_input = self.chat_ctx.to_dict()
            items = user_input['items']
            if not items:
                return {"visit_details": "No user input found"}
            
            input_message = items[-1]
            print("User Input:\n", input_message["content"])
            response_state = visit_details(self.state, input_message["content"])
            # await self.session.say(response_state.response)
            return {"visit_details": response_state.response}
        except Exception as e:
            print(f"Error in return_state_response: {e}")
            return {"visit_details": "Sorry, an error occured"}

async def entrypoint(ctx: agents.JobContext):


    try:
        state = State()
        state.user_id = "005fK000001oNIbQAM"
        try:
            session = AgentSession(
            llm=openai.realtime.RealtimeModel(
                voice="coral",
            )
        )   
            session.generate_reply(instructions="Greet the user and offer your assistance.")
            print("Using OpenAI")
        except Exception as e:
            print("Using Google")
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
            ),
        )

        await ctx.connect()

        await session.generate_reply(
            instructions="Greet the user and offer your assistance.",
            allow_interruptions=False, 
        )

        
        
    except Exception as e:
        print(f"Error in entrypoint: {e}")
        raise

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))
    
