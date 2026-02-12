"""Authentication page for login and registration."""

import streamlit as st


def show_auth_page():
    """Display authentication page"""
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        st.markdown("---")
        st.markdown("### 👗 Fashion Wardrobe Manager")
        st.markdown("Welcome! Please login or register to continue.")
        st.markdown("---")
        
        # Tab selection
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            _show_login_form()
        
        with tab2:
            _show_register_form()


def _show_login_form():
    """Display login form."""
    st.markdown("#### Login to Your Account")
    
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    
    if st.button("🔓 Login", type="primary", use_container_width=True):
        if not username or not password:
            st.error("Please enter both username and password")
        else:
            with st.spinner("Logging in..."):
                success, response = st.session_state.api_client.login(username, password)
                
                if success:
                    # Fetch backend storage config
                    config_success, config_data = st.session_state.api_client.fetch_storage_config()
                    
                    st.session_state.authenticated = True
                    st.session_state.username = username
                    st.success("✅ Login successful!")
                    st.rerun()
                else:
                    st.error("❌ Login failed. Please check your username and password.")


def _show_register_form():
    """Display registration form."""
    st.markdown("#### Create New Account")
    
    username = st.text_input("Choose a username", key="reg_username")
    password = st.text_input("Choose a password", type="password", key="reg_password")
    password_confirm = st.text_input("Confirm password", type="password", key="reg_password_confirm")
    
    if st.button("✍️ Register", type="primary", use_container_width=True):
        if not username or not password or not password_confirm:
            st.error("Please fill in all fields")
        elif password != password_confirm:
            st.error("Passwords don't match")
        elif len(password) < 6:
            st.error("Password must be at least 6 characters")
        else:
            with st.spinner("Creating account..."):
                success, response = st.session_state.api_client.register(username, password)
                
                if success:
                    # Auto-login after registration
                    login_success, login_response = st.session_state.api_client.login(username, password)
                    
                    if login_success:
                        # Fetch backend storage config
                        config_success, config_data = st.session_state.api_client.fetch_storage_config()
                        
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.success("✅ Account created and logged in!")
                        st.rerun()
                    else:
                        st.error("⚠️ Account created, but there was an issue logging in. Please try logging in manually.")
                else:
                    st.error("❌ Registration failed. This username might already be taken.")
