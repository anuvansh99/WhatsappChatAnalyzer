import requests
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")


# Place your OpenRouter API key here
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "meta-llama/llama-4-maverick:free"  # Use a supported model for chat completions

def summarize_last_300_messages(df: pd.DataFrame) -> str:
    """
    Summarizes the last 300 WhatsApp messages using OpenRouter API via requests.
    """
    last_300 = df['message'].tail(300).tolist()
    chat_text = "\n".join([msg for msg in last_300 if msg.strip()])
    prompt = (
        "You are a witty assistant. Summarize the following WhatsApp group chat in a fun and engaging way, "
        "highlighting key moments, jokes, and group dynamics. Be concise and lively!\n\n"
        f"{chat_text}"
    )

    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}]
    }

    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Summary generation failed: {str(e)}")
        return "Could not generate summary."

def generate_300_message_taglines(df: pd.DataFrame) -> dict:
    """
    Creates funny taglines for each user based on their last 300 messages using OpenRouter API via requests.
    """
    taglines = {}
    users = df[
        (df['user'] != 'group_notification') & 
        (df['user'] != 'Meta AI')
    ]['user'].unique()

    for user in users:
        user_msgs = df[df['user'] == user]['message'].tail(300).tolist()
        user_text = "\n".join([msg for msg in user_msgs if msg.strip()])
        if len(user_text.split()) < 20:
            taglines[user] = "Too mysterious for a tagline!"
            continue

        prompt = (
            "Based on the following WhatsApp messages, create a unique, funny, and light-hearted tagline for the user. "
            "Make it 5-7 words, and reflect their chat personality or quirks. Examples: "
            "'King of Random Facts', 'Always Hungry, Never Late', 'Group's Resident Philosopher'.\n\n"
            f"{user_text}"
        )

        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MODEL,
            "messages": [{"role": "user", "content": prompt}]
        }

        try:
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            tagline = result["choices"][0]["message"]["content"].strip().strip('"')
            taglines[user] = tagline
        except Exception as e:
            print(f"Tagline failed for {user}: {str(e)}")
            taglines[user] = "Mystery Member"

    return taglines
