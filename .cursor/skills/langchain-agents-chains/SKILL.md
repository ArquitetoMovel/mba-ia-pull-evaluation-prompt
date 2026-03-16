---
name: langchain-agents-chains
description: Teaches how to build custom agents and chains with LangChain using LCEL (LangChain Expression Language). Use when creating LLM pipelines, chaining prompts with models, adding tools to agents, or when the user asks about LangChain agents, chains, runnables, or LCEL.
---

# LangChain Custom Agents and Chains

## LCEL: Building Chains with the Pipe Operator

In LangChain, a **chain** is a runnable built by composing other runnables. Use the pipe operator `|` to connect them; output of one becomes input of the next.

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Simple chain: prompt -> LLM -> string
chain = prompt_template | llm | StrOutputParser()
result = chain.invoke({"topic": "Python"})
```

**Common pattern in this project:** `prompt_template | llm` (LLM returns a message object; use `.content` or add `StrOutputParser()` for a string).

### Chaining Multiple Steps

Add as many runnables as needed. Each step receives the previous step's output.

```python
from langchain_core.runnables import RunnablePassthrough

# prompt -> llm -> parser -> next_prompt -> llm
chain = (
    prompt_1
    | llm
    | StrOutputParser()
    | (lambda x: {"refined": x})
    | prompt_2
    | llm
    | StrOutputParser()
)
```

Use `RunnablePassthrough` when you need to pass through original inputs alongside a new value:

```python
from langchain_core.runnables import RunnablePassthrough, RunnableParallel

chain = RunnableParallel(
    original=RunnablePassthrough(),
    summary=prompt | llm | StrOutputParser(),
)
# Invoke with one input; get {"original": input, "summary": "..."}
```

### Invocation and Streaming

- `chain.invoke(input)` — single sync call
- `chain.ainvoke(input)` — single async call
- `chain.stream(input)` — stream chunks
- `chain.batch([input1, input2])` — batch (efficient for I/O-bound steps)

---

## Custom Tools for Agents

Tools are callables the agent can use. Define them with the `@tool` decorator or by subclassing `BaseTool`.

```python
from langchain_core.tools import tool

@tool
def search(query: str) -> str:
    """Search the knowledge base. Use when the user asks about documentation or facts."""
    # Implement search; return string.
    return f"Results for: {query}"

@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression. Input should be a single expression, e.g. 2+3."""
    return str(eval(expression))
```

Tools need a **description** (in docstring or `description=`); the LLM uses it to choose when to call the tool. Keep descriptions short and action-oriented.

---

## Building an Agent Chain

Two common patterns:

### 1. Tool-calling agent (recommended for chat models that support tool calls)

Bind tools to the LLM and run a loop: call LLM → if tool_calls, run tools and append results → repeat until the model returns a final message. See [reference.md](reference.md) for a complete tool-calling loop.

```python
from langchain_core.messages import HumanMessage, ToolMessage

llm_with_tools = llm.bind_tools([search, calculator])
messages = [HumanMessage(content="What is 3*4?")]

response = llm_with_tools.invoke(messages)
# If response.tool_calls: run each tool, append ToolMessage, invoke again; repeat until no tool_calls.
# Final answer is in response.content
```

### 2. ReAct-style agent (prompt-based)

Use when you need a ReAct (reasoning + acting) flow with a single prompt and a list of tools:

```python
from langchain import hub
from langchain.agents import create_react_agent, AgentExecutor

prompt = hub.pull("hwchase17/react")
agent = create_react_agent(llm, [search, calculator], prompt)
agent_executor = AgentExecutor(agent=agent, tools=[search, calculator], verbose=True)
result = agent_executor.invoke({"input": "What is 2+2?"})
```

The agent returns a dict with an `"output"` key containing the final answer.

---

## Checklist for Custom Chains

- Use **LCEL** (`|`) for linear pipelines; prefer `invoke`/`batch`/`stream` on the composed runnable.
- For **multi-step** flows that need state or branching, consider **LangGraph** (see [reference.md](reference.md)).
- **Tools**: clear docstrings/descriptions; use `@tool` or `BaseTool`; bind to LLM with `llm.bind_tools(tools)` for tool-calling agents.
- **Prompts**: use `ChatPromptTemplate` and variable names that match the dict you pass to `invoke`.
- **Parsing**: add `StrOutputParser()` or `JsonOutputParser()` at the end when you need a plain string or dict instead of an AIMessage.

---

## Additional Resources

- For LangGraph, multi-step agents, and advanced patterns, see [reference.md](reference.md).
