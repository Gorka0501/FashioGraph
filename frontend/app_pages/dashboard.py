"""Dashboard page for displaying wardrobe statistics and quick stats."""

import streamlit as st
from datetime import datetime


def show_dashboard():
    """Display dashboard with wardrobe statistics and recommendations."""
    
    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown("# 📊 Dashboard")
        st.markdown("*Welcome to your Fashion Wardrobe Intelligence*")
    with col2:
        st.markdown("")
        st.markdown("")
        current_time = datetime.now().strftime("%H:%M")
        st.write(f"🕐 {current_time}")
    
    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    
    # Get wardrobe stats
    success, wardrobe = st.session_state.api_client.get_wardrobe()
    
    if success:
        # Statistics Cards
        st.markdown("## 📈 Wardrobe Statistics")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            items_count = wardrobe.get('items_count', 0)
            st.metric("👕 Total Items", items_count, delta="In wardrobe")
        
        with col2:
            outfits_count = wardrobe.get('outfits_count', 0)
            st.metric("👗 Total Outfits", outfits_count, delta="Generated")
        
        with col3:
            st.metric("🎯 Recommendations", "AI Ready", delta="Personalized")
        
        with col4:
            st.metric("✨ Model Status", "Active", delta="Learning")
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Quick Actions
        st.markdown("## ⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("➕ Add New Item", use_container_width=True, type="primary", key="dashboard_add_item"):
                st.session_state.nav_page = "Wardrobe"
                st.rerun()
        
        with col2:
            if st.button("🎯 Browse Outfits", use_container_width=True, key="dashboard_browse_outfits"):
                st.session_state.nav_page = "Outfits"
                st.rerun()
        
        with col3:
            if st.button("⚙️ Settings", use_container_width=True, key="dashboard_settings"):
                st.session_state.nav_page = "Settings"
                st.rerun()
        
        with col4:
            if st.button("📱 Help & Docs", use_container_width=True, key="dashboard_help"):
                st.info("""
                **Fashion Wardrobe Manager Guide**
                
                👕 **Wardrobe**: Upload and manage your clothing items with AI-powered classification
                👗 **Outfits**: Generate outfit combinations powered by intelligent recommendations
                ⚙️ **Settings**: Manage your personal preferences and reset your model
                
                Your personalized AI model learns from your outfit choices to improve recommendations!
                """)
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Wardrobe Info
        st.markdown("## 📂 Wardrobe Information")
        
        created_at = wardrobe.get('created_at', 'Unknown')
        updated_at = wardrobe.get('updated_at', 'Unknown')
        
        info_col1, info_col2 = st.columns(2)
        
        with info_col1:
            st.write(f"**📅 Created**: {created_at}")
            st.write(f"**👕 Items**: {items_count} pieces")
        
        with info_col2:
            st.write(f"**🔄 Last Updated**: {updated_at}")
            st.write(f"**👗 Outfits**: {outfits_count} combinations")
        
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Tips & Features
        st.markdown("## 💡 Tips for Best Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("""
            ✅ **Build Your Wardrobe**
            
            Upload clear photos of your clothing items. The AI will automatically detect categories, colors, and attributes.
            """)
        
        with col2:
            st.success("""
            ✅ **Rate Your Outfits**
            
            Rate generated outfits based on your preferences. Your personal model learns from your feedback!
            """)
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.info("""
            ℹ️ **Personalization**
            
            The more you rate outfits, the smarter the recommendations become. Your personal model improves with every interaction.
            """)
        
        with col4:
            st.info("""
            ℹ️ **Reset Your Model**
            
            Go to Settings → Personal Model if you want to reset your preferences and start with a fresh base model.
            """)
    
    else:
        st.error("Failed to load wardrobe data")
        st.info("Please try refreshing the page or contact support if the issue persists.")
