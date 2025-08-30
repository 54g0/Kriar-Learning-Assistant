from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
import os
from langchain_google_genai import ChatGoogleGenerativeAI
class Model:
    def __init__(self, model_provider, model_name, api_key, temperature=0.7, max_tokens=2000, verbose=True):
        self.model_provider = model_provider
        self.model_name = model_name
        self.api_key = api_key
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.verbose = verbose

    def create_model(self):
        if self.model_provider == "openai":
            os.environ["OPENAI_API_KEY"] = self.api_key
            return ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                verbose=self.verbose
            )
        elif self.model_provider == "groq":
            os.environ["GROQ_API_KEY"] = self.api_key
            return ChatGroq(
                
                model=self.model_name,
                temperature=self.temperature, 
                verbose=self.verbose
            )
        elif self.model_provider == "google":
            os.environ["GOOGLE_API_KEY"] = self.api_key
            return ChatGoogleGenerativeAI(
                model=self.model_name,
                temperature=self.temperature,
                verbose=self.verbose
            )
        else:
            raise ValueError(f"Invalid model provider: {self.model_provider}")

    def bind_tools(self, tools):
        """Bind tools to the model"""
        model = self.create_model()
        return model.bind_tools(tools)

    def invoke(self, messages):
        """Invoke the model with messages"""
        model = self.create_model()
        return model.invoke(messages)
