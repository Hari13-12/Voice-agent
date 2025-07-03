from langchain_google_genai import ChatGoogleGenerativeAI


class LLMManger:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="models/gemini-1.5-flash",
           
            temperature=1,
           
            api_key="AIzaSyDsrbg02ek4Jbh1p2F3EDOoBsQDS9M1qZg"
        )
 
    def get_llm(self):
        return self.llm

    def invoke(self,message):
        return self.llm.invoke(message)