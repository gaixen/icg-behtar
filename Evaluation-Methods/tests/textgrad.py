import httpx
import textgrad as tg
from textgrad.engine_experimental.litellm import LiteLLMEngine

LiteLLMEngine("gpt-4o", cache=True).generate(
    content="hello, what's 3+4", system_prompt="you are an assistant"
)

image_url = "https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg"
image_data = httpx.get(image_url).content

LiteLLMEngine("gpt-4o", cache=True).generate(
    content=[image_data, "what is this my boy"], system_prompt="you are an assistant"
)


tg.set_backward_engine("gpt-4o", override=True)

model = tg.BlackboxLLM("gpt-4o")
question_string = (
    "If it takes 1 hour to dry 25 shirts under the sun, "
    "how long will it take to dry 30 shirts under the sun? "
    "Reason step by step"
)

question = tg.Variable(
    question_string, role_description="question to the LLM", requires_grad=False
)
answer = model(question)


answer.set_role_description("concise and accurate answer to the question")

optimizer = tg.TGD(parameters=[answer])
evaluation_instruction = (
    f"Here's a question: {question_string}. "
    "Evaluate any given answer to this question, "
    "be smart, logical, and very critical. "
    "Just provide concise feedback."
)

loss_fn = tg.TextLoss(evaluation_instruction)

loss = loss_fn(answer)
loss.backward()
optimizer.step()

__import__("pprint").pprint(answer)
