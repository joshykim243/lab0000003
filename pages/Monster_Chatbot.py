import requests
import streamlit as st
import pandas as pd
import google.generativeai as genai

api_key = st.secrets.get("GOOGLE_API_KEY", None)

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-1.5-flash")
else:
    model = None

@st.cache_data
def get_monster_index():
    """Return list of all monsters (name + index) from the D&D 5e 2014 API."""
    url = "https://www.dnd5eapi.co/api/2014/monsters/"
    response = requests.get(url)
    response.raise_for_status()
    data = response.json()
    return data["results"]


@st.cache_data
def get_monster_details(monster_index: str):
    """Return full JSON data for a single monster."""
    url = f"https://www.dnd5eapi.co/api/2014/monsters/{monster_index}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def extract_key_stats(monster_json: dict) -> dict:
    """Pull out the stats we want to feed into the LLM."""
    ac = monster_json.get("armor_class", None)
    if isinstance(ac, list) and len(ac) > 0:
        ac_value = ac[0].get("value", None)
    else:
        ac_value = ac

    stats = {
        "name": monster_json.get("name", "Unknown"),
        "size": monster_json.get("size", "Unknown"),
        "type": monster_json.get("type", "Unknown"),
        "alignment": monster_json.get("alignment", "Unknown"),
        "hit_points": monster_json.get("hit_points", "Unknown"),
        "armor_class": ac_value,
        "strength": monster_json.get("strength", "Unknown"),
        "dexterity": monster_json.get("dexterity", "Unknown"),
        "constitution": monster_json.get("constitution", "Unknown"),
        "intelligence": monster_json.get("intelligence", "Unknown"),
        "wisdom": monster_json.get("wisdom", "Unknown"),
        "charisma": monster_json.get("charisma", "Unknown"),
        "challenge_rating": monster_json.get("challenge_rating", "Unknown"),
        "special_abilities": [
            a.get("name", "") for a in (monster_json.get("special_abilities", []) or [])
        ],
        "actions": [
            a.get("name", "") for a in (monster_json.get("actions", []) or [])
        ],
    }
    return stats


def build_system_prompt(monster_stats_list):
    """
    Build a system-style prompt that describes the available data
    and what the chatbot is allowed to do.
    """
    lines = [
        "You are a Dungeons & Dragons rules assistant and combat coach.",
        "You must answer questions ONLY using the monster data provided below.",
        "Do not invent new abilities, spells, or stats that are not present in this data.",
        "If the user asks something you cannot answer from this data,",
        "explain that the information is not available instead of guessing.",
        "",
        "Here is the monster data you can rely on:",
    ]

    for stats in monster_stats_list:
        lines.append(f"\n=== {stats['name']} ===")
        lines.append(
            f"Size: {stats['size']}, Type: {stats['type']}, Alignment: {stats['alignment']}"
        )
        lines.append(
            f"HP: {stats['hit_points']}, AC: {stats['armor_class']}, "
            f"STR: {stats['strength']}, DEX: {stats['dexterity']}, "
            f"CON: {stats['constitution']}, INT: {stats['intelligence']}, "
            f"WIS: {stats['wisdom']}, CHA: {stats['charisma']}"
        )
        lines.append(f"Challenge Rating: {stats['challenge_rating']}")
        if stats["special_abilities"]:
            lines.append(
                "Special Abilities: " + ", ".join(stats["special_abilities"][:5])
            )
        if stats["actions"]:
            lines.append("Actions: " + ", ".join(stats["actions"][:5]))

    lines.append(
        "\nYour job is to have a helpful, conversational chat with the user "
        "about these monsters, combat tactics, and how to handle them."
    )

    return "\n".join(lines)


st.header("Phase 4: Monster Chatbot (Gemini-Powered)")
st.write(
    """
This page implements an **AI chatbot** that can have an intelligent conversation
about D&D monsters using data pulled from the official **D&D 5e 2014 API**.

1. Pick one or more monsters as the knowledge base.
2. Ask the chatbot questions about those monsters, combat strategy, or how
   an adventuring party might handle them.
3. The chatbot will answer **only** using the stats and abilities passed into the LLM.
"""
)

if not api_key:
    st.error(
        "No Google API key found. Add `GOOGLE_API_KEY` to your `.streamlit/secrets.toml` "
        "file to enable the chatbot."
    )
    st.stop()

if model is None:
    st.error("Gemini model is not configured correctly.")
    st.stop()

st.subheader("1. Choose Monster Data for the Chatbot")

try:
    monsters = get_monster_index()
except Exception as e:
    st.error(f"Error contacting the D&D API: {e}")
    st.stop()

monster_names = [m["name"] for m in monsters]

selected_names = st.multiselect(
    "Select one or more monsters as the knowledge base:",
    options=monster_names,
    default=monster_names[:1] if monster_names else [],
)

if not selected_names:
    st.info("Select at least one monster above to start the chatbot.")
    st.stop()

selected_stats = []
for name in selected_names:
    try:
        idx = next(m["index"] for m in monsters if m["name"] == name)
        monster_json = get_monster_details(idx)
        selected_stats.append(extract_key_stats(monster_json))
    except StopIteration:
        st.warning(f"Could not find index for monster '{name}'. Skipping.")
    except Exception as e:
        st.warning(f"Error fetching details for '{name}': {e}")

if not selected_stats:
    st.error("No monster data could be loaded. Please try a different selection.")
    st.stop()

st.write("### Selected Monsters (from the D&D API)")

df = pd.DataFrame(
    [
        {
            "name": s["name"],
            "size": s["size"],
            "type": s["type"],
            "alignment": s["alignment"],
            "HP": s["hit_points"],
            "AC": s["armor_class"],
            "CR": s["challenge_rating"],
        }
        for s in selected_stats
    ]
).set_index("name")

st.table(df)

with st.expander("Show abilities & actions"):
    for s in selected_stats:
        st.markdown(f"**{s['name']}**")
        st.write("• Special Abilities:", ", ".join(s["special_abilities"]) or "None")
        st.write("• Actions:", ", ".join(s["actions"]) or "None")
        st.write("---")

st.subheader("2. Chat with the Monster Coach")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

system_prompt = build_system_prompt(selected_stats)

for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_message = st.chat_input("Ask about these monsters, tactics, or combat strategy...")

if user_message:
    st.session_state.chat_history.append({"role": "user", "content": user_message})
    with st.chat_message("user"):
        st.markdown(user_message)

    conversation_text = ""
    for m in st.session_state.chat_history:
        speaker = "User" if m["role"] == "user" else "Assistant"
        conversation_text += f"{speaker}: {m['content']}\n"

    full_prompt = (
        system_prompt
        + "\n\n--- Conversation so far ---\n"
        + conversation_text
        + "\nAssistant: Please respond to the user's latest message."
    )

    try:
        with st.chat_message("assistant"):
            with st.spinner("Thinking about monster tactics..."):
                response = model.generate_content(full_prompt)
                assistant_reply = response.text.strip()
                st.markdown(assistant_reply)

        st.session_state.chat_history.append(
            {"role": "assistant", "content": assistant_reply}
        )

    except Exception as e:
        st.error("Sorry, something went wrong while contacting the LLM.")
        st.info(
            "This might be due to rate limits, temporary network issues, "
            "or an invalid request. Please try again in a moment."
        )
        st.caption(f"Debug info: {e}")
