"""Settings page for app configuration."""

import streamlit as st


def show_settings():
    """Settings page with user preferences and model management."""
    st.markdown("# ⚙️ Settings")
    st.markdown("*Manage your personal preferences and AI model*")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    tab1, tab2, tab3 = st.tabs(["🤖 Personal Model", "👤 Account", "ℹ️ About"])
    
    # ========================================================================
    # TAB 1: PERSONAL MODEL
    # ========================================================================
    with tab1:
        st.markdown("### Personal Preference Model")
        st.write("""
        Your personalized preference model learns from your outfit ratings and improves 
        recommendations over time. This model is unique to you and stored securely on the backend.
        """)
        
        st.markdown("---")
        st.markdown("#### Model Management Options")
        
        col1, col2 = st.columns(2)
        
        # RETRAIN OPTION
        with col1:
            st.markdown("##### 🔁 Retrain From Base")
            st.write("""
            Rebuild your personal model from scratch using all your historical ratings.
            """)
            
            with st.expander("When to use Retrain?"):
                st.write("""
                - You want a fresh start with improved recommendations
                - Your preferences have changed significantly
                - You want to reset the learning without losing history
                """)
            
            if st.button("🔁 Retrain Personal Model", key="retrain_model_btn", type="primary", use_container_width=True):
                with st.spinner("Retraining your personal model..."):
                    success, data = st.session_state.api_client.retrain_personal_model()
                    if success:
                        st.success("✨ Personal model retrained successfully!")
                        st.balloons()
                    else:
                        st.error("Unable to retrain model. Please try again later.")
        
        # RESET OPTION
        with col2:
            st.markdown("##### 🗑️ Reset Personal Model")
            st.write("""
            Delete your personal model and revert to the base model.
            """)
            
            with st.expander("When to use Reset?"):
                st.write("""
                - You want to completely start over
                - Your model needs a fresh reset
                - You want to use the base model instead
                """)
            
            if st.button("🗑️ Reset Personal Model", key="reset_model_btn", use_container_width=True):
                with st.spinner("Resetting your personal model..."):
                    success, data = st.session_state.api_client.reset_personal_model()
                    if success:
                        st.success("✅ Personal model reset!")
                        st.info("Your ratings are preserved. You're now using the base model.")
                    else:
                        st.error("Unable to reset model. Please try again later.")
        
        st.markdown("---")
        st.markdown("#### How Your Model Learns")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            **Training Process:**
            - Each outfit you rate teaches your model
            - Model updates every 10 ratings
            - Learns your style preferences
            - Improves recommendations over time
            """)
        
        with col2:
            st.write("""
            **Base Model:**
            - Trained on all users' feedback
            - Updates every 100 community ratings
            - Used for initial recommendations
            - Your personal model refines it
            """)
    
    with tab2:
        st.markdown("### Account Settings")
        st.write("Manage your account information and security.")
        
        st.markdown("---")
        st.markdown("#### User Information")
        
        username = st.session_state.get("username", "Not logged in")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write(f"**Username:** `{username}`")
        with col2:
            st.write("**Status:** 🟢 Active")
        
        st.markdown("---")
        st.markdown("#### Data & Storage")
        
        st.info("""
        **Backend Server Storage:**
        - All clothing images and metadata
        - Your personal preference model (fine-tuned just for you)
        - Your rating history for continuous learning
        - Account data and authentication
        - Location: `~/.fashion_wardrobe_app/` on the server
        """)
        
        st.info("""
        **Streamlit Session (Browser Memory):**
        - Authentication token (current session only)
        - Cached wardrobe items (for this session)
        - Current UI state (selected items, filters, etc.)
        
        **Important:** All session data is cleared when you log out or close the browser.
        Nothing is saved to your local disk.
        """)
        
        st.markdown("---")
        st.markdown("#### Backend Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            try:
                is_connected = st.session_state.api_client.is_connected()
                if is_connected:
                    st.success("✅ Backend is running")
                else:
                    st.warning("⚠️ Connection unavailable")
            except Exception:
                st.warning("⚠️ Connection unavailable")
        
        with col2:
            if st.button("🔄 Check Connection", use_container_width=True):
                with st.spinner("Checking connection..."):
                    try:
                        is_connected = st.session_state.api_client.is_connected()
                        if is_connected:
                            st.success("✅ Backend is running")
                        else:
                            st.warning("⚠️ Connection unavailable - try again later")
                    except Exception:
                        st.warning("⚠️ Connection unavailable - try again later")
        
        st.markdown("---")
        st.markdown("#### Logout")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.write("Sign out from your account")
        with col2:
            if st.button("🚪 Logout", type="secondary", use_container_width=True):
                st.session_state.clear()
                st.success("You have been logged out.")
                st.rerun()
    
    with tab3:
        st.markdown("### About Fashion Wardrobe Manager")
        st.write("Learn about this intelligent wardrobe management system.")
        
        st.markdown("---")
        st.markdown("#### ✨ Key Features")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            **Wardrobe Management**
            - Upload and catalog clothing items
            - AI-powered automatic classification
            - Organize by category and attributes
            
            **Smart Recommendations**
            - AI-powered outfit generation
            - Personalized suggestions
            - Learn your style preferences
            """)
        
        with col2:
            st.write("""
            **Personalization**
            - Rate outfits to teach your model
            - Real-time preference learning
            - Model improves with every rating
            
            **Multi-Platform**
            - Web app (this interface)
            - Desktop application
            - Mobile-ready design
            """)
        
        st.markdown("---")
        st.markdown("#### 🏗️ Technology Stack")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("""
            **Frontend:**
            - Streamlit for interactive UI
            - No local data storage
            - Responsive design
            """)
        
        with col2:
            st.write("""
            **Backend:**
            - FastAPI framework
            - SQLite database
            - Secure authentication
            """)
        
        st.markdown("---")
        st.markdown("#### 📊 ML Architecture")
        
        st.write("""
        **Advanced Models:**
        - **FashionCLIP**: Visual understanding of clothing
        - **HGNN**: Hierarchical fashion relationships
        - **Personal Models**: Individual preference learning
        - **Tagger Network**: Attribute extraction
        """)
        
        st.markdown("---")
        st.markdown("#### 📝 Version & Support")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**App Version:** 1.0.0")
        
        with col2:
            st.write("**Release Date:** 2025")
        
        with col3:
            st.write("**Status:** Active")

