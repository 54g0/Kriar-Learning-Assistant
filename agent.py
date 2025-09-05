from model import Model
from context_extractor import ContextExtractor
from tools import tools
from langchain.schema import HumanMessage, AIMessage, BaseMessage
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from typing import List, Dict, Any, TypedDict, Annotated
from langgraph.graph.message import add_messages

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    context: str
    metadata: Dict[str, Any]
    timestamp: float
    video_url: str
    final_result: str

class KriarLearningAgent:
    def __init__(self, model_provider, model_name,api_key):
        self.api_key = api_key
        self.model = Model(model_provider, model_name,api_key)
        self.tools = tools
        self.context_extractor = None

    def set_video_context(self, video_url: str, timestamp: float = 0):
        """Set the video context for the agent"""
        try:
            self.context_extractor = ContextExtractor(video_url, timestamp)
            return True
        except Exception as e:
            return False

    def create_graph(self):
        """Create the LangGraph workflow"""
        graph = StateGraph(AgentState)
        graph.add_node("context_node", self.context_node)
        graph.add_node("prompt_optimizer_node", self.prompt_optimizer_node)
        graph.add_node("executor_node", self.executor_node)

        # Add tool node
        tool_node = ToolNode(self.tools)
        graph.add_node("tool_caller_node", tool_node)

        # Set entry point
        graph.set_entry_point("context_node")

        # Add edges
        graph.add_edge("context_node", "prompt_optimizer_node")
        graph.add_edge("prompt_optimizer_node", "executor_node")

        # Add conditional edges
        graph.add_conditional_edges(
            "executor_node",
            self.should_use_tool,
            {
                "use_tool": "tool_caller_node",
                "finish": END
            }
        )
        graph.add_edge("tool_caller_node", "executor_node")

        return graph.compile()

    def context_node(self, state: AgentState) -> AgentState:
        """Extract relevant context from video at timestamp"""
        try:
            if self.context_extractor and state.get("timestamp") is not None:
                print(f"Extracting context at timestamp: {state['timestamp']}")
                context_text = self.context_extractor.get_context_at_timestamp(state["timestamp"])
                state["context"] = context_text
                state["metadata"] = self.context_extractor.metadata
                print(f"Extracted context length: {len(context_text)} characters")
            else:
                state["context"] = ""
                print("No context extractor or timestamp available")
            return state
        except Exception as e:
            print(f"Context extraction error: {e}")
            state["context"] = ""
            return state

    def prompt_optimizer_node(self, state: AgentState) -> AgentState:
        """Optimize the query into best prompt for results"""
        try:
            query = state.get("query", "")
            context = state.get("context", "")

            optimization_prompt = f"""
            Optimize this user query for better LLM understanding: "{query}"

            Available context from video transcript: {context} and this is the meta data of the video {state.get('metadata', {})}

            Create a clear, specific prompt that will help answer the user's question using the video context if 
            video context is not given then answer the question and say no context available but here is the answer.
            this prompt also has previous messages you can use them if you want to.
            """
            messages = state.get("messages", [])
            messages.append[HumanMessage(content=optimization_prompt)]
            model = self.model.create_model()
            optimized_response = model.invoke(messages[-5:])

            state["query"] = optimized_response.content
            state["messages"] = [HumanMessage(content=optimization_prompt), AIMessage(content=optimized_response.content)]
            return state
        except Exception as e:
            return state

    def executor_node(self, state: AgentState) -> AgentState:
        """Execute the main task with context awareness"""
        try:
            query = state.get("query", "")
            context = state.get("context", "")

            executor_prompt = f"""
            You are a YouTube Learning Assistant. Answer the user's question using the provided video context.

            User Question: {query}

            Video Context: {context}

            Provide a helpful, accurate answer based on the video content. If you need additional information, 
            you can use the available tools (wikipedia_query, context_search, timestamp_analyzer).
            """

            messages = state.get("messages", [])
            messages.append(HumanMessage(content=executor_prompt))

            model_with_tools = self.model.bind_tools(self.tools)
            result = model_with_tools.invoke(messages[-5:])

            messages.append(result)
            state["messages"] = messages
            state["final_result"] = result.content

            return state
        except Exception as e:
            state["final_result"] = f"Error processing query: {str(e)}"
            return state

    def should_use_tool(self, state: AgentState) -> str:
        """Determine if tools should be used"""
        try:
            messages = state.get("messages", [])
            if not messages:
                return "finish"

            last_message = messages[-1]

            if hasattr(last_message, 'tool_calls') and last_message.tool_calls:
                return "use_tool"

            return "finish"
        except Exception as e:
            return "finish"

    def execute_task(self, query: str, video_url: str = None, timestamp: float = 0) -> str:
        """Execute the main learning task"""
        try:

            if video_url:
                success = self.set_video_context(video_url, timestamp)
                if not success:
                    return "Error: Could not load video context"


            initial_state = AgentState(
                messages=[],
                query=query,
                metadata={},
                context="",
                timestamp=timestamp,
                video_url=video_url or "",
                final_result=""
            )

            # Create and run graph
            graph = self.create_graph()
            final_state = graph.invoke(initial_state)

            return final_state.get("final_result", "No result generated")

        except Exception as e:
            return f"Error: {str(e)}"

    def get_context_at_timestamp(self, timestamp: float) -> Dict[str, Any]:
        """Get video context at specific timestamp"""
        if self.context_extractor:
            return self.context_extractor.get_context_at_timestamp(timestamp)
        return {"error": "No video context available"}


