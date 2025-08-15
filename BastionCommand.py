import streamlit as st
import pandas as pd
# from supabase import create_client, Client # Uncomment when ready
import time
import json
import random

# --- CONFIGURATION & INITIALIZATION ---
st.set_page_config(
    page_title="Bastion Manager",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- AESTHETICS & CUSTOM CSS ---
def load_css():
    """Injects custom CSS for a D&D-inspired aesthetic."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=IM+Fell+English+SC&family=Libre+Baskerville:ital@0;1&display=swap');

        /* Main app styling */
        .stApp {
            background-image: url("https://www.transparenttextures.com/patterns/crissxcross.png");
            background-color: #2E2A24; /* A dark, parchment-like brown */
        }

        /* Main content area */
        .main .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            padding-left: 5rem;
            padding-right: 5rem;
        }

        /* Sidebar styling */
        .stSidebar {
            background-color: #1a1814;
        }

        /* Font styles */
        h1, h2, h3, h4, h5, h6 {
            font-family: 'IM Fell English SC', serif;
            color: #D4AF37; /* Gold color for headers */
        }
        .stMarkdown, p, .stButton > button, .stSelectbox > div > div, .stTextInput > div > div > input {
            font-family: 'Libre Baskerville', serif;
            color: #EAE0C8; /* Cream/parchment color for text */
        }

        /* Custom container style for a "scroll" or "tablet" effect */
        .st-emotion-cache-1r6slb0 {
            border: 2px solid #5a4d39;
            background-color: #3c352a;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 8px 0 rgba(0,0,0,0.5);
            margin-bottom: 20px;
        }

        /* Button styling */
        .stButton > button {
            border: 2px solid #D4AF37;
            background-color: transparent;
            color: #D4AF37;
            padding: 10px 24px;
            border-radius: 8px;
            transition: all 0.3s ease-in-out;
        }
        .stButton > button:hover {
            background-color: #D4AF37;
            color: #1a1814;
            border-color: #D4AF37;
        }
        .stButton > button:active {
            background-color: #b89a31 !important;
            color: #1a1814 !important;
        }
        
        /* Disabled button styling */
        .stButton > button:disabled {
            border-color: #5a4d39;
            color: #5a4d39;
            background-color: #3c352a;
        }

        /* Metric styling */
        .st-emotion-cache-1g8m52x {
            background-color: #3c352a;
            border: 1px solid #5a4d39;
            border-radius: 8px;
            padding: 1rem;
        }
        .st-emotion-cache-1g8m52x p {
            font-family: 'IM Fell English SC', serif;
        }

    </style>
    """, unsafe_allow_html=True)

load_css()

# --- SUPABASE CONNECTION (Placeholder) ---
# SUPABASE_URL = st.secrets["supabase"]["url"]
# SUPABASE_KEY = st.secrets["supabase"]["key"]
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- COMPREHENSIVE RULES ENGINE ---
from rules import FACILITY_RULES, BASTION_EVENTS, SPECIAL_FACILITY_ACQUISITION

# --- MOCK DATA ---
def get_mock_data():
    return {
        "campaign": {"campaign_name": "The Crimson Crown", "current_day": 127},
        "characters": [
            {"id": 1, "name": "Elara Meadowlight", "level": 9},
            {"id": 2, "name": "Kaelen Shadowhand", "level": 5},
            {"id": 3, "name": "DM", "level": 99},
        ],
        "bastions": [
            {
                "id": 101, "character_id": 1, "name": "Aegis Tower", "defenders": 12,
                "facilities": [
                    {"id": 1, "name": "Arcane Study", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 2, "name": "Smithy", "type": "Special", "status": "Crafting Magic Item", "order_progress": 4, "order_duration": 20},
                    {"id": 3, "name": "Barrack", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 4, "name": "Library", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 5, "name": "Bedroom", "type": "Basic", "size": "Roomy"},
                ]
            },
            {
                "id": 102, "character_id": 2, "name": "The Gilded Serpent", "defenders": 4,
                "facilities": [
                    {"id": 6, "name": "Garden", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 7, "name": "Workshop", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 10, "name": "Kitchen", "type": "Basic", "size": "Cramped"},
                ]
            }
        ],
        "log": [
            "Day 126: A strange guest arrived at Aegis Tower, offering a gift of 200 GP.",
            "Day 123: Elara's Smithy began work on a +1 Longsword.",
            "Day 120: Kaelen's bastion was maintained. All is well.",
        ]
    }

# --- STATE MANAGEMENT ---
if 'data' not in st.session_state:
    st.session_state.data = get_mock_data()
if 'current_player' not in st.session_state:
    st.session_state.current_player = "Elara Meadowlight"

# --- HELPER FUNCTIONS ---
def get_character_by_name(name):
    for char in st.session_state.data['characters']:
        if char['name'] == name: return char
    return None

def get_bastion_by_char_id(char_id):
    for bastion in st.session_state.data['bastions']:
        if bastion['character_id'] == char_id: return bastion
    return None

def add_log_entry(day, message):
    st.session_state.data['log'].insert(0, f"Day {day}: {message}")

# --- UI: PROPRIETOR VIEW ---
def proprietor_view():
    st.title("✒️ Proprietor's Ledger")
    st.markdown("---")

    char_name = st.session_state.current_player
    character = get_character_by_name(char_name)
    if not character or character['name'] == "DM":
        st.warning("Please select a valid character from the sidebar.")
        return

    bastion = get_bastion_by_char_id(character['id'])
    if not bastion:
        st.error(f"No bastion found for {char_name}.")
        return

    st.header(f"{bastion['name']}")
    st.caption(f"Managed by {character['name']} | Level {character['level']} | Defenders: {bastion['defenders']}")

    # --- Facility Management Tab ---
    st.subheader("Facilities & Orders")
    
    # Global Maintain Order
    if st.button("Issue 'Maintain' Order to Entire Bastion (Triggers Bastion Event)"):
        # This is a special order that takes a full turn
        # In a real app, you'd flag the whole bastion as 'Maintaining'
        # For now, we'll just trigger the event roll.
        roll = random.randint(1, 100)
        event_name = "All Is Well" # Default
        for r, name in BASTION_EVENTS.items():
            if roll in r:
                event_name = name
                break
        
        message = f"{bastion['name']} was maintained. Event: **{event_name}**."
        
        if event_name == "Attack":
            dice_rolls = [random.randint(1, 6) for _ in range(6)]
            losses = dice_rolls.count(1)
            bastion['defenders'] = max(0, bastion['defenders'] - losses)
            message += f" The bastion was attacked! It lost {losses} defenders in the fray. (Rolls: {dice_rolls})"

        st.success(f"Maintain order issued. Rolled {roll} on the event table: {event_name}!")
        add_log_entry(st.session_state.data['campaign']['current_day'], message)
        time.sleep(2)
        st.rerun()


    for facility in bastion['facilities']:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"**{facility['name']}** ({facility['type']})")
                if facility['type'] == 'Special':
                    if facility['status'] == 'Idle':
                        st.markdown(f"Status: <span style='color: #82E0AA;'>Idle</span>", unsafe_allow_html=True)
                    else:
                        progress = facility['order_progress']
                        duration = facility['order_duration']
                        st.markdown(f"Status: <span style='color: #F7DC6F;'>{facility['status']}</span>", unsafe_allow_html=True)
                        st.progress(progress / duration if duration > 0 else 0, text=f"{progress}/{duration} Days")
                else:
                     st.markdown(f"Size: {facility.get('size', 'N/A')}")

            with col2:
                if facility['type'] == 'Special' and facility['status'] == 'Idle':
                    if st.button("Issue Order", key=f"order_{facility['id']}"):
                        st.session_state.selected_facility = facility['id']

            # Order Modal Logic
            if 'selected_facility' in st.session_state and st.session_state.selected_facility == facility['id']:
                with st.form(key=f"form_{facility['id']}"):
                    st.subheader(f"Issue Order: {facility['name']}")
                    rules = FACILITY_RULES.get(facility['name'], {})
                    available_orders = list(rules.get("orders", {}).keys())

                    if not available_orders:
                        st.warning("No orders defined for this facility.")
                        if st.form_submit_button("Cancel"):
                            del st.session_state.selected_facility
                            st.rerun()
                    else:
                        order_choice = st.selectbox("Choose an order:", available_orders)
                        order_details = rules["orders"][order_choice]
                        st.caption(f"Duration: {order_details['duration']} days | Cost: {order_details['cost_gp']} GP")
                        
                        if st.form_submit_button("Confirm Order"):
                            facility['status'] = order_choice
                            facility['order_progress'] = 0
                            facility['order_duration'] = order_details['duration']
                            add_log_entry(st.session_state.data['campaign']['current_day'], f"{char_name}'s {facility['name']} began the order: {order_choice}.")
                            del st.session_state.selected_facility
                            st.success(f"Order issued to {facility['name']}!")
                            time.sleep(1)
                            st.rerun()
    
    # --- Facility Acquisition Tab ---
    st.markdown("---")
    st.subheader("Acquire New Facilities")

    # Special Facilities
    num_special_facilities = len([f for f in bastion['facilities'] if f['type'] == 'Special'])
    max_special_facilities = SPECIAL_FACILITY_ACQUISITION.get(character['level'], 0)
    
    st.markdown(f"**Special Facilities:** {num_special_facilities} / {max_special_facilities} owned.")
    if num_special_facilities < max_special_facilities:
        owned_names = [f['name'] for f in bastion['facilities']]
        available_special = [name for name, rules in FACILITY_RULES.items() if rules['type'] == 'Special' and name not in owned_names and character['level'] >= rules['level']]
        
        if available_special:
            new_special = st.selectbox("Choose a new Special Facility to acquire:", available_special)
            if st.button(f"Acquire {new_special} (Free with level up)"):
                new_id = max(f['id'] for b in st.session_state.data['bastions'] for f in b['facilities']) + 1
                bastion['facilities'].append({"id": new_id, "name": new_special, "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0})
                add_log_entry(st.session_state.data['campaign']['current_day'], f"{char_name} has acquired a new facility: {new_special}!")
                st.success(f"{new_special} has been added to your bastion!")
                time.sleep(1)
                st.rerun()
        else:
            st.info("No new Special Facilities available at your current level.")
    else:
        st.info("You have reached your maximum number of Special Facilities for your level.")

    # Basic Facilities
    st.markdown("**Basic Facilities:**")
    available_basic = [name for name, rules in FACILITY_RULES.items() if rules['type'] == 'Basic']
    
    col1, col2 = st.columns(2)
    with col1:
        new_basic_name = st.selectbox("Choose a Basic Facility to build:", available_basic)
    with col2:
        new_basic_size = st.selectbox("Choose size:", ["Cramped", "Roomy", "Vast"])

    cost_info = FACILITY_RULES[new_basic_name]['add_cost'][new_basic_size]
    if st.button(f"Build {new_basic_name} ({new_basic_size}) - Cost: {cost_info['cost_gp']} GP, Time: {cost_info['time_days']} days"):
        # This is a placeholder for the transaction. In a real app, you'd start an order.
        st.success(f"Construction order for {new_basic_name} has been issued!")
        add_log_entry(st.session_state.data['campaign']['current_day'], f"{char_name} has begun construction on a new {new_basic_name}.")
        time.sleep(1)
        st.rerun()


# --- UI: COMMUNAL VIEW ---
def communal_view():
    st.title("🏰 The Bastion's Hearth")
    st.markdown("---")
    data = st.session_state.data
    total_defenders = sum(b['defenders'] for b in data['bastions'])
    col1, col2, col3 = st.columns(3)
    col1.metric(label="Campaign Name", value=data['campaign']['campaign_name'])
    col2.metric(label="Current In-Game Day", value=data['campaign']['current_day'])
    col3.metric(label="Total Bastion Defenders", value=total_defenders)
    st.markdown("---")
    st.subheader("Recent Bastion Activity")
    with st.container():
        for log_entry in data['log']:
            st.markdown(f"> {log_entry}")

# --- UI: DM VIEW ---
def dm_view():
    st.title("👑 The Architect's Sanctum")
    st.markdown("---")
    st.header("Campaign Time Management")
    current_day = st.session_state.data['campaign']['current_day']
    st.metric("Current In-Game Day", current_day)
    with st.form("time_advance_form"):
        days_to_advance = st.number_input("Days to Advance:", min_value=1, step=1, value=7)
        submitted = st.form_submit_button("Advance Time")
        if submitted:
            new_day = current_day + days_to_advance
            st.session_state.data['campaign']['current_day'] = new_day
            for bastion in st.session_state.data['bastions']:
                for facility in bastion['facilities']:
                    if facility['status'] != 'Idle':
                        facility['order_progress'] += days_to_advance
                        if facility['order_progress'] >= facility['order_duration']:
                            completed_order = facility['status']
                            facility['status'] = 'Idle'
                            facility['order_progress'] = 0
                            facility['order_duration'] = 0
                            owner_name = [c['name'] for c in st.session_state.data['characters'] if c['id'] == bastion['character_id']][0]
                            add_log_entry(new_day, f"{owner_name}'s {facility['name']} has completed the order: {completed_order}.")
            st.success(f"Time advanced by {days_to_advance} days. New day is {new_day}.")
            time.sleep(2)
            st.rerun()

# --- MAIN APP ROUTER ---
st.sidebar.title("Navigation")
st.sidebar.markdown("---")
player_list = [char['name'] for char in st.session_state.data['characters']]
selected_player = st.sidebar.selectbox("Select Your Character:", options=player_list, index=player_list.index(st.session_state.current_player))
st.session_state.current_player = selected_player

if selected_player == "DM":
    view = "DM View"
else:
    view = st.sidebar.radio("Select View", ("Communal View", "Proprietor's View"), label_visibility="hidden")

st.sidebar.markdown("---")
st.sidebar.info("This app helps manage D&D 5e Bastions. All data is currently mocked and will reset on refresh.")

if view == "Communal View":
    communal_view()
elif view == "Proprietor's View":
    proprietor_view()
elif view == "DM View":
    dm_view()

# --- RULES FILE (rules.py) ---
# This content should be in a separate file named `rules.py` in the same directory.
# For this self-contained example, it's included here.
# In a real project, you would `import rules` at the top.
if 'rules_defined' not in st.session_state:
    st.session_state.rules_defined = True
    # This is a large block of data, so we only define it once.
    
    # This data would be in a separate file `rules.py`
    SPECIAL_FACILITY_ACQUISITION = {
        5: 2, 6: 2, 7: 2, 8: 2,
        9: 4, 10: 4, 11: 4, 12: 4,
        13: 5, 14: 5, 15: 5, 16: 5,
        17: 6, 18: 6, 19: 6, 20: 6
    }

    BASTION_EVENTS = {
        range(1, 51): "All Is Well",
        range(51, 56): "Attack",
        range(56, 59): "Criminal Hireling",
        range(59, 64): "Extraordinary Opportunity",
        range(64, 73): "Friendly Visitors",
        range(73, 77): "Guest",
        range(77, 80): "Lost Hirelings",
        range(80, 84): "Magical Discovery",
        range(84, 92): "Refugees",
        range(92, 99): "Request for Aid",
        range(99, 101): "Treasure",
    }

    FACILITY_RULES = {
        # --- Basic Facilities ---
        "Bedroom": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}},
        "Dining Room": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}},
        "Parlor": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}},
        "Courtyard": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}},
        "Kitchen": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}},
        "Storage": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}},
        
        # --- Level 5 Special Facilities ---
        "Arcane Study": {"type": "Special", "level": 5, "orders": {"Craft: Arcane Focus": {"duration": 7, "cost_gp": 0}, "Craft: Book": {"duration": 7, "cost_gp": 10}, "Craft: Magic Item (Arcana)": {"duration": 20, "cost_gp": 250}}}, # Example values for magic item
        "Armory": {"type": "Special", "level": 5, "orders": {"Stock Armory": {"duration": 7, "cost_gp": 100}}}, # Cost is per defender, simplified here
        "Barrack": {"type": "Special", "level": 5, "orders": {"Recruit: Bastion Defenders (4)": {"duration": 7, "cost_gp": 0}}},
        "Garden": {"type": "Special", "level": 5, "orders": {"Harvest: Decorative": {"duration": 7, "cost_gp": 0}, "Harvest: Food": {"duration": 7, "cost_gp": 0}, "Harvest: Herb": {"duration": 7, "cost_gp": 0}, "Harvest: Poison": {"duration": 7, "cost_gp": 0}}},
        "Library": {"type": "Special", "level": 5, "orders": {"Research: Topical Lore": {"duration": 7, "cost_gp": 0}}},
        "Sanctuary": {"type": "Special", "level": 5, "orders": {"Craft: Sacred Focus": {"duration": 7, "cost_gp": 0}}},
        "Smithy": {"type": "Special", "level": 5, "orders": {"Craft: Smith's Tools Item": {"duration": 14, "cost_gp": 50}, "Craft: Magic Item (Armament)": {"duration": 20, "cost_gp": 250}}}, # Example values
        "Storehouse": {"type": "Special", "level": 5, "orders": {"Procure Goods (500 GP)": {"duration": 7, "cost_gp": 500}, "Sell Goods": {"duration": 7, "cost_gp": 0}}},
        "Workshop": {"type": "Special", "level": 5, "orders": {"Craft: Adventuring Gear": {"duration": 10, "cost_gp": 25}, "Craft: Magic Item (Implement)": {"duration": 20, "cost_gp": 250}}}, # Example values

        # --- Level 9 Special Facilities ---
        "Gaming Hall": {"type": "Special", "level": 9, "orders": {"Run Gambling Hall": {"duration": 7, "cost_gp": 0}}},
        "Greenhouse": {"type": "Special", "level": 9, "orders": {"Harvest: Healing Herbs": {"duration": 7, "cost_gp": 0}, "Harvest: Poison": {"duration": 7, "cost_gp": 0}}},
        "Laboratory": {"type": "Special", "level": 9, "orders": {"Craft: Alchemist's Supplies": {"duration": 7, "cost_gp": 25}, "Craft: Poison": {"duration": 7, "cost_gp": 50}}}, # Example values
        "Sacristy": {"type": "Special", "level": 9, "orders": {"Craft: Holy Water": {"duration": 7, "cost_gp": 25}, "Craft: Magic Item (Relic)": {"duration": 20, "cost_gp": 250}}},
        "Scriptorium": {"type": "Special", "level": 9, "orders": {"Craft: Book Replica": {"duration": 7, "cost_gp": 10}, "Craft: Spell Scroll": {"duration": 5, "cost_gp": 100}, "Craft: Paperwork": {"duration": 7, "cost_gp": 50}}},
        "Stable": {"type": "Special", "level": 9, "orders": {"Buy/Sell Animals": {"duration": 7, "cost_gp": 0}}},
        "Teleportation Circle": {"type": "Special", "level": 9, "orders": {"Recruit: Spellcaster": {"duration": 7, "cost_gp": 0}}},
        "Theater": {"type": "Special", "level": 9, "orders": {"Stage Production": {"duration": 21, "cost_gp": 100}}},
        "Training Area": {"type": "Special", "level": 9, "orders": {"Train: Battle Expert": {"duration": 7, "cost_gp": 0}, "Train: Skills Expert": {"duration": 7, "cost_gp": 0}}},
        "Trophy Room": {"type": "Special", "level": 9, "orders": {"Research: Lore": {"duration": 7, "cost_gp": 0}, "Research: Trinket Trophy": {"duration": 7, "cost_gp": 0}}},
        
        # --- Level 13 Special Facilities ---
        "Archive": {"type": "Special", "level": 13, "orders": {"Research: Helpful Lore": {"duration": 7, "cost_gp": 0}}},
        "Meditation Chamber": {"type": "Special", "level": 13, "orders": {"Empower: Inner Peace": {"duration": 7, "cost_gp": 0}}},
        "Menagerie": {"type": "Special", "level": 13, "orders": {"Recruit: Creature (Ape)": {"duration": 7, "cost_gp": 500}, "Recruit: Creature (Lion)": {"duration": 7, "cost_gp": 1000}}},
        "Observatory": {"type": "Special", "level": 13, "orders": {"Empower: Eldritch Discovery": {"duration": 7, "cost_gp": 0}}},
        "Pub": {"type": "Special", "level": 13, "orders": {"Research: Information Gathering": {"duration": 7, "cost_gp": 0}}},
        "Reliquary": {"type": "Special", "level": 13, "orders": {"Harvest: Talisman": {"duration": 7, "cost_gp": 0}}},
        
        # --- Level 17 Special Facilities ---
        "Demiplane": {"type": "Special", "level": 17, "orders": {"Empower: Arcane Resilience": {"duration": 7, "cost_gp": 0}}},
        "Guildhall": {"type": "Special", "level": 17, "orders": {"Assign: Adventurers' Guild": {"duration": 7, "cost_gp": 100}, "Assign: Thieves' Guild": {"duration": 7, "cost_gp": 250}}},
        "Sanctum": {"type": "Special", "level": 17, "orders": {"Empower: Fortifying Rites": {"duration": 7, "cost_gp": 0}}},
        "War Room": {"type": "Special", "level": 17, "orders": {"Recruit: Lieutenant": {"duration": 7, "cost_gp": 0}, "Recruit: Soldiers (100)": {"duration": 7, "cost_gp": 100}}}, # Cost is per day
    }

