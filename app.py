import streamlit as st
from core.state import init_state
from core.storage import load_settings, load_events
from core.auth import ensure_login, get_current_user_role, get_trainer_name, refresh_session_passwords
from pages.admin import admin_page
from pages.viewer import viewer_page
from pages.trainer import trainer_page
from core.config import EXCEL_FILE

st.set_page_config(page_title="EQS Event Scheduling", layout="wide")

# --- Hide Streamlit multipage navigation (app/admin/trainer/viewer list) ---
st.markdown(
    """
    <style>
    /* Hides the 'Pages' / navigation area in Streamlit sidebar */
    [data-testid="stSidebarNav"] { display: none !important; }

    /* If Streamlit changes testid, this also catches the nav block */
    section[data-testid="stSidebar"] div:has(> ul[role="list"]) { display:none !important; }
    </style>
    """,
    unsafe_allow_html=True
)


# --- Hide Streamlit sidebar toggle + extra chrome ---
st.markdown(
    """
    <style>
    [data-testid="collapsedControl"] { display: none !important; }
    header[data-testid="stHeader"] { height: 0rem; }
    header[data-testid="stHeader"] > div { display: none; }
    .block-container { padding-top: 1.5rem; }
    </style>
    """,
    unsafe_allow_html=True
)

init_state()

users_df, trainers_df, lists_df, rules_df, defaults_df, notif_df = load_settings()

AUTHORIZED_EMAILS = users_df[users_df["Active"]==True]["Email"].str.lower().tolist()

def refresh_pw_cb():
    global users_df
    users_df, _, _, _, _, _ = load_settings()  # Reload users from file
    refresh_session_passwords(users_df)

user_email = ensure_login(AUTHORIZED_EMAILS, users_df)
role = get_current_user_role(users_df, user_email)

# sidebar logout
with st.sidebar:
    st.write(f"👤 Logged in as: **{user_email}**")
    if st.button("🚪 Logout"):
        st.session_state.authenticated = False
        st.session_state.user_email = None
        st.rerun()

# load live data + settings
df = load_events()
TRAINERS = trainers_df[trainers_df["Active"]==True]["Name"].tolist()
TRAINER_COLORS = {r["Name"]: r["Color"] for _, r in trainers_df.iterrows() if r["Active"]==True}

def get_list(category, fallback):
    sub = lists_df[(lists_df["Category"]==category) & (lists_df["Active"]==True)]
    return sub["Value"].tolist() if len(sub) else fallback

LOCATIONS = get_list("Locations", ["Syd","Mel","Bne","SG","Msia","Global"])
SOURCES = ["All"] + get_list("Sources", ["EQS","CCE","CTD"])
STATUSES = ["All"] + get_list("Statuses", ["Offered","Tentative","Confirmed"])
MEDIUMS = get_list("Mediums", ["F2F","Online"])
TYPES = get_list("Types", ["W","C","M"])

def get_rule(key, default=False):
    row = rules_df[rules_df["Key"]==key]
    if len(row)==0: return default
    val = row.iloc[0]["Value"]
    if isinstance(val, bool): return val
    return str(val).lower()=="true"

RULE_ONLY_ADMIN_CAN_BLOCK = get_rule("only_admin_can_block", True)
RULE_BLOCK_PREVENT_DUPLICATES = get_rule("blocked_prevents_duplicates", True)

def get_default(key, fallback=""):
    row = defaults_df[defaults_df["Key"]==key]
    return row.iloc[0]["Value"] if len(row) else fallback

DEFAULT_STATUS = get_default("default_status", "Offered")
DEFAULT_MEDIUM = get_default("default_medium", "Online")
DEFAULT_SOURCE = get_default("default_source", "EQS")
DEFAULT_LOCATION = get_default("default_location", "Global")
DEFAULT_TYPE = get_default("default_type", "W")

st.title("🗓️ EQS Event Scheduling")
st.markdown("---")

if role == "admin":
    settings_tuple = (
        TRAINERS, TRAINER_COLORS, TYPES, STATUSES, SOURCES, MEDIUMS, LOCATIONS,
        DEFAULT_TYPE, DEFAULT_STATUS, DEFAULT_SOURCE, DEFAULT_MEDIUM, DEFAULT_LOCATION,
        RULE_ONLY_ADMIN_CAN_BLOCK, RULE_BLOCK_PREVENT_DUPLICATES,
        users_df, trainers_df, lists_df, rules_df, defaults_df, notif_df, EXCEL_FILE, refresh_pw_cb
    )
    df = admin_page(df, user_email, settings_tuple)
elif role == "view_only":
    df = viewer_page(df, user_email, {"TRAINERS": TRAINERS, "TRAINER_COLORS": TRAINER_COLORS})
elif role == "trainer":
    trainer_name = get_trainer_name(users_df, user_email)
    df = trainer_page(df, user_email, {"TRAINERS": TRAINERS, "TRAINER_COLORS": TRAINER_COLORS, "trainer_name": trainer_name})
else:
    st.error("Unauthorized role.")
