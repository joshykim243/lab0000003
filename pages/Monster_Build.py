import os
import json
from typing import Dict, Any

from google import genai

GEMINI_MODEL = "gemini-1.5-flash"



def _get_api_key() -> str:
    """
    Get the Gemini API key from the environment.

    If you'd rather hard-code it (NOT recommended), you could do:
        return "YOUR_API_KEY"
    """
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GEMINI_API_KEY environment variable not set.\n"
            "Set it first, then run again."
        )
    return api_key


_client = genai.Client(api_key=_get_api_key())


def _call_gemini(prompt: str) -> str:
    """
    Low-level helper: send a prompt to Gemini and return the response text.
    """
    response = _client.models.generate_content(
        model=GEMINI_MODEL,
        contents=prompt
    )
    return (response.text or "").strip()



def generate_rules_explanation(user_question: str) -> str:
    """
    General D&D rules helper.

    Example:
        answer = generate_rules_explanation(
            "How does advantage and disadvantage work in D&D 5e?"
        )
    """
    prompt = f"""
You are a friendly Dungeon Master assistant for Dungeons & Dragons 5th Edition.
Explain rules clearly for a beginner, but don't change the official 5e meaning.

User question:
{user_question}

Requirements:
- Answer in 1–3 short paragraphs.
- Use plain English (no super rule-lawyer jargon).
- If something is ambiguous in the rules, briefly say so.
"""
    return _call_gemini(prompt)


def explain_spell(spell_data: Dict[str, Any]) -> str:
    """
    Take a spell JSON object (from the DnD 5e API) and generate a player-friendly explanation.

    You can call this after fetching a spell from:
        https://www.dnd5eapi.co/api/spells/<spell-index>

    Example usage (in your Phase 2 code):
        from phase3 import explain_spell
        explanation = explain_spell(spell_json)

    Expected keys (typical DnD 5e API format):
        name, desc, range, components, material, duration, casting_time, level, school, classes, etc.
    """
    spell_json_str = json.dumps(spell_data, indent=2)

    prompt = f"""
You are a D&D 5e assistant helping a new player understand a spell.

Here is the raw spell data in JSON format:
{spell_json_str}

Tasks:
1. Start by naming the spell and its level + school (e.g., "Fireball is a 3rd-level evocation spell").
2. Explain what the spell does in 1–2 short paragraphs, in simple language.
3. Mention:
   - casting time
   - range
   - duration
   - key components (verbal, somatic, material) if they matter
4. If there is important tactical advice (e.g., good times to use it), include a brief tip.
"""
    return _call_gemini(prompt)


def explain_monster(monster_data: Dict[str, Any]) -> str:
    """
    Take a monster JSON object (from the DnD 5e API) and generate a flavorful description
    plus tactical overview.

    You can call this after fetching a monster from:
        https://www.dnd5eapi.co/api/monsters/<monster-index>

    Example usage (in your Phase 2 code):
        from phase3 import explain_monster
        explanation = explain_monster(monster_json)
    """
    monster_json_str = json.dumps(monster_data, indent=2)

    prompt = f"""
You are a Dungeon Master assistant describing a D&D 5e monster for players.

Here is the raw monster data in JSON format:
{monster_json_str}

Tasks:
1. Give a short, vivid description of what the monster looks like and feels like to encounter.
2. Summarize its combat style:
   - Is it tanky? sneaky? spellcaster? brute?
   - Any notable abilities or resistances players should watch out for.
3. Give 2–3 quick tips to players on how to survive or counter this monster.
Keep it to about 2–4 short paragraphs total.
"""
    return _call_gemini(prompt)


def generate_story_prompt(character_name: str, character_class: str, character_race: str) -> str:
    """
    Optional fun helper: create a short story hook for a given character.

    You can call this in Phase 2 when the user creates/selects a character and
    wants a story prompt or backstory seed.
    """
    prompt = f"""
You are a D&D storyteller.

Create a short, punchy story hook (about 1 paragraph) for the following character:

Name: {character_name}
Race: {character_race}
Class: {character_class}

The hook should:
- Feel like the start of a quest.
- Include a hint of danger or mystery.
- Be written in second person ("You ...").
"""
    return _call_gemini(prompt)



def main():
    """
    Run this file directly to quickly test Gemini from the terminal.

    Examples:
        python phase3.py
    """
    print("=== Phase 3: Gemini D&D Helper ===")
    print("Type a D&D rules question, or 'q' to quit.\n")

    while True:
        user_q = input("Ask about a rule / spell / idea (or 'q' to quit): ").strip()
        if user_q.lower() in {"q", "quit", "exit"}:
            print("Goodbye!")
            break

        print("\nThinking with Gemini...\n")
        try:
            answer = generate_rules_explanation(user_q)
            print(answer)
        except Exception as e:
            print("Error calling Gemini:", e)
        print("\n" + "-" * 60 + "\n")


if __name__ == "__main__":
    main()
