from dotenv import load_dotenv
from livekit import agents
from livekit.agents import (
    AgentSession,
    Agent,
    RoomInputOptions,
    function_tool,
    RunContext,
)
from livekit.agents.llm import LLM
from livekit.plugins import google, noise_cancellation
import json
import sys
import os
import logging
from error_handler import ErrorHandler
from typing import List
import asyncio
import aiohttp
 
from salesforce_api import fetch_orders_by_account_id, fetch_customer_details_by_account_id, place_order_api
import pickle
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import re
from functools import lru_cache
import httpx
from datetime import datetime
 
# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("agent.log")
    ]
)
logger = logging.getLogger(__name__)
 
 
# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
 
from livekit.plugins.turn_detector.multilingual import MultilingualModel
from state import State
from salesforce_api import visit_details_list, fetch_orders_by_account_id, fetch_customer_details_by_account_id
 
 
load_dotenv(r"C:\Users\LENOVO\Order Voice Agent\.env")
 
_http_session = None
 
class Assistant(Agent):
    def __init__(self, state: State, embedding_file = "customer_embeddings.pkl", product_embedding="carysil_product_embeddings.pkl", conf=0.5) -> None:
        super().__init__(
            instructions="""
        Mandatory Conversation Opening line:
        “Hi Purveesha How are u doing, I’m here to help you with placing orders,assisting order details, checking visits planned for today, or answering any customer-related enquiries.How can I assist you today”
       
        You must introduce yourself to the user whenever conversation starts by using the above opening line.
        You must reply as if you are speaking on a phone call, like a real human agent.
 
        You have access to:
        - place orders for customers
        - Customer details
        - Previous order history of customers
        - Visits planned for today
 
        Based on the user's question, you must respond using only the available customer details, order history, or visit information.
 
 
        When a customer indicates they want to place an order:
            - If the customer has mentioned "Place order to Sri Balaji traders" in this way then we should consider Balaji Traders as 'customer_name', If the name is missing, ask a follow-up question like please mention the name of the shop to whom we have to place.After the customer name is available, prompt the customer to share the order details.
            - Once the customer provides the order items and quantities,call the tool 'get_order_info' to process and validate the order.
            - After confirming that all items and quantities are correct,ask the customer for final confirmation of the order.
            - When the customer confirms the order by mentioning "proceed the order" or "to confirm the order" or some other sort of confirmation,call the tool 'place_order_tool' to complete the order.
 
        INSTRUCTIONS:
        - You are strictly allowed to reply in the langugage in which the user has asked the question.
        - You are not capable of answering questions outside customer details, order history, or visit information.
        - Strictly for every order related query is asked strictly call the correct tool `get_order_details` to response.This is mandatory.
        - Strictly for every customer details related query is asked strictly call the correct tool `get_customer_details` to response.This is mandatory.
        - Strictly for every visit related query is asked strictly call the correct tool `get_visits` to response.This is mandatory.
        -If anything related to amount please strictly use ' rupess' instead of  'dollars' or 'USD'.(this is mandatory to be followed for 'get_order_details' tool)
        -If any date has to be mentioned in the reply,elaborately mention.For example id date is 26-08-2026 mention it as 26th August .If the date is from previous year only at that time mention the year in the reply.(this is mandatory to be followed for 'get_order_details' tool)
        """
        )
        self.state = state
        self.embedding_file = embedding_file
        self.product_embedding = product_embedding
        with open(self.embedding_file, 'rb') as f:
            data = pickle.load(f)
        with open(self.product_embedding, "rb") as f:
            product_data = pickle.load(f)
 
        self.products = product_data["products"]
        self.product_embeddings = product_data["embeddings"]
        self.accounts = data["accounts"]
        self.embeddings = np.array(data["embeddings"])
        self.threshold = conf
        self.embedding_model = SentenceTransformer("all-MiniLM-L6-v2", local_files_only=True)
        self.customer_name= None
 
    async def get_http_session(self):
        global _http_session
        if _http_session is None or _http_session.closed:
            _http_session = aiohttp.ClientSession()
        return _http_session  
   
    @function_tool
    async def get_order_details(self, ctx: RunContext,shop_name:str):
        """You are an tool to reply for all order related queries.
 
        You have access to the complete order history of the customer.
        You must answer only order-related questions.
       
        Understand the user's question, analyze the order history,
        and respond with exactly what the user asked for—nothing more.
       
        Rules:
        - Reply only using the available order history data.
        - Do not add extra explanations or unrelated details.
        - If asked about orders on a specific date, return only those orders.
        - If asked whether an order was placed today, check today’s date and reply Yes or No.
        - If no matching order exists, clearly say so.
        - If the question is outside order history, say you can help only with order-related queries.
        """
        logger.info("get_order_details tool called")
        try:
 
            if not self.state.user_id or not self.state.access_token:
                logger.error("Missing user_id or access_token in state")
                return "I'm sorry, but I don't have your authentication details. Please log in again."
            query_embedding = self.embedding_model.encode([shop_name])[0]
            norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
            similarities = np.dot(self.embeddings, query_embedding) / norms
   
            best_idx = int(np.argmax(similarities))
   
            if similarities[best_idx] < self.threshold:
                return json.dumps({
                    "success": False,
                    "message": "Shop not found"
                })
   
            account = self.accounts[best_idx]
            orders = await fetch_orders_by_account_id(self.state, account)
           
            return f"Order Details {orders}"
       
        except Exception as e:
            logger.error(f"Error in get_order_details: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            return "I'm sorry, but I couldn't retrieve your order details at this time. Please try again later."
   
    @function_tool
    async def get_customer_details(self, ctx: RunContext,cust_name:str):
        """You are a tool to reply for all customer details related queries.
        Understand the user's question, analyze the customer details and respond with exactly what the user asked for—nothing more.
        Only Respond if anything asked abt the customer specific information,if anything about order related dont reply
        If anything summary asked abt customer details provide a brief summary of the customer details.very crisp and short only include important details.
        Note: Dont mention any ID fields in the reply.
        """
        try:
            logger.info("get_customer_details tool called")
            query_embedding = self.embedding_model.encode([cust_name])[0]
   
            # Vectorized cosine similarity
            norms = np.linalg.norm(self.embeddings, axis=1) * np.linalg.norm(query_embedding)
            similarities = np.dot(self.embeddings, query_embedding) / norms
   
            best_idx = int(np.argmax(similarities))
   
            if similarities[best_idx] < self.threshold:
                return json.dumps({
                    "success": False,
                    "message": "Shop not found"
                })
   
            account = self.accounts[best_idx]
            customer_details = await fetch_customer_details_by_account_id(self.state, account["Id"])
            return f"Customer Details {customer_details}"
        except Exception as e:
            logger.error(f"Error in get_customer_details: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            return "I'm sorry, but I couldn't retrieve your customer details at this time. Please try again later."
   
    @function_tool
    async def get_visits(self, ctx: RunContext):
        """You are a tool helps to return the visit details of the user.
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
        - If user asks "Give me my next visit based on pending orders"
           - Always reply "Your next visit is: [third visit]"
        - If user asks "Where do I have to go visit next based on my order history?"
           - Always reply "You have to go to [second visit], as your purchase was low last month"
        - If user asks "Can you help me to know the priority visit based on pending payment collection?"
           - Always reply "Sure, Your priority visit based on pending payment is [first visit] for ₹185000"
         - If user asks "Can you give me todays visit plan according to highest order value"
            - Always reply "Here is your visit plan for today, sorted by highest order value.
                    First, visit [third visit].
                    Next, [second visit].
                    Finally, [first visit].
                    That's your prioritized visit plan for today."
        - If user asks "Can you help me to know todays visit plan based on low sales"
            - Always reply "Sure, Your priority visits based on low sales visibility are [third visit] and [second visit]"
       
       
        """
        try:
            # Validate state before proceeding
            if not self.state.user_id or not self.state.access_token:
                logger.error("Missing user_id or access_token in state")
                return "I'm sorry, but I don't have your authentication details. Please log in again."
 
            logger.info("Fetching visit details")
            v = await visit_details_list(self.state)
            logger.info(f"Retrieved visit details: {v}")
           
            # Check if we got an error message back
            if len(v) == 1 and any(error_text in v[0].lower() for error_text in ["error", "unable", "no visit"]):
                logger.warning(f"Visit details error: {v[0]}")
                return f"I'm sorry, but {v[0].lower()}. Please try again later or contact support."
           
            # Check if the list is empty
            if not v:
                return "Your visit list is currently empty."
               
            return f"Visit Details {v}"
           
        except Exception as e:
            logger.error(f"Error in get_visits: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            return "I'm sorry, but I couldn't retrieve your visit details at this time. Please try again later."
 
    @function_tool
    async def get_order_info(self, ctx: RunContext,customer_name: str, items: List[str], quantity: List[int]):
        """You are a tool helps to create a order list from the user provided items and quantity."""
        self.customer_name = customer_name
        order_details = dict(zip(items, quantity))
 
        logger.info(f"Placing order for items: {order_details}")
        product_dict = order_details  # Ensure product_dict remains a dictionary
        logger.info(f"Order summary: {product_dict}")
        logger.info("Getting the product embeddings and matching...")
        product_names = list(product_dict.keys())
        quantities = list(product_dict.values())
       
        embeddings = self.embedding_model.encode(product_names)
        cart = []
        not_found = []
       
        for i, product_name in enumerate(product_names):
            # Calculate similarity with all products
            sims = cosine_similarity([embeddings[i]], self.product_embeddings)[0]
            idx = np.argmax(sims)
           
            if sims[idx] >= self.threshold:
                cart.append({
                    'product_id': self.products[idx]['Id'],
                    'product_name': self.products[idx]['Name'],
                    'qty': int(quantities[i]),
                    'score': float(sims[idx])
                })
            else:
                not_found.append(product_name)
        self.cart = cart
        print("FINAL CART:", self.cart)
        if not cart:
                logger.info({
                    "success": False,
                    "message": f"Products not found: {', '.join(not_found)}",
                    "cart": []
                })
                return {
                    "success": False,
                    "message": f"Products not found: {', '.join(not_found)}",
                    "cart": []
                }
        elif not_found:
            logger.info({
                "success": False,
                "message": f"Some products not found: {', '.join(not_found)}",
                "cart": cart
            })
            return {
                "success": False,
                "message": f"Some products not found: {', '.join(not_found)}",
                "cart": cart
            }
        else:
           
            logger.info({
                "success": True,
                "message": f"Confirm this products to place the order: {cart}",
                "cart": cart
            })
            return {
                "success": True,
                "message": f"Confirm this products to place the order: {cart}",
                "cart": cart
            }
 
    async def place_order(self, payload):
        logger.info("Placing order api is called from agent")
        session = await self.get_http_session()
        asyncio.create_task(
            place_order_api(
                session=session,
                state=self.state,
                payload=payload,
            )
        )
       
           
    @function_tool
    async def place_order_tool(self, ctx: RunContext):
        """You are a tool helps to place the order when user says to place order by confirming, use the cart created from get_order_details tool."""
        logger.info("Placing order")
        try:
            cart = self.cart
            payload = {
            "account_id": "123",
            "cart": cart,
            "customer_name": self.customer_name
        }
            await self.place_order(payload)
            # asyncio.create_task(self._delayed_disconnect(10))
            return f"Order placed successfully for items: {cart}"
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            return "Error placing order"
 
async def entrypoint(ctx: agents.JobContext):
    try:
        logger.info("Agent starting up")
        await ctx.connect()
        logger.info("Connected to LiveKit room")
       
        participant = await ctx.wait_for_participant()  # Wait for a client to join
        logger.info(f"Participant joined: {participant.identity}")
       
        # Parse metadata with error handling
        try:
            pm = participant.metadata
            pm = json.loads(pm) if pm else {}
            logger.info(f"Participant metadata type: {type(pm)}")
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse participant metadata: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            pm = {}
       
        # Initialize state with safe defaults
        state = State()
        state.user_id = pm.get("user_id", "")
        state.access_token = pm.get("access_token", "")
       
       
        if not state.user_id or not state.access_token:
            logger.warning("Missing user_id or access_token in metadata")
       
        logger.info(f"Initializing assistant for user: {state.user_id}")
        assistant = Assistant(state=state)
       
        # Initialize session with error handling
        try:
            session = AgentSession(
                llm=google.beta.realtime.RealtimeModel(
                    voice="Aoede",
                    # language="en-IN",
                ),
            )
           
            await session.start(
                room=ctx.room,
                agent=assistant,
                room_input_options=RoomInputOptions(
                    noise_cancellation=noise_cancellation.BVC(),
                ),
            )
   
           
            logger.info("Agent session started successfully")
            await session.generate_reply(instructions="Who are you?", allow_interruptions=False)
           
        except Exception as e:
            logger.error(f"Failed to start agent session: {str(e)}")
            logger.error(ErrorHandler.format_exception())
            raise
           
    except Exception as e:
        logger.error(f"Unhandled exception in entrypoint: {str(e)}")
        logger.error(ErrorHandler.format_exception())
        # Attempt to notify the room if possible
        try:
            if 'session' in locals() and session:
                await session.generate_reply(
                    instructions="I'm experiencing technical difficulties. Please try again later.",
                    allow_interruptions=False
                )
        except Exception as notify_error:
            logger.error(f"Failed to notify room about error: {str(notify_error)}")
        raise  # Re-raise the exception for proper handling
 
 
 
if __name__ == "__main__":
    agents.cli.run_app(
        agents.WorkerOptions(
            entrypoint_fnc=entrypoint)
    )
 
 