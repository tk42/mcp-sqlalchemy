import streamlit as st
import os
from dotenv import load_dotenv
from mcp import StdioServerParameters
from utils.openai_agent import OpenAIAgent
from utils.openai_tools import OpenAIToolManager
from utils.mcp_client import MCPClient
import asyncio

# Load environment variables
load_dotenv()

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []


async def process_message(user_input: str, agent: OpenAIAgent, mcp_client: MCPClient):
    """Process user message and get response from Llamacpp with MCP tools"""
    response = await agent.invoke_with_prompt(user_input)
    return response


async def main():
    st.title("Llamacpp MCP Chat")
    
    # Initialize Llamacpp agent and MCP client
    agent = OpenAIAgent(
        llamacpp_url=os.getenv("LLAMACPP_URL"),
    )
    agent.tools = OpenAIToolManager()

    # Configure MCP client with mcp-alchemy
    server_params = StdioServerParameters(
        command="/app/.venv/bin/python",
        args=["/app/mcp-alchemy/server.py"],
        env={"DB_URL": os.getenv("DB_URL")}
    )

    async with MCPClient(server_params) as mcp_client:
        tools = await mcp_client.get_available_tools()
        for tool in tools:
            agent.tools.register_tool(
                name=tool.name,
                func=mcp_client.call_tool,
                description=tool.description,
                input_schema=tool.inputSchema
            )

        # Display chat messages
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("What would you like to know?"):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Get response
            with st.chat_message("assistant"):
                # async def get_response():
                #     async with MCPClient(server_params) as mcp_client:
                #         # Register MCP tools with the agent
                #         tools = await mcp_client.get_available_tools()
                #         # st.info(tools)
                #         for tool in tools:
                #             agent.tools.register_tool(
                #                 name=tool.name,
                #                 func=mcp_client.call_tool,
                #                 description=tool.description,
                #                 input_schema=tool.inputSchema
                #             )
                        
                #         response = await process_message(prompt, agent, mcp_client)
                #         return response

                with st.spinner("Thinking..."):
                    # response = get_response()
                    response = await process_message(prompt, agent, mcp_client)
                    st.markdown(response)
                    st.session_state.messages.append({"role": "assistant", "content": response})


if __name__ == "__main__":
    asyncio.run(main())
