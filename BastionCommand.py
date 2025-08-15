import streamlit as st
import pandas as pd
# from supabase import create_client, Client  # Uncomment when ready to connect to Supabase
import time
import json

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
        .stMarkdown, p, .stButton > button, .stSelectbox > div > div {
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
# Replace with your actual Supabase credentials
# SUPABASE_URL = st.secrets["supabase_url"]
# SUPABASE_KEY = st.secrets["supabase_key"]
# supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- MOCK DATA (to be replaced by Supabase calls) ---
# This data simulates what you would pull from your database.
# It's structured to be easily convertible to Supabase tables.

def get_mock_data():
    return {
        "campaign": {
            "campaign_name": "The Crimson Crown",
            "current_day": 127,
        },
        "characters": [
            {"id": 1, "name": "Elara Meadowlight", "level": 9},
            {"id": 2, "name": "Kaelen Shadowhand", "level": 9},
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
                    {"id": 6, "name": "Gaming Hall", "type": "Special", "status": "Running Gambling Hall", "order_progress": 6, "order_duration": 7},
                    {"id": 7, "name": "Pub", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 8, "name": "Storehouse", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 9, "name": "Workshop", "type": "Special", "status": "Idle", "order_progress": 0, "order_duration": 0},
                    {"id": 10, "name": "Kitchen", "type": "Basic", "size": "Cramped"},
                ]
            }
        ],
        "log": [
            "Day 126: Kaelen's Gaming Hall reported winnings of 120 GP.",
            "Day 123: Elara's Smithy began work on a +1 Longsword.",
            "Day 120: A request for aid was received from Oakhaven. All defenders returned safely.",
        ]
    }

# --- BASTION RULES ENGINE (Data from PDF) ---
# A comprehensive dictionary holding the rules for facilities and orders.
# This makes the app modular and easy to update.
FACILITY_RULES = {
    "Arcane Study": {
        "level": 5, "prerequisite": "Arcane Focus User", "space": "Roomy",
        "orders": {
            "Craft: Arcane Focus": {"duration": 7, "cost_gp": 0},
            "Craft: Book": {"duration": 7, "cost_gp": 10},
            "Craft: Magic Item (Arcana)": {"duration": "Varies", "cost_gp": "Varies"},
        }
    },
    "Smithy": {
        "level": 5, "prerequisite": "None", "space": "Roomy",
        "orders": {
            "Craft: Smith's Tools Item": {"duration": "Varies", "cost_gp": "Varies"},
            "Craft: Magic Item (Armament)": {"duration": "Varies", "cost_gp": "Varies"},
        }
    },
    "Barrack": {
        "level": 5, "prerequisite": "None", "space": "Roomy",
        "orders": {
            "Recruit: Bastion Defenders (4)": {"duration": 7, "cost_gp": 0},
        }
    },
    "Gaming Hall": {
        "level": 9, "prerequisite": "None", "space": "Vast",
        "orders": {
            "Run Gambling Hall": {"duration": 7, "cost_gp": 0, "details": "Roll 1d100 for winnings at the end."},
        }
    },
    # Add all other facilities from the PDF here...
}


# --- STATE MANAGEMENT ---
if 'data' not in st.session_state:
    st.session_state.data = get_mock_data()
if 'current_player' not in st.session_state:
    st.session_state.current_player = "Elara Meadowlight"


# --- HELPER FUNCTIONS ---
def get_character_by_name(name):
    """Fetches a character's data dictionary by their name."""
    for char in st.session_state.data['characters']:
        if char['name'] == name:
            return char
    return None

def get_bastion_by_char_id(char_id):
    """Fetches a bastion's data dictionary by character ID."""
    for bastion in st.session_state.data['bastions']:
        if bastion['character_id'] == char_id:
            return bastion
    return None

# --- UI COMPONENTS ---
def communal_view():
    """Renders the main dashboard visible to all players."""
    st.title("🏰 The Bastion's Hearth")
    st.markdown("---")

    data = st.session_state.data
    total_defenders = sum(b['defenders'] for b in data['bastions'])
    campaign_name = data['campaign']['campaign_name']
    current_day = data['campaign']['current_day']

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(label="Campaign Name", value=campaign_name)
    with col2:
        st.metric(label="Current In-Game Day", value=current_day)
    with col3:
        st.metric(label="Total Bastion Defenders", value=total_defenders)

    st.markdown("---")
    st.subheader("Recent Bastion Activity")

    with st.container():
        for log_entry in data['log']:
            st.markdown(f"> {log_entry}")

def proprietor_view():
    """Renders the detailed management view for a single player."""
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
    st.caption(f"Managed by {character['name']} | Level {character['level']}")

    st.subheader("Facilities & Orders")
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

            # --- Order Modal Logic ---
            if 'selected_facility' in st.session_state and st.session_state.selected_facility == facility['id']:
                with st.form(key=f"form_{facility['id']}"):
                    st.subheader(f"Issue Order: {facility['name']}")
                    rules = FACILITY_RULES.get(facility['name'], {})
                    available_orders = list(rules.get("orders", {}).keys())

                    if not available_orders:
                        st.warning("No specific orders are defined for this facility in the rules engine.")
                        submitted = st.form_submit_button("Cancel")
                        if submitted:
                            del st.session_state.selected_facility
                            st.rerun()

                    else:
                        order_choice = st.selectbox("Choose an order:", available_orders)
                        
                        # Mock inputs for variable orders
                        if "Varies" in str(rules["orders"][order_choice]["duration"]):
                            duration_input = st.number_input("Enter Order Duration (Days):", min_value=1, value=7)
                        if "Varies" in str(rules["orders"][order_choice]["cost_gp"]):
                            cost_input = st.number_input("Enter Order Cost (GP):", min_value=0, value=50)

                        submitted = st.form_submit_button("Confirm Order")
                        if submitted:
                            # In a real app, this would be a call to Supabase to update the facility record
                            st.success(f"Order '{order_choice}' issued to {facility['name']}!")
                            facility['status'] = order_choice
                            facility['order_progress'] = 0
                            facility['order_duration'] = rules["orders"][order_choice]["duration"]
                            if "Varies" in str(facility['order_duration']):
                                facility['order_duration'] = duration_input
                            
                            # Update log
                            st.session_state.data['log'].insert(0, f"Day {st.session_state.data['campaign']['current_day']}: {char_name}'s {facility['name']} began the order: {order_choice}.")

                            del st.session_state.selected_facility
                            time.sleep(1) # Give user time to see success message
                            st.rerun()

def dm_view():
    """Renders the Dungeon Master's control panel."""
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
            
            # --- CORE TIME ADVANCEMENT LOGIC ---
            # In a real app, you'd update the campaign day and then loop through all
            # active orders in Supabase, incrementing their progress.
            st.session_state.data['campaign']['current_day'] = new_day

            for bastion in st.session_state.data['bastions']:
                for facility in bastion['facilities']:
                    if facility['status'] != 'Idle':
                        facility['order_progress'] += days_to_advance
                        if facility['order_progress'] >= facility['order_duration']:
                            # Order is complete
                            completed_order = facility['status']
                            facility['status'] = 'Idle'
                            facility['order_progress'] = 0
                            facility['order_duration'] = 0
                            
                            owner_name = [c['name'] for c in st.session_state.data['characters'] if c['id'] == bastion['character_id']][0]
                            
                            log_message = f"Day {new_day}: {owner_name}'s {facility['name']} has completed the order: {completed_order}."
                            st.session_state.data['log'].insert(0, log_message)
            
            st.success(f"Time advanced by {days_to_advance} days. The new day is {new_day}.")
            st.info("Bastion orders have been updated. Check the log for completed tasks.")
            time.sleep(2)
            st.rerun()

# --- MAIN APP ROUTER ---
st.sidebar.title("Navigation")
st.sidebar.markdown("---")

# Player selection in the sidebar
player_list = [char['name'] for char in st.session_state.data['characters']]
selected_player = st.sidebar.selectbox(
    "Select Your Character:",
    options=player_list,
    index=player_list.index(st.session_state.current_player)
)
st.session_state.current_player = selected_player


# View selection based on player
if selected_player == "DM":
    view = "DM View"
else:
    view = st.sidebar.radio(
        "Select View",
        ("Communal View", "Proprietor's View"),
        label_visibility="hidden"
    )

st.sidebar.markdown("---")
st.sidebar.info("This app helps manage D&D 5e Bastions. All data is currently mocked and will reset on refresh.")


# Display the selected view
if view == "Communal View":
    communal_view()
elif view == "Proprietor's View":
    proprietor_view()
elif view == "DM View":
    dm_view()
