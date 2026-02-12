"""
Fashion Wardrobe Manager - Main App
Modular Streamlit application with separate pages
"""

import streamlit as st
from streamlit_option_menu import option_menu

# Import configuration
from config import APP_TITLE, APP_ICON, BACKEND_URL
from api_client import BackendAPIClient

# Import page modules
from app_pages.auth import show_auth_page
from app_pages.dashboard import show_dashboard
from app_pages.wardrobe import show_wardrobe
from app_pages.outfits import show_outfits
from app_pages.settings import show_settings
from app_pages.edit_item import show_edit_item


# ============================================================================
# PAGE CONFIGURATION
# ============================================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS with improved styling
st.markdown("""
<style>
    /* Main styling */
    .main-header {
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 0.5rem;
        color: white;
    }
    
    /* Metric cards with better styling */
    .stat-card {
        padding: 1.5rem;
        border-radius: 0.75rem;
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        margin: 0.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        box-shadow: 0 8px 16px rgba(0,0,0,0.15);
        transform: translateY(-2px);
    }
    
    /* Text styling */
    .success-text {
        color: #00AA00;
        font-weight: bold;
    }
    
    .error-text {
        color: #FF0000;
        font-weight: bold;
    }
    
    .info-text {
        color: #0066CC;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    .sidebar-title {
        font-size: 1.3rem;
        font-weight: bold;
        color: #667eea;
        margin-bottom: 1rem;
    }
    
    /* Action buttons */
    .action-button {
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        font-weight: 500;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    /* Section headers */
    .section-header {
        color: #667eea;
        font-size: 1.2rem;
        font-weight: bold;
        border-bottom: 2px solid #667eea;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    
    /* Divider */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 1.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

if 'api_client' not in st.session_state:
    st.session_state.api_client = BackendAPIClient(BACKEND_URL)

# Check server status
def check_server_status():
    """Check if backend server is available"""
    try:
        response = st.session_state.api_client.session.get(
            f"{BACKEND_URL}/health",
            timeout=3
        )
        return response.status_code == 200
    except:
        return False

# Check for saved login credentials
saved_token = None
saved_user_id = None
saved_wardrobe_id = None
saved_username = None

# Try to restore session from backend
def restore_session_from_backend():
    """Check if there's an active session on the backend and restore it."""
    try:
        response = st.session_state.api_client.session.get(
            f"{BACKEND_URL}/api/v1/auth/session/check",
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            return {
                'token': data.get('access_token'),
                'user_id': data.get('user_id'),
                'username': data.get('username'),
                'wardrobe_id': data.get('wardrobe_id')
            }
    except:
        pass
    return None

# Attempt to restore session on app startup
session_data = restore_session_from_backend()
if session_data:
    saved_token = session_data['token']
    saved_user_id = session_data['user_id']
    saved_wardrobe_id = session_data['wardrobe_id']
    saved_username = session_data['username']

# Initialize session state with saved credentials if available
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = saved_token is not None

if 'username' not in st.session_state:
    st.session_state.username = saved_username

if saved_token:
    st.session_state.api_client.token = saved_token
    st.session_state.api_client.user_id = saved_user_id
    st.session_state.api_client.wardrobe_id = saved_wardrobe_id

# Initialize other session state variables
if 'wardrobe_items' not in st.session_state:
    st.session_state.wardrobe_items = []

if 'current_image_name' not in st.session_state:
    st.session_state.current_image_name = None

if 'category_mappings' not in st.session_state:
    st.session_state.category_mappings = None

if 'selected_item_id' not in st.session_state:
    st.session_state.selected_item_id = None

if 'edit_item_id' not in st.session_state:
    st.session_state.edit_item_id = None

if 'nav_page' not in st.session_state:
    st.session_state.nav_page = None

if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Check if navigation was requested from a button click - DO THIS BEFORE SIDEBAR RENDERS
if st.session_state.nav_page:
    st.session_state.current_page = st.session_state.nav_page
    st.session_state.nav_page = None


# ============================================================================
# SIDEBAR
# ============================================================================

with st.sidebar:
    # Logo/Title with styling
    st.markdown("<div class='sidebar-title'>👗 Fashion Wardrobe Manager</div>", unsafe_allow_html=True)
    st.markdown("*AI-Powered Outfit Intelligence*")
    
    if st.session_state.authenticated:
        # User info card
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"👤 **{st.session_state.username}**")
        with col2:
            if st.button("🚪", help="Logout", key="sidebar_logout"):
                st.session_state.authenticated = False
                st.session_state.username = None
                st.session_state.api_client.token = None
                st.rerun()
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Navigation menu
        menu_options = ["Dashboard", "Wardrobe", "Outfits", "Settings"]
        
        # Determine which menu item should be highlighted
        # Don't show edit in menu - it's accessed via button from Wardrobe
        try:
            if st.session_state.current_page == "edit":
                default_idx = 1  # Default to Wardrobe when in edit mode
            else:
                default_idx = menu_options.index(st.session_state.current_page)
        except (ValueError, IndexError):
            default_idx = 0
        
        selected = option_menu(
            menu_title="Navigation",
            options=menu_options,
            icons=["📊", "👗", "👕", "⚙️"],
            menu_icon="cast",
            default_index=default_idx,
            styles={
                "container": {"padding": "0!important", "background-color": "transparent"},
                "icon": {"color": "#667eea", "font-size": "20px"},
                "nav-link": {
                    "text-align": "left",
                    "margin": "0px",
                    "color": "#555",
                    "border-radius": "0.5rem",
                    "padding": "0.75rem 1rem",
                },
                "nav-link-selected": {
                    "background-color": "#667eea",
                    "color": "white",
                    "font-weight": "bold",
                },
            }
        )
        
        # If menu selection changed and we're in edit mode, clear it
        if st.session_state.edit_item_id and selected != "Wardrobe":
            st.session_state.edit_item_id = None
    else:
        selected = None
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.caption("☁️ Backend: ~/.fashion_wardrobe_app/")
    st.caption("v1.0 • Fashion Wardrobe Manager")


# ============================================================================
# MAIN CONTENT
# ============================================================================

# Check server status first
if not check_server_status():
    st.error("⚠️ **Server Unavailable**")
    st.error(
        "The Fashion Wardrobe Manager backend server is currently unavailable.\n\n"
        "**Please ensure the server is running:**\n\n"
        "`python app/main.py`\n\n"
        "Then refresh this page."
    )
    st.info(
        "The backend server must be running at: " + BACKEND_URL
    )
    st.stop()

if not st.session_state.authenticated:
    show_auth_page()
else:
    # Determine which page to show
    # Priority 1: Check if we're in edit mode first (highest priority)
    if st.session_state.edit_item_id:
        show_edit_item()
    # Priority 2: Check if menu selection changed
    elif selected and selected != st.session_state.current_page:
        st.session_state.current_page = selected
        if selected == "Dashboard":
            show_dashboard()
        elif selected == "Wardrobe":
            show_wardrobe()
        elif selected == "Outfits":
            show_outfits()
        elif selected == "Settings":
            show_settings()
    # Priority 3: Show current page
    else:
        if st.session_state.current_page == "Dashboard":
            show_dashboard()
        elif st.session_state.current_page == "Wardrobe":
            show_wardrobe()
        elif st.session_state.current_page == "Outfits":
            show_outfits()
        elif st.session_state.current_page == "Settings":
            show_settings()
