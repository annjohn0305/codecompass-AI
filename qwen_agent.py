from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="qwen2.5:1.5b"
)

def analyze_project(prompt):

    print("================================")
    print("QWEN STARTED")
    print("================================")

    response = llm.invoke(prompt)

    print("================================")
    print("QWEN FINISHED")
    print("================================")

    return response.content