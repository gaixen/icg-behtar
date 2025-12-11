import asyncio
import os

from core.agent import RealtimeAudioAgent
from dotenv import load_dotenv


async def main():
    """Main function to start the audio agent"""

    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise ValueError("OPENAI_API_KEY not found in .env file")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    prompt_path = os.path.join(base_dir, "prompt.txt")

    with open(prompt_path, "r", encoding="utf-8") as f:
        system_prompt = f.read()

    agent = RealtimeAudioAgent(api_key, system_prompt)
    await agent.run()


if __name__ == "__main__":
    asyncio.run(main())
