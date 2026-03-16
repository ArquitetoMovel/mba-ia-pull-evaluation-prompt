# LangChain Agents & Chains — Reference

## LangGraph for Production Agents

For agents that need cycles, state, or human-in-the-loop, use **LangGraph** instead of the legacy `AgentExecutor`:

- Install: `langgraph`
- Build a graph with nodes (LLM, tools, conditional edges) and compile to a runnable.
- Supports cycles (agent → tools → agent), stateful messages, and streaming.

See [LangGraph docs](https://langchain-ai.github.io/langgraph/) for the current API.

## Tool-calling loop (full example)

Minimal loop to run a tool-calling agent without LangGraph:

```python
from langchain_core.messages import AIMessage, ToolMessage

def run_tool(name: str, args: dict, tools: list) -> str:
    for t in tools:
        if t.name == name:
            return str(t.invoke(args))
    return f"Unknown tool: {name}"

messages = [HumanMessage(content=user_input)]
while True:
    response = llm_with_tools.invoke(messages)
    messages.append(response)
    if not getattr(response, "tool_calls", None):
        break
    for tc in response.tool_calls:
        result = run_tool(tc["name"], tc["args"], tools)
        messages.append(ToolMessage(content=result, tool_call_id=tc["id"]))
# Final text: messages[-1].content
```

## Runnable types

| Type | Use case |
|------|----------|
| `ChatPromptTemplate` | Prompt with variables → messages |
| `BaseChatModel` | Messages in → AIMessage out |
| `StrOutputParser()` | AIMessage → str |
| `JsonOutputParser()` | AIMessage → dict (parse JSON from content) |
| `RunnablePassthrough()` | Pass input through unchanged |
| `RunnableLambda(fn)` | Custom sync function |
| `RunnableParallel({...})` | Fan-out; run multiple runnables on same input |

## Prompts from LangSmith Hub

```python
from langchain import hub
prompt = hub.pull("owner/prompt-name")
# Use in chain: prompt | llm | ...
```

Requires `LANGCHAIN_API_KEY` or `LANGCHAIN_HUB_API_KEY` in the environment.
