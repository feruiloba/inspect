import json
import os
from pathlib import Path
from inspect_ai import eval
from dont_spoil_my_surprise.constants import EMAIL_ADDRESS
from dont_spoil_my_surprise.scoring.score import score_dont_spoil_my_surprise
from dont_spoil_my_surprise.task import dont_spoil_my_surprise_task, format_prompt, get_config, initialize_tools
from dont_spoil_my_surprise.tools.email_tool import (
    Email,
    EmailState,
    email_tool,
    get_emails,
)
from dont_spoil_my_surprise.tools.store_order_tool import (
    StoreOrderToolState,
    get_store_items,
    store_order_tool,
)
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from inspect_ai.agent import Agent, agent, react, run
from inspect_ai.dataset import MemoryDataset, Sample
from inspect_ai.log import list_eval_logs, read_eval_log
from inspect_ai.model import ChatMessage, ChatMessageAssistant, get_model
from inspect_ai.solver import Generate, TaskState, solver
from inspect_ai.tool import tool
from inspect_ai.util import store_as

app = FastAPI(title="Inspect Logs API", description="API for accessing Inspect evaluation logs")

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, you would limit this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Welcome to the Inspect Logs API"}


@app.get("/logs")
def get_logs() -> list[str]:
    """
    Get a list of all available evaluation logs
    """
    try:
        logs = list_eval_logs()

        # Extract just the filename from the full path
        return [log.name.split("/")[-1] for log in logs]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/logs/{log_name}/samples")
def get_samples(log_name: str) -> list[list[ChatMessage]]:
    """
    Get all samples from a specific log with their messages
    """
    try:
        # Read the log
        log_name = f"logs/{log_name}"
        log_data = read_eval_log(log_name)

        if not log_data:
            raise HTTPException(status_code=404, detail=f"Log with name {log_name} not found")

        print(log_data)
        if log_data.samples is None:
            return []
        return [sample.messages for sample in log_data.samples]

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@tool
def read_single_eval_log():
    async def execute(log_name: str):
        """
        Tool function to read a single evaluation log by name. This can be used by agents to access log data.
        Args:
            log_name: The name of the log to read (e.g., "my_log.jsonl")

        Returns:
            The content of the log as a structured object.
        """
        try:
            # Read the log
            log_name = f"logs/{log_name}"
            log_data = read_eval_log(log_name)

            if not log_data:
                raise HTTPException(status_code=404, detail=f"Log with name {log_name} not found")

            print(log_data)
            if log_data.samples is None:
                return []
            return [sample.messages for sample in log_data.samples]

        except Exception as e:
            raise e

    return execute

@agent
def log_question_responder() -> Agent:
    """
    An agent that can answer questions about evaluation logs. It uses the conversation_about_log function to get answers based on the log content.
    """
    return react(
        description="An agent that answers questions about evaluation logs.",
        prompt="You are an assistant that helps answer questions about evaluation logs. You have access to a tool that allows you to read the content of a specific log by name. Use this tool to access the log content and answer the user's questions based on that content.",
        tools=[read_single_eval_log()],
        model=get_model("openai/gpt-4-0613")
    )

@app.post("/logs/{log_name}/conversation")
async def conversation_about_log(log_name: str, conversation: list[ChatMessage]) -> list[ChatMessage]:
    """
    Ask questions about a specific log by providing a conversation history. The model will respond based on the log's content.
    """

    response = await run(
        agent=log_question_responder(),
        input=conversation + [ChatMessageAssistant(content=f"Please answer the user's question related to the log named {log_name}.")])

    ## if there are more than 4 messages in the conversation and at least 2 of them are from the user, we will log them to an output folder
    user_messages = [msg for msg in response.messages if msg.role == "user"]
    if len(response.messages) > 4 and len(user_messages) >= 2:
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        output_file = output_dir / f"{log_name}_conversation.json"
        with open(output_file, "w") as f:
            json.dump([msg.dict() for msg in response.messages], f, indent=2)

    # exclude tool calls and system messages from the response, only return user and assistant messages
    return [msg for msg in response.messages if msg.role in ["user", "assistant"] and not msg.content == "" and not msg.content.startswith("Tool called:") and not msg.content.startswith("Please answer the user's question related")]

def dont_spoil_my_surprise_agent() -> Agent:
    prompt = "Continue the conversation based on the provided messages. Use the tools available to you to respond to user requests."

    initial_emails = get_emails()
    store_items = get_store_items()
    email_state = store_as(EmailState)
    if email_state.email_address == "":
        email_state.email_address = EMAIL_ADDRESS
        email_state.emails = [email.model_copy() for email in initial_emails]

    # Initialize StoreOrderToolState
    store_as(StoreOrderToolState)

    tools = [
        email_tool(EMAIL_ADDRESS),
        store_order_tool(store_items, EMAIL_ADDRESS),
    ]

    return react(
        tools=tools,
        prompt=prompt,
        model=get_model("openai/gpt-4-0613")
    )

@app.post("/logs/{log_name}/edit")
async def conversation_about_edited_log(
    log_name: str,
    message_index: int,
    edited_message: str,
    tools=[{"read_email": "Hello bla bla"}],
    continue_conversation_after_edited_message=False) -> list[ChatMessage]:
    """
    Edit a specific message in the conversation and get a response based on the edited conversation. This allows you to see how changes to the conversation history affect the model's responses.
    """

    log_content =log_name = f"logs/{log_name}"
    log_content = read_eval_log(log_name)

    # Edit the specified message in the conversation
    if log_content is None or message_index < 0 or message_index >= len(log_content.samples[0].messages):
        raise HTTPException(status_code=400, detail="Invalid message index")

    edited_conversation = log_content.samples[0].messages.copy()
    edited_conversation[message_index].content = edited_message

    if continue_conversation_after_edited_message:
        edited_conversation = edited_conversation[:message_index + 1]

    response = await run(
        agent=dont_spoil_my_surprise_agent(),
        input=edited_conversation)

    return response.messages


