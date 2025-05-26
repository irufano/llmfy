import asyncio
import pprint
import random
import time

from llmfy import (
    END,
    START,
    LLMfyPipe,
    MemoryManager,
    Message,
    Role,
    WorkflowState,
)

# Initialize memory manager
memory_manager = MemoryManager(extend_list=True)

# Create workflow with memory manager
state = {
    "messages": [],
    "skill": {"programming": []},
    "auth": {
        "name": "irufano",
        "company": "gokil",
    },
}
workflow = LLMfyPipe(state, memory=memory_manager)


async def main(state: WorkflowState) -> dict:
    messages = state.get("messages", [])
    responses = [
        "Hello",
        "Wowww",
        "Amazing",
        "Gokil",
        "Good game well played",
        "Selamat pagi",
        "Maaf aku tidak tahu",
    ]
    random_answer = random.choice(responses)
    ai_message = Message(role=Role.ASSISTANT, content=random_answer)
    messages.append(ai_message)
    return {"messages": messages}


# Add nodes
workflow.add_node("main", main)
workflow.add_edge(START, "main")
workflow.add_edge("main", END)


async def call_workflow(
    question: str,
    thread_id: str,
    name: str,
    company: str,
    coding: str,
):
    try:
        message = Message(role=Role.USER, content=question)
        messages = [message]
        auth = {"name": name, "company": company}
        programming = {"programming": [{"name": coding}]}
        res = await workflow.execute(
            {"messages": messages, "auth": auth, "skill": programming}, thread_id
        )

        return res
    except Exception as e:
        raise e


async def chat_terminal():
    print("Welcome to the Chat Terminal! Type 'exit' to quit.")
    print(
        "Use one digit number on thread id for simplicity testing, i.e: thread_id: 1\n"
    )

    while True:
        thread_id = input("thread_id: ")
        name = input("name: ")
        company = input("company: ")
        coding = input("coding: ")
        user_input = input("You: ")

        if user_input.lower() == "exit":
            print("Chatbot: Goodbye!")
            break

        response = await call_workflow(
            user_input.lower(), thread_id, name, company, coding
        )
        time.sleep(0.5)  # Simulate a small delay for realism
        print(f"\nChatbot: {response['messages'][-1].content}\n")
        pprint.pp(response)
        # print("History: ")
        # for msg in history:
        #     print(f"\t{msg}")


if __name__ == "__main__":
    asyncio.run(chat_terminal())
