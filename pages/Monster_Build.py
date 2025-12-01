import requests
import streamlit as st
import pandas as pd
import google.generativeai as genai

api_key = st.secrets.get("GOOGLE_API_KEY", None)

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel("gemini-2.0-flash")
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
    }

    special_abilities = monster_json.get("special_abilities", []) or []
    actions = monster_json.get("actions", []) or []
    stats["special_abilities"] = [a.get("name", "") for a in special_abilities][:3]
    stats["actions"] = [a.get("name", "") for a in actions][:3]

    return stats


def build_prompt(monster1_stats: dict,
                 monster2_stats: dict,
                 focus: str,
                 tone: str) -> str:
    """Create the text prompt that will be sent to Gemini."""
    prompt = f"""
You are an expert Dungeons & Dragons combat coach.

Below are summarized statistics for two monsters, pulled directly from the official D&D 5e 2014 API.
Use ONLY the information given; do not invent new abilities or change any numbers.

MONSTER 1:
{monster1_stats}

MONSTER 2:
{monster2_stats}

User-selected battle focus: {focus}
Desired writing tone: {tone}

TASK:
Write a clear and helpful battle briefing that:
1. Compares the key strengths and weaknesses of the two monsters.
2. Explains how a well-prepared adventuring party should approach fighting EACH monster.
3. Gives at least one concrete tactical tip that follows from the actual stats (e.g., high AC, low HP, high DEX, etc.).

Make it understandable for a player who is new to combat strategy,
but still insightful enough for an experienced player.
Avoid rules-lawyering; focus on practical advice.

Start directly with the analysis; do not restate the instructions.
"""
    return prompt


st.header("Phase 3: LLM-Powered Monster Battle Coach")
st.write(
    """
In this Phase 3 page, we reuse the same **D&D 5e 2014 web API** from Phase 2,
but now we send monster stats into **Google Gemini** to generate a tactical battle briefing.

Use the controls below to pick two monsters and customize how the LLM analyzes them.
"""
)

if not api_key:
    st.warning(
        "No Google API key found. Add `GOOGLE_API_KEY` to your `.streamlit/secrets.toml` "
        "file to enable the LLM features."
    )

# --- Step 1: choose monsters from the API ---

monsters = get_monster_index()
monster_names = [m["name"] for m in monsters]

st.subheader("1. Choose Two Monsters to Analyze")

col1, col2 = st.columns(2)

with col1:
    monster1_name = st.selectbox("Monster 1", monster_names, index=0)

with col2:
    # default to a different monster if possible
    default_index = 1 if len(monster_names) > 1 else 0
    monster2_name = st.selectbox("Monster 2", monster_names, index=default_index)

monster1_index = next(m["index"] for m in monsters if m["name"] == monster1_name)
monster2_index = next(m["index"] for m in monsters if m["name"] == monster2_name)

# --- Step 2: user customizations that affect what goes to the LLM ---

st.subheader("2. Customize the LLM’s Analysis")

focus = st.radio(
    "What should the battle plan prioritize?",
    ["Balanced overview", "Survivability / defense", "Maximum damage", "Crowd control & positioning"],
)

tone = st.select_slider(
    "Choose the tone for the briefing:",
    options=["Serious and tactical", "Friendly coach", "Epic fantasy narrator"],
)

st.write("---")

# --- Step 3: fetch data from API and show processed stats ---

if st.button("Analyze Monsters and Generate LLM Battle Plan", disabled=(model is None)):
    with st.spinner("Contacting the D&D API and preparing data..."):
        monster1_json = get_monster_details(monster1_index)
        monster2_json = get_monster_details(monster2_index)

        monster1_stats = extract_key_stats(monster1_json)
        monster2_stats = extract_key_stats(monster2_json)

        # Show the processed data in a table first (non-LLM analysis)
        st.subheader("Key Stats from the D&D API")

        stats_df = pd.DataFrame(
            [
                {**monster1_stats, "monster": monster1_stats["name"]},
                {**monster2_stats, "monster": monster2_stats["name"]},
            ]
        )

        # put monster name as index and drop long list columns from the table
        table_df = stats_df.set_index("monster").drop(columns=["special_abilities", "actions"])
        st.table(table_df)

        # Also show abilities / actions as bullet lists
        with st.expander(f"{monster1_stats['name']} – Abilities & Actions"):
            st.write("**Special Abilities:**")
            if monster1_stats["special_abilities"]:
                for ability in monster1_stats["special_abilities"]:
                    st.write(f"- {ability}")
            else:
                st.write("- None listed")

            st.write("**Actions:**")
            if monster1_stats["actions"]:
                for action in monster1_stats["actions"]:
                    st.write(f"- {action}")
            else:
                st.write("- None listed")

        with st.expander(f"{monster2_stats['name']} – Abilities & Actions"):
            st.write("**Special Abilities:**")
            if monster2_stats["special_abilities"]:
                for ability in monster2_stats["special_abilities"]:
                    st.write(f"- {ability}")
            else:
                st.write("- None listed")

            st.write("**Actions:**")
            if monster2_stats["actions"]:
                for action in monster2_stats["actions"]:
                    st.write(f"- {action}")
            else:
                st.write("- None listed")

    if model is None:
        st.error("Gemini model is not configured. Add your API key to secrets.toml to run the LLM analysis.")
    else:
        # --- Step 4: send processed data to Gemini ---
        st.subheader("LLM Battle Briefing")

        prompt = build_prompt(
            monster1_stats=monster1_stats,
            monster2_stats=monster2_stats,
            focus=focus,
            tone=tone,
        )

        try:
            with st.spinner("Generating tactical advice with Gemini..."):
                response = model.generate_content(prompt)
            st.write(response.text)
        except Exception as e:
            st.error(f"Something went wrong while calling the Gemini API: {e}")
            st.info("Double-check your API key and internet connection, then try again.")


