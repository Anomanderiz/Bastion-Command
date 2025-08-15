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
    "Arcane Study": {"type": "Special", "level": 5, "orders": {"Craft: Arcane Focus": {"duration": 7, "cost_gp": 0}, "Craft: Book": {"duration": 7, "cost_gp": 10}, "Craft: Magic Item (Arcana)": {"duration": 20, "cost_gp": 250}}},
    "Armory": {"type": "Special", "level": 5, "orders": {"Stock Armory": {"duration": 7, "cost_gp": 100}}},
    "Barrack": {"type": "Special", "level": 5, "orders": {"Recruit: Bastion Defenders (4)": {"duration": 7, "cost_gp": 0}}},
    "Garden": {"type": "Special", "level": 5, "orders": {"Harvest: Decorative": {"duration": 7, "cost_gp": 0}, "Harvest: Food": {"duration": 7, "cost_gp": 0}, "Harvest: Herb": {"duration": 7, "cost_gp": 0}, "Harvest: Poison": {"duration": 7, "cost_gp": 0}}},
    "Library": {"type": "Special", "level": 5, "orders": {"Research: Topical Lore": {"duration": 7, "cost_gp": 0}}},
    "Sanctuary": {"type": "Special", "level": 5, "orders": {"Craft: Sacred Focus": {"duration": 7, "cost_gp": 0}}},
    "Smithy": {"type": "Special", "level": 5, "orders": {"Craft: Smith's Tools Item": {"duration": 14, "cost_gp": 50}, "Craft: Magic Item (Armament)": {"duration": 20, "cost_gp": 250}}},
    "Storehouse": {"type": "Special", "level": 5, "orders": {"Procure Goods (500 GP)": {"duration": 7, "cost_gp": 500}, "Sell Goods": {"duration": 7, "cost_gp": 0}}},
    "Workshop": {"type": "Special", "level": 5, "orders": {"Craft: Adventuring Gear": {"duration": 10, "cost_gp": 25}, "Craft: Magic Item (Implement)": {"duration": 20, "cost_gp": 250}}},

    # --- Level 9 Special Facilities ---
    "Gaming Hall": {"type": "Special", "level": 9, "orders": {"Run Gambling Hall": {"duration": 7, "cost_gp": 0}}},
    "Greenhouse": {"type": "Special", "level": 9, "orders": {"Harvest: Healing Herbs": {"duration": 7, "cost_gp": 0}, "Harvest: Poison": {"duration": 7, "cost_gp": 0}}},
    "Laboratory": {"type": "Special", "level": 9, "orders": {"Craft: Alchemist's Supplies": {"duration": 7, "cost_gp": 25}, "Craft: Poison": {"duration": 7, "cost_gp": 50}}},
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
    "War Room": {"type": "Special", "level": 17, "orders": {"Recruit: Lieutenant": {"duration": 7, "cost_gp": 0}, "Recruit: Soldiers (100)": {"duration": 7, "cost_gp": 100}}},
}

# --- DATA FETCHING & STATE MANAGEMENT ---
@st.cache_data(ttl=60) # Cache data for 60 seconds
def load_data(campaign_id=1):
    """Loads all necessary data from Supabase for a given campaign."""
    if not supabase: return None
    try:
        campaign = supabase.table("campaigns").select("*").eq("id", campaign_id).single().execute().data
        characters = supabase.table("characters").select("*").eq("campaign_id", campaign_id).execute().data
        bastions_raw = supabase.table("bastions").select("*, characters(*)").eq("characters.campaign_id", campaign_id).execute().data
        
        bastion_ids = [b['id'] for b in bastions_raw]
        facilities = supabase.table("facilities").select("*").in_("bastion_id", bastion_ids).execute().data
        log = supabase.table("bastion_log").select("*").eq("campaign_id", campaign_id).order("created_at", desc=True).limit(20).execute().data

        # Structure the data similarly to the old mock data for compatibility
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

if 'data' not in st.session_state:
    st.session_state.data = load_data()

if 'current_player' not in st.session_state and st.session_state.data:
    st.session_state.current_player = st.session_state.data['characters'][0]['name'] if st.session_state.data['characters'] else None

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
    st.session_state.data['log'].insert(0, full_log_message)
    send_to_discord(full_log_message)
    # Write to Supabase
    if supabase:
        try:
            supabase.table("bastion_log").insert({
                "campaign_id": campaign_id,
                "day_occurred": day,
                "entry_text": message
            }).execute()
        except Exception as e:
            st.warning(f"Could not save log to database: {e}")

# --- UI: PROPRIETOR VIEW ---
def proprietor_view():
    st.title("✒️ Proprietor's Ledger")
    st.markdown("---")

    char_name = st.session_state.current_player
    character = next((c for c in st.session_state.data['characters'] if c['name'] == char_name), None)
    if not character or character['name'] == "DM":
        st.warning("Please select a valid character from the sidebar.")
        return

    bastion = next((b for b in st.session_state.data['bastions'] if b['character_id'] == character['id']), None)
    if not bastion:
        st.error(f"No bastion found for {char_name}.")
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
            supabase.table("bastions").update({"defenders": new_defenders}).eq("id", bastion['id']).execute()
            bastion['defenders'] = new_defenders # Update state
            
        st.success(f"Maintain order issued. Rolled {roll}: {event_name}!")
        add_log_entry(st.session_state.data['campaign']['current_day'], message)
        time.sleep(2)
        st.rerun()

    for facility in bastion['facilities']:
        with st.container():
            cols = st.columns([2, 2, 1])
            cols[0].markdown(f"**{facility['name']}** ({facility['type']})")
            if facility['type'] == 'Special':
                if facility['status'] == 'Idle':
                    cols[0].markdown(f"Status: <span style='color: #82E0AA;'>Idle</span>", unsafe_allow_html=True)
                else:
                    progress = facility['order_progress']
                    duration = facility['order_duration']
                    cols[0].markdown(f"Status: <span style='color: #F7DC6F;'>{facility['status']}</span>", unsafe_allow_html=True)
                    cols[0].progress(progress / duration if duration > 0 else 0, text=f"{progress}/{duration} Days")
                
                if facility['status'] != 'Idle':
                    if cols[1].button("Cancel Order", key=f"cancel_{facility['id']}"):
                        supabase.table("facilities").update({"status": "Idle", "order_progress": 0, "order_duration": 0}).eq("id", facility['id']).execute()
                        add_log_entry(st.session_state.data['campaign']['current_day'], f"{char_name} cancelled the order '{facility['status']}' at the {facility['name']}.")
                        st.rerun()
                else:
                    if cols[2].button("Issue Order", key=f"order_{facility['id']}"):
                        st.session_state.selected_facility = facility['id']
            else:
                cols[0].markdown(f"Size: {facility.get('size', 'N/A')}")

            if 'selected_facility' in st.session_state and st.session_state.selected_facility == facility['id']:
                with st.form(key=f"form_{facility['id']}"):
                    st.subheader(f"Issue Order: {facility['name']}")
                    rules = FACILITY_RULES.get(facility['name'], {})
                    order_choice = st.selectbox("Choose an order:", list(rules.get("orders", {}).keys()))
                    if order_choice:
                        order_details = rules["orders"][order_choice]
                        st.caption(f"Duration: {order_details['duration']} days | Cost: {order_details['cost_gp']} GP")
                        if st.form_submit_button("Confirm Order"):
                            supabase.table("facilities").update({
                                "status": order_choice, 
                                "order_progress": 0, 
                                "order_duration": order_details['duration']
                            }).eq("id", facility['id']).execute()
                            add_log_entry(st.session_state.data['campaign']['current_day'], f"{char_name}'s {facility['name']} began the order: {order_choice}.")
                            del st.session_state.selected_facility
                            st.rerun()

    st.markdown("---")
    st.subheader("Acquire New Facilities")
    # (Acquisition logic remains the same, but would need Supabase INSERTs)

# --- UI: COMMUNAL VIEW ---
def communal_view():
    st.title("🏰 The Bastion's Hearth")
    st.markdown("---")
    if not st.session_state.data:
        st.warning("Could not load campaign data.")
        return
        
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
    
    campaign = st.session_state.data['campaign']
    current_day = campaign['current_day']
    st.metric("Current In-Game Day", current_day)
    
    with st.form("time_advance_form"):
        days_to_advance = st.number_input("Days to Advance:", min_value=1, step=1, value=7)
        submitted = st.form_submit_button("Advance Time")
        if submitted:
            new_day = current_day + days_to_advance
            
            # Update all active orders
            for bastion in st.session_state.data['bastions']:
                for facility in bastion['facilities']:
                    if facility.get('type') == 'Special' and facility.get('status') != 'Idle':
                        new_progress = facility['order_progress'] + days_to_advance
                        if new_progress >= facility['order_duration']:
                            # Order complete
                            supabase.table("facilities").update({"status": "Idle", "order_progress": 0, "order_duration": 0}).eq("id", facility['id']).execute()
                            owner = next(c for c in st.session_state.data['characters'] if c['id'] == bastion['character_id'])
                            add_log_entry(new_day, f"{owner['name']}'s {facility['name']} has completed the order: {facility['status']}.")
                        else:
                            # Order in progress
                            supabase.table("facilities").update({"order_progress": new_progress}).eq("id", facility['id']).execute()

            # Update campaign day
            supabase.table("campaigns").update({"current_day": new_day}).eq("id", campaign['id']).execute()
            
            st.success(f"Time advanced by {days_to_advance} days. New day is {new_day}.")
            time.sleep(1)
            st.rerun()

# --- MAIN APP ROUTER ---
if not supabase or not st.session_state.data:
    st.error("Application could not initialize. Please check Supabase connection and configuration.")
else:
    st.sidebar.title("Navigation")
    st.sidebar.markdown("---")
    
    player_list = [char['name'] for char in st.session_state.data['characters']]
    if st.session_state.current_player not in player_list:
        st.session_state.current_player = player_list[0] if player_list else None
    
    selected_player = st.sidebar.selectbox("Select Your Character:", options=player_list, index=player_list.index(st.session_state.current_player))
    st.session_state.current_player = selected_player

    if selected_player == "DM":
        view = "DM View"
    else:
        view = st.sidebar.radio("Select View", ("Communal View", "Proprietor's View"), label_visibility="hidden")

    st.sidebar.markdown("---")
    st.sidebar.info("This app helps manage D&D 5e Bastions.")

    if view == "Communal View":
        communal_view()
    elif view == "Proprietor's View":
        proprietor_view()
    elif view == "DM View":
        dm_view()
