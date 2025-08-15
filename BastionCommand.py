import streamlit as st
import pandas as pd
import requests
import time
import json
import random
from supabase import create_client, Client

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
        .st-emotion-cache-1r6slb0, .bastion-card {
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
        
        /* Mortimer's Log Styling */
        .log-entry {
            border-left: 3px solid #5a4d39; /* Default border color */
            padding-left: 10px;
            margin-bottom: 8px;
        }
        .log-entry-negative { border-left-color: #FF5733; }
        .log-entry-positive { border-left-color: #D4AF37; }
        .log-entry-progress { border-left-color: #F7DC6F; }
        .log-entry-complete { border-left-color: #82E0AA; }

    </style>
    """, unsafe_allow_html=True)

load_css()

# --- SUPABASE CONNECTION ---
@st.cache_resource
def init_connection():
    """Initializes the connection to Supabase."""
    try:
        url = st.secrets["supabase"]["url"]
        key = st.secrets["supabase"]["key"]
        return create_client(url, key)
    except Exception as e:
        st.error(f"Failed to connect to Supabase. Please check your secrets.toml file. Error: {e}")
        return None

supabase = init_connection()

# --- RULES DATA ---
# This data is kept in memory for quick access.
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
    "Bedroom": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}, "enlarge_cost": {"Cramped to Roomy": {"cost_gp": 500, "time_days": 25}, "Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Dining Room": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}, "enlarge_cost": {"Cramped to Roomy": {"cost_gp": 500, "time_days": 25}, "Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Parlor": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}, "enlarge_cost": {"Cramped to Roomy": {"cost_gp": 500, "time_days": 25}, "Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Courtyard": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}, "enlarge_cost": {"Cramped to Roomy": {"cost_gp": 500, "time_days": 25}, "Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Kitchen": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}, "enlarge_cost": {"Cramped to Roomy": {"cost_gp": 500, "time_days": 25}, "Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Storage": {"type": "Basic", "add_cost": {"Cramped": {"cost_gp": 500, "time_days": 20}, "Roomy": {"cost_gp": 1000, "time_days": 45}, "Vast": {"cost_gp": 3000, "time_days": 125}}, "enlarge_cost": {"Cramped to Roomy": {"cost_gp": 500, "time_days": 25}, "Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    
    # --- Level 5 Special Facilities ---
    "Arcane Study": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Craft: Arcane Focus": {"duration": 7, "cost_gp": 0}, "Craft: Book": {"duration": 7, "cost_gp": 10}, "Craft: Magic Item (Arcana)": {"duration": 20, "cost_gp": 250}}},
    "Armory": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Stock Armory": {"duration": 7, "cost_gp": 100}}},
    "Barrack": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Recruit: Bastion Defenders (4)": {"duration": 7, "cost_gp": 0}}, "enlarge_cost": {"Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Garden": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Harvest: Decorative": {"duration": 7, "cost_gp": 0}, "Harvest: Food": {"duration": 7, "cost_gp": 0}, "Harvest: Herb": {"duration": 7, "cost_gp": 0}, "Harvest: Poison": {"duration": 7, "cost_gp": 0}}, "enlarge_cost": {"Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Library": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Research: Topical Lore": {"duration": 7, "cost_gp": 0}}},
    "Sanctuary": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Craft: Sacred Focus": {"duration": 7, "cost_gp": 0}}},
    "Smithy": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Craft: Smith's Tools Item": {"duration": 14, "cost_gp": 50}, "Craft: Magic Item (Armament)": {"duration": 20, "cost_gp": 250}}},
    "Storehouse": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Procure Goods (500 GP)": {"duration": 7, "cost_gp": 500}, "Sell Goods": {"duration": 7, "cost_gp": 0}}},
    "Workshop": {"type": "Special", "level": 5, "size": "Roomy", "orders": {"Craft: Adventuring Gear": {"duration": 10, "cost_gp": 25}, "Craft: Magic Item (Implement)": {"duration": 20, "cost_gp": 250}}},

    # --- Level 9 Special Facilities ---
    "Gaming Hall": {"type": "Special", "level": 9, "size": "Vast", "orders": {"Run Gambling Hall": {"duration": 7, "cost_gp": 0}}},
    "Greenhouse": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Harvest: Healing Herbs": {"duration": 7, "cost_gp": 0}, "Harvest: Poison": {"duration": 7, "cost_gp": 0}}},
    "Laboratory": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Craft: Alchemist's Supplies": {"duration": 7, "cost_gp": 25}, "Craft: Poison": {"duration": 7, "cost_gp": 50}}},
    "Sacristy": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Craft: Holy Water": {"duration": 7, "cost_gp": 25}, "Craft: Magic Item (Relic)": {"duration": 20, "cost_gp": 250}}},
    "Scriptorium": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Craft: Book Replica": {"duration": 7, "cost_gp": 10}, "Craft: Spell Scroll": {"duration": 5, "cost_gp": 100}, "Craft: Paperwork": {"duration": 7, "cost_gp": 50}}},
    "Stable": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Buy/Sell Animals": {"duration": 7, "cost_gp": 0}}, "enlarge_cost": {"Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Teleportation Circle": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Recruit: Spellcaster": {"duration": 7, "cost_gp": 0}}},
    "Theater": {"type": "Special", "level": 9, "size": "Vast", "orders": {"Stage Production": {"duration": 21, "cost_gp": 100}}},
    "Training Area": {"type": "Special", "level": 9, "size": "Vast", "orders": {"Train: Battle Expert": {"duration": 7, "cost_gp": 0}, "Train: Skills Expert": {"duration": 7, "cost_gp": 0}}},
    "Trophy Room": {"type": "Special", "level": 9, "size": "Roomy", "orders": {"Research: Lore": {"duration": 7, "cost_gp": 0}, "Research: Trinket Trophy": {"duration": 7, "cost_gp": 0}}},
    
    # --- Level 13 Special Facilities ---
    "Archive": {"type": "Special", "level": 13, "size": "Roomy", "orders": {"Research: Helpful Lore": {"duration": 7, "cost_gp": 0}}, "enlarge_cost": {"Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Meditation Chamber": {"type": "Special", "level": 13, "size": "Cramped", "orders": {"Empower: Inner Peace": {"duration": 7, "cost_gp": 0}}},
    "Menagerie": {"type": "Special", "level": 13, "size": "Vast", "orders": {"Recruit: Creature (Ape)": {"duration": 7, "cost_gp": 500}, "Recruit: Creature (Lion)": {"duration": 7, "cost_gp": 1000}}},
    "Observatory": {"type": "Special", "level": 13, "size": "Roomy", "orders": {"Empower: Eldritch Discovery": {"duration": 7, "cost_gp": 0}}},
    "Pub": {"type": "Special", "level": 13, "size": "Roomy", "orders": {"Research: Information Gathering": {"duration": 7, "cost_gp": 0}}, "enlarge_cost": {"Roomy to Vast": {"cost_gp": 2000, "time_days": 80}}},
    "Reliquary": {"type": "Special", "level": 13, "size": "Cramped", "orders": {"Harvest: Talisman": {"duration": 7, "cost_gp": 0}}},
    
    # --- Level 17 Special Facilities ---
    "Demiplane": {"type": "Special", "level": 17, "size": "Vast", "orders": {"Empower: Arcane Resilience": {"duration": 7, "cost_gp": 0}}},
    "Guildhall": {"type": "Special", "level": 17, "size": "Vast", "orders": {"Assign: Adventurers' Guild": {"duration": 7, "cost_gp": 100}, "Assign: Thieves' Guild": {"duration": 7, "cost_gp": 250}}},
    "Sanctum": {"type": "Special", "level": 17, "size": "Roomy", "orders": {"Empower: Fortifying Rites": {"duration": 7, "cost_gp": 0}}},
    "War Room": {"type": "Special", "level": 17, "size": "Vast", "orders": {"Recruit: Lieutenant": {"duration": 7, "cost_gp": 0}, "Recruit: Soldiers (100)": {"duration": 7, "cost_gp": 100}}},
}

# --- DATA FETCHING & STATE MANAGEMENT ---
@st.cache_data(ttl=60)
def load_data(campaign_id=1):
    """Loads all necessary data from Supabase for a given campaign."""
    if not supabase: return None
    try:
        campaign_response = supabase.table("campaigns").select("*").eq("id", campaign_id).execute()
        if not campaign_response.data:
            return None 
        campaign = campaign_response.data[0]

        characters = supabase.table("characters").select("*").eq("campaign_id", campaign_id).execute().data
        bastions_raw = supabase.table("bastions").select("*, characters(*)").eq("characters.campaign_id", campaign_id).execute().data
        
        bastion_ids = [b['id'] for b in bastions_raw]
        facilities = []
        if bastion_ids:
            facilities = supabase.table("facilities").select("*").in_("bastion_id", bastion_ids).execute().data
            
        log = supabase.table("bastion_log").select("*").eq("campaign_id", campaign_id).order("created_at", desc=True).limit(50).execute().data

        bastions = []
        for b_raw in bastions_raw:
            bastion = {
                "id": b_raw['id'],
                "character_id": b_raw['character_id'],
                "name": b_raw['name'],
                "defenders": b_raw['defenders'],
                "facilities": [f for f in facilities if f['bastion_id'] == b_raw['id']]
            }
            bastions.append(bastion)

        return {
            "campaign": campaign,
            "characters": characters,
            "bastions": bastions,
            "log": [f"Day {l['day_occurred']}: {l['entry_text']}" for l in log]
        }
    except Exception as e:
        st.error(f"An error occurred while fetching data from Supabase: {e}")
        return None

# --- HELPER FUNCTIONS ---
def send_to_discord(message):
    """Formats and sends a message to a Discord webhook."""
    webhook_url = st.secrets.get("discord", {}).get("webhook_url")
    if not webhook_url: return

    formatted_content = (
        "My noble masters, I write to you of happenings at your bastion:\n\n"
        f"{message}\n\n"
        "Never you fear for Mortimer is here."
    )
    data = {"content": formatted_content, "username": "Mortimer"}
    try:
        requests.post(webhook_url, json=data).raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Error sending message to Discord: {e}")

def add_log_entry(day, message, campaign_id=1):
    """Adds an entry to the in-app log, Supabase, and sends it to Discord."""
    full_log_message = f"Day {day}: {message}"
    # Immediately update the log in the session state for snappy UI
    if 'data' in st.session_state and st.session_state.data:
        st.session_state.data['log'].insert(0, full_log_message)
    send_to_discord(full_log_message)
    if supabase:
        try:
            supabase.table("bastion_log").insert({
                "campaign_id": campaign_id,
                "day_occurred": day,
                "entry_text": message
            }).execute()
        except Exception as e:
            st.warning(f"Could not save log to database: {e}")

def refresh_data():
    """Clears the data cache and reruns the app to force a fresh load from the DB."""
    st.cache_data.clear()
    st.rerun()

def get_log_style(log_entry):
    """Determines the CSS class for a log entry based on its content."""
    entry_lower = log_entry.lower()
    if any(keyword in entry_lower for keyword in ["attack", "lost", "criminal", "tense", "siege"]):
        return "log-entry-negative"
    if any(keyword in entry_lower for keyword in ["treasure", "acquired", "magical discovery"]):
        return "log-entry-positive"
    if any(keyword in entry_lower for keyword in ["completed", "enlarged"]):
        return "log-entry-complete"
    if any(keyword in entry_lower for keyword in ["began", "construction", "started", "vigilant"]):
        return "log-entry-progress"
    return "log-entry" # Default style

# --- UI: PROPRIETOR VIEW ---
def proprietor_view(data):
    st.title("✒️ Proprietor's Ledger")
    st.markdown("---")

    char_name = st.session_state.current_player
    character = next((c for c in data['characters'] if c['name'] == char_name), None)
    if not character or character['name'] == "DM":
        st.warning("Please select a valid character from the sidebar.")
        return

    if character['level'] < 5:
        st.warning(f"As a level {character['level']} adventurer, you have not yet earned the right to a Bastion. Return when you have attained the 5th level of experience.")
        return

    # Find the specific bastion object from the session state to modify it directly
    bastion_index, bastion = next(((i, b) for i, b in enumerate(data['bastions']) if b['character_id'] == character['id']), (None, None))
    if not bastion:
        st.error(f"No bastion found for {char_name}. Please ensure one is created in the Supabase table.")
        return

    st.header(f"{bastion['name']}")
    st.caption(f"Managed by {character['name']} | Level {character['level']} | Defenders: {bastion['defenders']}")

    st.subheader("Facilities & Orders")
    
    if st.button("Issue 'Maintain' Order (Triggers Bastion Event)"):
        roll = random.randint(1, 100)
        event_name = next((name for r, name in BASTION_EVENTS.items() if roll in r), "All Is Well")
        
        message = f"{bastion['name']} was maintained. Event: **{event_name}**."
        
        if event_name == "Attack":
            dice_rolls = [random.randint(1, 6) for _ in range(6)]
            losses = dice_rolls.count(1)
            new_defenders = max(0, bastion['defenders'] - losses)
            message += f" The bastion was attacked! It lost {losses} defenders. (Rolls: {dice_rolls})"
            # Update DB and session state
            supabase.table("bastions").update({"defenders": new_defenders}).eq("id", bastion['id']).execute()
            st.session_state.data['bastions'][bastion_index]['defenders'] = new_defenders
            
        st.success(f"Maintain order issued. Rolled {roll}: {event_name}!")
        add_log_entry(data['campaign']['current_day'], message)
        time.sleep(1)
        st.rerun() # Rerun with updated session state

    for fac_index, facility in enumerate(sorted(bastion['facilities'], key=lambda f: (f['type'], f['name']))):
        # Find the original index to update the session state correctly
        original_fac_index = next((i for i, f in enumerate(st.session_state.data['bastions'][bastion_index]['facilities']) if f['id'] == facility['id']), None)
        if original_fac_index is None: continue

        with st.container():
            cols = st.columns([2, 2, 1])
            is_busy = facility.get('status', 'Idle') != 'Idle'
            
            with cols[0]:
                st.markdown(f"**{facility['name']}** ({facility['type']})")
                if is_busy:
                    progress = facility['order_progress']
                    duration = facility['order_duration']
                    st.markdown(f"Status: <span style='color: #F7DC6F;'>{facility['status']}</span>", unsafe_allow_html=True)
                    st.progress(progress / duration if duration > 0 else 0, text=f"{progress}/{duration} Days")
                else:
                    st.markdown(f"Status: <span style='color: #82E0AA;'>Idle</span>", unsafe_allow_html=True)
                    st.markdown(f"Size: {facility.get('size', 'N/A')}")
            
            with cols[1]:
                if is_busy:
                    if st.button("Cancel Order", key=f"cancel_{facility['id']}"):
                        update_payload = {"status": "Idle", "order_progress": 0, "order_duration": 0}
                        supabase.table("facilities").update(update_payload).eq("id", facility['id']).execute()
                        add_log_entry(data['campaign']['current_day'], f"{char_name} cancelled the order '{facility['status']}' at the {facility['name']}.")
                        st.session_state.data['bastions'][bastion_index]['facilities'][original_fac_index].update(update_payload)
                        st.rerun()
                else: # Facility is Idle
                    if facility['type'] == 'Basic':
                        current_size = facility.get('size')
                        if current_size in ["Cramped", "Roomy"]:
                            upgrade_map = {"Cramped": "Roomy", "Roomy": "Vast"}
                            target_size = upgrade_map[current_size]
                            if st.button(f"Enlarge to {target_size}", key=f"enlarge_{facility['id']}"):
                                st.session_state.selected_facility_upgrade = facility['id']
                                st.rerun()

            with cols[2]:
                if not is_busy and facility['type'] == 'Special':
                    if st.button("Issue Order", key=f"order_{facility['id']}"):
                        st.session_state.selected_facility_order = facility['id']
                        st.rerun()

            # --- Modals for Orders and Upgrades ---
            if 'selected_facility_order' in st.session_state and st.session_state.selected_facility_order == facility['id']:
                with st.form(key=f"form_order_{facility['id']}"):
                    st.subheader(f"Issue Order: {facility['name']}")
                    rules = FACILITY_RULES.get(facility['name'], {})
                    order_choice = st.selectbox("Choose an order:", list(rules.get("orders", {}).keys()))
                    order_details = rules["orders"][order_choice]
                    st.caption(f"Duration: {order_details['duration']} days | Cost: {order_details['cost_gp']} GP")
                    
                    if st.form_submit_button("Confirm Order"):
                        update_payload = {"status": order_choice, "order_progress": 0, "order_duration": order_details['duration']}
                        supabase.table("facilities").update(update_payload).eq("id", facility['id']).execute()
                        add_log_entry(data['campaign']['current_day'], f"{char_name}'s {facility['name']} began the order: {order_choice}.")
                        st.session_state.data['bastions'][bastion_index]['facilities'][original_fac_index].update(update_payload)
                        del st.session_state.selected_facility_order
                        st.rerun()
                            
            if 'selected_facility_upgrade' in st.session_state and st.session_state.selected_facility_upgrade == facility['id']:
                with st.form(key=f"form_upgrade_{facility['id']}"):
                    current_size = facility.get('size')
                    target_size = {"Cramped": "Roomy", "Roomy": "Vast"}[current_size]
                    cost_info = FACILITY_RULES[facility['name']]['enlarge_cost'][f"{current_size} to {target_size}"]
                    
                    st.subheader(f"Enlarge {facility['name']} to {target_size}")
                    st.caption(f"Duration: {cost_info['time_days']} days | Cost: {cost_info['cost_gp']} GP")
                    
                    if st.form_submit_button("Confirm Enlargement"):
                        update_payload = {"status": f"Enlarging to {target_size}", "order_progress": 0, "order_duration": cost_info['time_days']}
                        supabase.table("facilities").update(update_payload).eq("id", facility['id']).execute()
                        add_log_entry(data['campaign']['current_day'], f"{char_name} has begun enlarging their {facility['name']} to {target_size}.")
                        st.session_state.data['bastions'][bastion_index]['facilities'][original_fac_index].update(update_payload)
                        del st.session_state.selected_facility_upgrade
                        st.rerun()

    st.markdown("---")
    
    # --- ENHANCEMENT: Tabbed interface for development ---
    dev_tab1, dev_tab2 = st.tabs(["Acquire Facilities", "Personnel"])

    with dev_tab1:
        st.subheader("Construction & Acquisition")
        # Special Facilities
        num_special_facilities = len([f for f in bastion['facilities'] if f['type'] == 'Special'])
        max_special_facilities = 0
        for level_req in sorted(SPECIAL_FACILITY_ACQUISITION.keys()):
            if character['level'] >= level_req:
                max_special_facilities = SPECIAL_FACILITY_ACQUISITION[level_req]

        st.markdown(f"**Special Facilities:** {num_special_facilities} / {max_special_facilities} owned.")
        if num_special_facilities < max_special_facilities:
            owned_names = [f['name'] for f in bastion['facilities']]
            available_special = [name for name, rules in FACILITY_RULES.items() if rules['type'] == 'Special' and name not in owned_names and character['level'] >= rules['level']]
            
            if available_special:
                new_special = st.selectbox("Choose a new Special Facility to acquire:", available_special, key="new_special_facility")
                if st.button(f"Acquire {new_special} (Free with level up)"):
                    facility_size = FACILITY_RULES.get(new_special, {}).get('size', 'Roomy')
                    insert_payload = {
                        "bastion_id": bastion['id'], "name": new_special, "type": "Special",
                        "status": "Idle", "size": facility_size, "order_progress": 0, "order_duration": 0
                    }
                    response = supabase.table("facilities").insert(insert_payload).execute()
                    new_facility_record = response.data[0]
                    
                    add_log_entry(data['campaign']['current_day'], f"{char_name} has acquired a new facility: {new_special}!")
                    st.success(f"{new_special} has been added to your bastion!")
                    st.session_state.data['bastions'][bastion_index]['facilities'].append(new_facility_record)
                    time.sleep(1)
                    st.rerun()

        # Basic Facilities
        st.markdown("**Basic Facilities:**")
        new_basic_name = st.selectbox("Choose a Basic Facility to build:", [name for name, rules in FACILITY_RULES.items() if rules['type'] == 'Basic'], key="new_basic_facility")
        new_basic_size = st.selectbox("Choose size:", ["Cramped", "Roomy", "Vast"], key="new_basic_size")
        cost_info = FACILITY_RULES[new_basic_name]['add_cost'][new_basic_size]
        
        if st.button(f"Build {new_basic_name} ({new_basic_size})"):
            insert_payload = {
                "bastion_id": bastion['id'], "name": new_basic_name, "type": "Basic", "size": new_basic_size,
                "status": f"Under Construction", "order_progress": 0, "order_duration": cost_info['time_days']
            }
            response = supabase.table("facilities").insert(insert_payload).execute()
            new_facility_record = response.data[0]

            add_log_entry(data['campaign']['current_day'], f"{char_name} has begun construction on a new {new_basic_name} ({new_basic_size}).")
            st.success(f"Construction order for {new_basic_name} has been issued!")
            st.session_state.data['bastions'][bastion_index]['facilities'].append(new_facility_record)
            time.sleep(1)
            st.rerun()

    with dev_tab2:
        st.subheader("Defenders & Hirelings")
        st.markdown(f"You currently have **{bastion['defenders']}** Bastion Defenders.")
        st.markdown("Recruit more defenders by issuing orders at a Barrack.")

# --- UI: COMMUNAL VIEW ---
def communal_view(data):
    st.title("🏰 The Bastion's Hearth")
    st.markdown("---")
    
    total_defenders = sum(b['defenders'] for b in data['bastions'])
    total_facilities = sum(len(b['facilities']) for b in data['bastions'])
    active_facilities = sum(1 for b in data['bastions'] for f in b['facilities'] if f.get('status', 'Idle') != 'Idle')
    productivity = (active_facilities / total_facilities * 100) if total_facilities > 0 else 0
    threat_level = data['campaign'].get('threat_level', 'Peaceful')

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(label="Campaign Name", value=data['campaign']['campaign_name'])
    col2.metric(label="Current In-Game Day", value=data['campaign']['current_day'])
    col3.metric(label="Total Bastion Defenders", value=total_defenders)
    col4.metric(label="Bastion Productivity", value=f"{productivity:.0f}%")
    col5.metric(label="Threat Level", value=threat_level)

    st.markdown("---")
    
    st.subheader("Party Bastion Roster")
    num_bastions = len(data['bastions'])
    if num_bastions == 0:
        st.info("No bastions established yet.")
    else:
        cols = st.columns(min(num_bastions, 4)) 
        for i, bastion in enumerate(data['bastions']):
            with cols[i % min(num_bastions, 4)]:
                with st.container():
                    owner = next((c for c in data['characters'] if c['id'] == bastion['character_id']), None)
                    st.markdown(f"""
                    <div class="bastion-card">
                        <h4>{bastion['name']}</h4>
                        <p><b>Proprietor:</b> {owner['name'] if owner else 'Unknown'}</p>
                        <p><b>Defenders:</b> {bastion['defenders']}</p>
                    </div>
                    """, unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Mortimer's Log")
    log_container = st.container(height=300)
    with log_container:
        if not data['log']:
            st.markdown("<p class='log-entry'>The log is presently empty, sir.</p>", unsafe_allow_html=True)
        for log_entry in data['log']:
            style_class = get_log_style(log_entry)
            st.markdown(f"<div class='log-entry {style_class}'>{log_entry}</div>", unsafe_allow_html=True)

# --- UI: DM VIEW ---
def dm_view(data):
    st.title("👑 The Architect's Sanctum")
    st.markdown("---")
    
    st.header("Master Control Panel")
    with st.expander("View All Bastion Details"):
        for bastion in data['bastions']:
            owner = next((c for c in data['characters'] if c['id'] == bastion['character_id']), None)
            st.subheader(f"{bastion['name']} (Proprietor: {owner['name'] if owner else 'N/A'})")
            st.text(f"Defenders: {bastion['defenders']}")
            
            active_orders = [f for f in bastion['facilities'] if f.get('status', 'Idle') != 'Idle']
            if not active_orders:
                st.text("All facilities are idle.")
            else:
                for facility in active_orders:
                    st.text(f"- {facility['name']}: {facility['status']} ({facility['order_progress']}/{facility['order_duration']} days)")
            st.markdown("---")

    st.header("Campaign Time Management")
    campaign = data['campaign']
    current_day = campaign['current_day']
    st.metric("Current In-Game Day", current_day)
    
    with st.form("time_advance_form"):
        days_to_advance = st.number_input("Days to Advance:", min_value=1, step=1, value=7)
        submitted = st.form_submit_button("Advance Time")
        
        if submitted:
            with st.spinner(f"Advancing time by {days_to_advance} days..."):
                for day_offset in range(1, days_to_advance + 1):
                    day_in_progress = current_day + day_offset
                    for bastion_index, bastion in enumerate(data['bastions']):
                        for fac_index, facility in enumerate(bastion['facilities']):
                            if facility.get('status', 'Idle') == 'Idle': continue
                            new_progress = facility['order_progress'] + 1
                            if new_progress >= facility['order_duration']:
                                completed_order = facility['status']
                                owner = next(c for c in data['characters'] if c['id'] == bastion['character_id'])
                                update_payload = {"status": "Idle", "order_progress": 0, "order_duration": 0}
                                log_message = ""
                                if completed_order.startswith("Enlarging to "):
                                    target_size = completed_order.split(" ")[-1]
                                    update_payload['size'] = target_size
                                    log_message = f"{owner['name']}'s {facility['name']} has been enlarged to {target_size}."
                                elif completed_order == "Under Construction":
                                    log_message = f"{owner['name']}'s new {facility['name']} has been completed."
                                else:
                                    log_message = f"{owner['name']}'s {facility['name']} has completed the order: {completed_order}."
                                supabase.table("facilities").update(update_payload).eq("id", facility['id']).execute()
                                add_log_entry(day_in_progress, log_message)
                                st.session_state.data['bastions'][bastion_index]['facilities'][fac_index].update(update_payload)
                            else:
                                supabase.table("facilities").update({"order_progress": new_progress}).eq("id", facility['id']).execute()
                                st.session_state.data['bastions'][bastion_index]['facilities'][fac_index]['order_progress'] = new_progress
                new_day = current_day + days_to_advance
                supabase.table("campaigns").update({"current_day": new_day}).eq("id", campaign['id']).execute()
                st.session_state.data['campaign']['current_day'] = new_day
            st.success(f"Time advanced by {days_to_advance} days. New day is {new_day}.")
            time.sleep(1) 
            st.cache_data.clear()
            st.rerun()

    st.header("Narrative Tools")
    
    st.subheader("Set Campaign Threat Level")
    threat_levels = ["Peaceful", "Vigilant", "Tense", "Under Siege"]
    current_threat = campaign.get('threat_level', 'Peaceful')
    
    if current_threat not in threat_levels:
        current_threat = "Peaceful" 
        
    current_threat_index = threat_levels.index(current_threat)
    selected_threat = st.selectbox("Select Threat Level:", threat_levels, index=current_threat_index)
    
    if st.button("Update Threat Level"):
        supabase.table("campaigns").update({"threat_level": selected_threat}).eq("id", campaign['id']).execute()
        st.session_state.data['campaign']['threat_level'] = selected_threat
        # --- FINAL ENHANCEMENT ---
        add_log_entry(current_day, f"Mortimer notes a change in the regional disposition. The threat level is now considered '{selected_threat}'.")
        st.success(f"Threat level updated to {selected_threat}.")
        time.sleep(1)
        st.rerun()

    st.subheader("Inject Bastion Event")
    bastion_names = {b['id']: b['name'] for b in data['bastions']}
    if bastion_names: # Only show if there are bastions to target
        target_bastion_id = st.selectbox("Target Bastion:", options=list(bastion_names.keys()), format_func=lambda x: bastion_names[x])
        event_to_inject = st.selectbox("Event to Trigger:", options=[name for r, name in BASTION_EVENTS.items()])
        if st.button("Trigger Event"):
            message = f"A special event occurred at {bastion_names[target_bastion_id]}: **{event_to_inject}**."
            add_log_entry(current_day, message)
            st.success(f"Injected '{event_to_inject}' event for {bastion_names[target_bastion_id]}.")
            time.sleep(1)
            st.rerun()


# --- MAIN APP ROUTER ---
def main():
    """Main function to run the Streamlit app."""
    if 'data' not in st.session_state or st.session_state.data is None:
        with st.spinner("Summoning Mortimer from the archives..."):
            st.session_state.data = load_data()

    if not supabase:
        st.error("Application could not initialize. Please check Supabase connection.")
        return
        
    if not st.session_state.data:
        st.warning("No campaign data found. Please ensure a campaign with ID 1 exists in your Supabase 'campaigns' table and that you have populated the other tables correctly.")
        st.info("Follow the data population guide to set up your first campaign.")
        return

    data = st.session_state.data
    
    st.sidebar.title("Navigation")
    st.sidebar.markdown("---")
    
    player_list = [char['name'] for char in data['characters']]
    if 'current_player' not in st.session_state or st.session_state.current_player not in player_list:
        st.session_state.current_player = player_list[0] if player_list else None
    
    if st.session_state.current_player:
        try:
            current_index = player_list.index(st.session_state.current_player)
        except ValueError:
            current_index = 0 

        selected_player = st.sidebar.selectbox("Select Your Character:", options=player_list, index=current_index)
        if st.session_state.current_player != selected_player:
            st.session_state.current_player = selected_player
            # Clear modals if player switches
            if 'selected_facility_order' in st.session_state: del st.session_state.selected_facility_order
            if 'selected_facility_upgrade' in st.session_state: del st.session_state.selected_facility_upgrade
            st.rerun()

        if selected_player == "DM":
            view = "DM View"
        else:
            view = st.sidebar.radio("Select View", ("Communal View", "Proprietor's View"), label_visibility="collapsed")

        st.sidebar.markdown("---")
        st.sidebar.info("This app helps manage D&D 5e Bastions, as per the 2024 Player's Handbook rules.")

        if view == "Communal View":
            communal_view(data)
        elif view == "Proprietor's View":
            proprietor_view(data)
        elif view == "DM View":
            dm_view(data)

if __name__ == "__main__":
    main()
