import warnings
warnings.filterwarnings("ignore", category=UserWarning)

import logging, sys, io
from contextlib import redirect_stdout
import builtins

# Suppress all logging output
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger("litellm").setLevel(logging.CRITICAL)
logging.getLogger("uvicorn").setLevel(logging.CRITICAL)

# Patch print to suppress unwanted messages from litellm
original_print = builtins.print
def silent_print(*args, **kwargs):
    if "Provider List" in str(args[0]):
        return
    original_print(*args, **kwargs)
builtins.print = silent_print

# Import after suppressing noise
import litellm
litellm.get_supported_params = lambda *args, **kwargs: {}

from crewai import Agent, Task, Crew, LLM

# Restore print
builtins.print = original_print

# Define your LLM
llm = LLM(
    model="llama3",
    base_url="http://localhost:11434",
    api_key="ollama",
    temperature=0.7,
    max_tokens=512,
    custom_llm_provider="ollama"
)
f = io.StringIO()
with redirect_stdout(f):
    # Define the agent
    math_professor = Agent(
        role="Math Professor",
        goal="Solve simple math problems",
        backstory="A professor with a knack for numbers.",
        verbose=False,
        llm=llm
    )

# Input loop until Ctrl+C
try:
    while True:
        user_input = input("\n🧮 Ask your math question (or press Ctrl+C to quit): ")
        if not user_input.strip():
            continue
        f = io.StringIO()
        with redirect_stdout(f):
            task = Task(
                description=user_input,
                expected_output="A clear answer to the math question.",
                agent=math_professor
            )

            crew = Crew(
                agents=[math_professor],
                tasks=[task],
                verbose=False
            )

            result = crew.kickoff()
        print("\n✅ Result:", result)

except KeyboardInterrupt:
    print("\n👋 Exiting... Have a great day!")

