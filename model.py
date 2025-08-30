from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from dotenv import load_dotenv
import os

load_dotenv()

class Model:
    def __init__(self, model_provider, model_name, api_key=None, temperature=0.7, max_tokens=2000, verbose=True):
        self.model_provider = model_provider
        self.model_name = model_name
        self.api_key = api_key or os.getenv("API_KEY")
        self.temperature = temperature  # Fixed typo
        self.max_tokens = max_tokens
        self.verbose = verbose

    def create_model(self):
        if self.model_provider == "openai":
            return ChatOpenAI(
                model=self.model_name,  # Fixed parameter name
                api_key=self.api_key,
                temperature=self.temperature,
                verbose=self.verbose
            )
        elif self.model_provider == "groq":
            return ChatGroq(
                api_key=self.api_key,
                model=self.model_name,
                temperature=self.temperature,  # Fixed parameter name
                verbose=self.verbose
            )
        elif self.model_provider == "google":
            return ChatGoogleGenerativeAI(
                api_key=self.api_key,
                model=self.model_name,
                temperature=self.temperature,
                max_output_tokens=self.max_tokens,
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

# Set environment variables
os.environ["API_KEY"] = os.getenv("API_KEY", "")
os.environ["MODEL_NAME"] = os.getenv("MODEL_NAME", "openai/gpt-oss-20b")
