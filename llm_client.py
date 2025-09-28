import httpx
import os
import time

LLM_API_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "mistralai/mistral-7b-instruct"

# sessions: {user_id: {"target_lang": "French", "messages": [], "last_ts": float}}
SESSIONS = {}

async def ask_llm(user_id: int, user_message: str, mode: str = "interaction", target_l: str = 'French') -> str:
    """
    mode can be: presentation / interaction / exit
    """

    # Init session if not exists
    if user_id not in SESSIONS:
        SESSIONS[user_id] = {
            "target_lang": target_l,  
            "messages": [],
            "last_ts": time.time()
        }

    sess = SESSIONS[user_id]
    sess["last_ts"] = time.time()

    # system prompt template
    target_lang = sess["target_lang"]

    SYSTEM_PROMPTS = {
        "presentation": f"""You are a penpal for a language learner.
Your target language is {target_lang}.
Your job:
1. Present yourself in ONE SHORT SENTENCE
    1.1 Generate a random name 
    1.2 Pick your vocation from:
        -- a worker: select your job: can be anything from swe to a fisher
        -- an artist: select what kind
        -- a student: select what you can study
        -- a musician: select an instrument
    1.3 Pick a city you're from, the city must be in a country where {target_lang} is spoken (like Lille for French, Vienna for German etc) 
2. Share ONE short interesting fact about yourself (hobby, pet, trip, concert, etc).
3. Ask the learner a natural question like a classmate would.
4. Explain they can write in {target_lang} or English. You will correct {target_lang} errors, or translate English.
5. Write your full message in BOTH {target_lang} and English.
""",
        "interaction": f"""You are continuing as the same penpal persona in {target_lang}.

- First: if they wrote in {target_lang}, you must highlight mistakes and give corrected versions.
- If they wrote in English, translate to {target_lang} and reply.

- Secondly: respond to the user's message.
- Always keep interaction natural, and end with a follow-up question.
- You must write your full reply in BOTH {target_lang} and English.
""",
        "exit": f"""Stay in persona as the penpal.
The user is leaving. Say goodbye naturally in {target_lang} and English.
"""
    }

    # Build chat history
    messages = [{"role": "system", "content": SYSTEM_PROMPTS[mode]}]
    messages += sess["messages"]
    if user_message:
        messages.append({"role": "user", "content": user_message})

    headers = {
        "Authorization": f"Bearer {os.getenv('OPENAI_API_KEY')}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(LLM_API_URL, headers=headers, json=payload)
        r.raise_for_status()
        answer = r.json()["choices"][0]["message"]["content"]

    # Save to history
    sess["messages"].append({"role": "user", "content": user_message})
    sess["messages"].append({"role": "assistant", "content": answer})

    return answer
