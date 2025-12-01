
import requests
import streamlit as st
import pandas as pd

st.header("Build Your Best Monster-Fighter")

st.image("images/banner.jpg", width = 250)

st.write("---")

race_list = []

race_data = requests.get(f"https://www.dnd5eapi.co/api/2014/races/")
race_dict = race_data.json()
for item in race_dict["results"]:
    race_list.append(item["name"])

st.subheader("Pick a Race:")

race = st.selectbox("Choose Wisely:",
             race_list)

if "race_button_on" not in st.session_state:
    st.session_state["race_button_on"] = False

def button_click_on():
    st.session_state["race_button_on"] = True

st.button("See Race Stats", on_click = button_click_on)

if st.session_state["race_button_on"]:
    my_info = requests.get(f"https://www.dnd5eapi.co/api/2014/races/{race.lower()}")
    my_json = my_info.json()

    st.image(f"images/{race}.jpg", width = 250)

    traits_list = []
    for item in my_json["traits"]:
        traits_list.append(item["name"])

    if traits_list != []:
        traits_tab = st.expander("Traits")
        for trait in traits_list:
            traits_tab.write(f"- {trait}")
                
    bonus_list = []
    for item in my_json["ability_bonuses"]:
        bonus_list.append([item["ability_score"]["index"], item["bonus"]])

    for i in range(len(bonus_list)):
        if bonus_list[i][0] == "str":
            bonus_list[i][0] = "Strength"
        elif bonus_list[i][0] == "cha":
            bonus_list[i][0] = "Charisma"
        elif bonus_list[i][0] == "dex":
            bonus_list[i][0] = "Dexterity"
        elif bonus_list[i][0] == "int":
            bonus_list[i][0] = "Intelligence"
        elif bonus_list[i][0] == "wis":
            bonus_list[i][0] = "Wisdom"
        elif bonus_list[i][0] == "con":
            bonus_list[i][0] = "Constitution"

    

    if bonus_list != []:    
        bonus_tab = st.expander("Ability Bonuses")
        for bonus in bonus_list:
            bonus_tab.write(f"- {bonus[0]}: +{bonus[1]}")

    languages_list = []
    for item in my_json["languages"]:
        languages_list.append(item["name"])
    if languages_list != []:    
        language_tab = st.expander("Languages")
        for language in languages_list:
            language_tab.write(f"- {language}")

    if my_json["subraces"] != []:
        subrace_data = requests.get(f"https://www.dnd5eapi.co/api/2014/subraces/{my_json['subraces'][0]['index']}/")
        subrace_json = subrace_data.json()
        subrace_tab = st.expander("Subraces")
        subrace_tab.write(f"- {subrace_json['name']}: {subrace_json['desc']}")

        subrace_choice = subrace_tab.selectbox("Equip Subrace?", ["No", "Yes"])

        if subrace_choice == "Yes":
            subrace = my_json['subraces'][0]["name"]
        else:
            subrace = "None"
        
st.write("---")

class_list = []

class_data = requests.get(f"https://www.dnd5eapi.co/api/2014/classes/")
class_dict = class_data.json()
for item in class_dict["results"]:
    class_list.append(item["name"])

st.subheader("Pick a Class:")

clash = st.selectbox("Choose Wisely:",
             class_list)

if "class_button_on" not in st.session_state:
    st.session_state["class_button_on"] = False

def on_button_click():
    st.session_state["class_button_on"] = True

st.button("See Class Stats", on_click = on_button_click)

if st.session_state["class_button_on"]:
    class_info = requests.get(f"https://www.dnd5eapi.co/api/2014/classes/{clash.lower()}")
    class_json = class_info.json()

    st.image(f"images/{clash}.jpg", width = 250)

    proficiency_list = []

    number = class_json["proficiency_choices"][0]["choose"]

    for item in class_json["proficiency_choices"][0]["from"]["options"]:
        proficiency_list.append(item["item"]["name"][7:])

    if proficiency_list != []:
        proficiency_tab = st.expander("Proficiencies")
        proficiency_tab.write(f"Time to select proficiencies! {class_json['proficiency_choices'][0]['desc']}:")
        proficiencies = proficiency_tab.multiselect(f"Please Select {number}:", proficiency_list, max_selections = number)

    
    weapons_and_armor_list = []

    for item in class_json["proficiencies"]:
        if "Saving Throw:" not in item["name"]:
            weapons_and_armor_list.append(item["name"])

    if weapons_and_armor_list != []:
        armor_tab = st.expander("Weapons and Armor Proficiencies")
        for thing in weapons_and_armor_list:
            armor_tab.write(f"- {thing}")
    
    starting_equipment_list = []
    
    for item in class_json["starting_equipment"]:
        starting_equipment_list.append(item["equipment"]["name"])
        
    if starting_equipment_list != [] or starting_equipment_list == []:
        starting_equipment_tab = st.expander("Starting Equipment")
        for thing in starting_equipment_list:
            starting_equipment_tab.write(f"- {thing}")

        starting_choices = []

        
        for item in class_json["starting_equipment_options"]:

            if " or (c)" in item["desc"]:
                choices = item["desc"][4:].split(", (b) ")
                choices1 = choices[1].split(", or (c) ")
                del choices[1]
                for item in choices1:
                    choices.append(item)

            

            else:
                choices = item["desc"][4:].split(" or (b) ")

            if len(choices) == 1:
                starting_equipment_tab.write(f"- {item['desc'].title()}")
                starting_equipment_list.append(item['desc'].title())
                continue

            for i in range(len(choices)):
                if "(if proficient)" in choices[i]:
                    choices[i] = choices[i][0:-15]

            choice = starting_equipment_tab.radio("Select Your Starting Equipment:", choices)
            
            starting_choices.append(choice)
        
    if class_json["subclasses"] != []:
        subclass_data = requests.get(f"https://www.dnd5eapi.co/api/2014/subclasses/{class_json['subclasses'][0]['index']}/")
        subclass_json = subclass_data.json()
        subclass_tab = st.expander("Subclasses")
        subclass_tab.write(f"- {subclass_json['name']}: {subclass_json['desc'][0]}")

        subclass_choice = subclass_tab.selectbox("Equip Subclass?", ["No", "Yes"])

        if subclass_choice == "Yes":
            subclass = class_json['subclasses'][0]["name"]
        else:
            subclass = "None"



st.write("---")

st.subheader("Choose Your Order Alignment:")

trait1 = st.select_slider("", ["Lawful", "Neutral", "Chaotic"])

st.subheader("Choose Your Morality Alignment:")

trait2 = st.select_slider("", ["Good", "Neutral", "Evil"])


st.write("---")

#DYNAMIC GRAPH

st.subheader("Average Monster Ability Scores")
st.write("Consider this graph when selecting your fighter's characteristics.")

monster_data = requests.get("https://www.dnd5eapi.co/api/2014/monsters/")
monster_dict = monster_data.json()

str_total = 0
dex_total = 0
con_total = 0
int_total = 0
wis_total = 0
cha_total = 0

monster_list = []

for item in monster_dict["results"]:

    monster_list.append(item["index"])


for monster in monster_list[0:201:10]:

    
    data = requests.get(f"https://www.dnd5eapi.co/api/2014/monsters/{monster}")
    json = data.json()

    str_total += int(json["strength"])
    dex_total += int(json["dexterity"])
    con_total += int(json["constitution"])
    int_total += int(json["intelligence"])
    wis_total += int(json["wisdom"])
    cha_total += int(json["charisma"])
  
    

str_average = int(str_total/20)
dex_average = int(dex_total/20)
con_average = int(con_total/20)
int_average = int(int_total/20)
wis_average = int(wis_total/20)
cha_average = int(cha_total/20)

stats_dict = {"Strength": str_average, "Dexterity": dex_average, "Constitution": con_average, "Intelligence": int_average, "Wisdom": wis_average, "Charisma": cha_average}

if "stats_set" not in st.session_state:
    st.session_state["stats_set"] = "all abilities"
st.radio("which ability scores are you most concerned about?:", ["all abilities", "physical abilities", "mental abilities"], key="stats_set")

ability_group = st.session_state["stats_set"]

if ability_group == "physical abilities":
    
    stats_dict = {"Strength": str_average, "Dexterity": dex_average, "Constitution": con_average}

elif ability_group == "mental abilities":

    stats_dict = {"Intelligence": int_average, "Wisdom": wis_average, "Charisma": cha_average}



st.write("---")
st.bar_chart(stats_dict)

st.write("Obviously many monsters have vastly different stats than this graph implies, but it is important to build your character so they are able to fight the widest range of foes possible.")

st.write("---")

finalize = st.button("Confirm Character Traits")

if finalize:

    st.balloons()

    st.subheader("You Have Completed Your Character!")

    st.image("images/final.jpg", width = 800)
    
    st.write("Your Character's Stats Are:")
    st.write(f"Race: {race}")
    try:
        st.write(f"Subrace: {subrace}")
    except:
        st.write(f"Subrace: None")
        
    st.write(f"Class: {clash}")
    try:
        st.write(f"Subclass: {subclass}")
    except:
        st.write(f"Subclass: None")

    alignment = trait1 + " " + trait2
    st.write(f"Alignment: {alignment}")

    st.image("images/fight.jpg", width = 800)

    st.write("You're all ready to take on your first monster! Good luck!")
    




