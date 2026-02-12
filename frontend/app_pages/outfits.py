"""Outfits browsing and rating page."""

import streamlit as st
from PIL import Image
from pathlib import Path


def show_outfits():
    """Display outfit browsing and management page."""
    st.markdown("# 👕 Outfits")
    
    # Initialize session state for outfit browsing
    if 'outfits_list' not in st.session_state:
        st.session_state.outfits_list = []
    
    if 'current_outfit_index' not in st.session_state:
        st.session_state.current_outfit_index = 0
    
    if 'outfit_view_mode' not in st.session_state:
        st.session_state.outfit_view_mode = "browse"
    
    if 'selected_outfit_item' not in st.session_state:
        st.session_state.selected_outfit_item = None
    
    # Control section
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.button("🔄 Generate New Outfits", use_container_width=True, type="primary"):
            with st.spinner("Generating outfits..."):
                success, message = st.session_state.api_client.generate_outfits()
                if success:
                    st.success("✅ Outfits generated!")
                    st.session_state.outfits_list = []  # Reset list
                    st.rerun()
                else:
                    st.error(f"❌ Failed to generate outfits: {message}")
    
    with col2:
        view_mode = st.radio("View Mode", ["Browse", "All Outfits"], 
                            horizontal=True,
                            label_visibility="collapsed")
        st.session_state.outfit_view_mode = view_mode.lower()
    
    with col3:
        if st.button("🔄 Refresh", use_container_width=True):
            st.session_state.outfits_list = []
            st.rerun()
    
    st.markdown("---")
    
    # Load outfits if not loaded
    if not st.session_state.outfits_list:
        success, outfits = st.session_state.api_client.get_outfits()
        if success:
            st.session_state.outfits_list = outfits
        else:
            st.error("Failed to load outfits")
            return
    
    if not st.session_state.outfits_list:
        st.info("📭 No outfits yet. Generate some outfits to get started!")
        return
    
    # Show item details modal if selected
    if st.session_state.selected_outfit_item:
        _show_item_details_modal()
    
    # Browse mode: Show one outfit at a time
    if st.session_state.outfit_view_mode == "browse":
        _show_browse_mode()
    
    # All Outfits mode: Show all outfits in a grid
    else:
        _show_all_outfits_mode()


def _show_item_details_modal():
    """Display item details modal when an item is clicked."""
    item_data = st.session_state.selected_outfit_item
    item = item_data.get('item', {})
    item_id = item.get('id')
    
    # Create modal container
    modal = st.container(border=True)
    
    with modal:
        # Close button
        col1, col2 = st.columns([0.9, 0.1])
        
        with col2:
            if st.button("✕", key="close_item_modal", use_container_width=True):
                st.session_state.selected_outfit_item = None
                st.rerun()
        
        with col1:
            st.markdown(f"### Item #{item_id} Details")
        
        st.markdown("---")
        
        # Load category mappings if not loaded
        if not st.session_state.category_mappings:
            with st.spinner("Loading attributes..."):
                success, mappings = st.session_state.api_client.get_categories()
                if success:
                    st.session_state.category_mappings = mappings
                else:
                    st.warning("Could not load category mappings")
                    mappings = None
        else:
            mappings = st.session_state.category_mappings
        
        # Image and basic info
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            st.markdown("#### Image")
            image_path = item.get('image_path')
            if image_path:
                try:
                    # Fetch image from backend API
                    item_id = item.get('id')
                    success, image_data = st.session_state.api_client.get_item_image(item_id)
                    if success and image_data:
                        st.image(image_data)
                    else:
                        st.caption("📷 Image unavailable")
                except Exception as e:
                    st.caption("📷 Image unavailable")
            else:
                st.caption("📷 No image")
        
        with col2:
            st.markdown("#### Attributes")
            
            if mappings and isinstance(mappings, dict):
                # Convert list format [[idx, name], ...] to dict format {idx: name}
                main_dict = {int(idx): name for idx, name in mappings.get('main_categories', [])}
                sub_dict = {int(idx): name for idx, name in mappings.get('sub_categories', [])}
                cat_dict = {int(idx): name for idx, name in mappings.get('categories', [])}
                rel_dict = {int(idx): name for idx, name in mappings.get('related_items', [])}
                
                # Main category
                main_cats = item.get('main_category_indices', [])
                if main_cats and main_dict:
                    main_idx = main_cats[0]
                    main_name = main_dict.get(main_idx, f"Main #{main_idx}")
                    st.write(f"**📂 Main**: {main_name}")
                
                # Sub categories
                sub_cats = item.get('sub_category_indices', [])
                if sub_cats and sub_dict:
                    sub_names = [sub_dict.get(idx, f"Sub #{idx}") for idx in sub_cats]
                    if sub_names:
                        st.write(f"**🏷️ Sub**: {', '.join(sub_names)}")
                
                # Categories
                categories = item.get('category_indices', [])
                if categories and cat_dict:
                    cat_names = [cat_dict.get(idx, f"Cat #{idx}") for idx in categories[:3]]
                    if cat_names:
                        st.write(f"**🎯 Categories**: {', '.join(cat_names)}")
                
                # Related items
                related = item.get('related_indices', [])
                if related and rel_dict:
                    rel_names = [rel_dict.get(idx, f"Related #{idx}") for idx in related[:3]]
                    if rel_names:
                        st.write(f"**🔗 Related**: {', '.join(rel_names)}")
                
                # If no attributes found, show message
                if not any([item.get('main_category_indices'), item.get('sub_category_indices'), 
                           item.get('category_indices'), item.get('related_indices')]):
                    st.write("No attributes assigned to this item.")
            else:
                st.warning("Could not load attribute mappings.")
        
        st.markdown("---")
        
        if st.button("Got it!", use_container_width=True):
            st.session_state.selected_outfit_item = None
            st.rerun()


def _show_browse_mode():
    """Display single outfit browsing mode."""
    st.markdown("## 🎯 Outfit Browser")
    st.markdown("Browse outfits one by one and rate them!")
    
    # Get next best outfit (highest system rating)
    sorted_outfits = sorted(st.session_state.outfits_list, 
                           key=lambda x: x.get('system_rating') or 0, 
                           reverse=True)
    
    if sorted_outfits:
        current_outfit = sorted_outfits[st.session_state.current_outfit_index % len(sorted_outfits)]
        outfit_id = current_outfit['id']
        
        # Display outfit info
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Current Outfit")
            st.markdown(f"**Outfit ID**: {outfit_id}")
            
            # Display outfit items
            items = current_outfit.get('items', [])
            if items:
                st.markdown("#### Items in this outfit:")
                
                # Load category mappings if not loaded
                if not st.session_state.category_mappings:
                    success, mappings = st.session_state.api_client.get_categories()
                    if success:
                        st.session_state.category_mappings = mappings
                
                # Sort items by category order: all-body(0), tops(2), bottoms(1), shoes(5), accessories
                category_order = {0: 0, 2: 1, 1: 2, 5: 3, 3: 4, 4: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
                def get_item_sort_key(outfit_item):
                    item = outfit_item.get('item', {})
                    main_cat = item.get('main_category_indices', [999])[0]
                    return category_order.get(main_cat, 999)
                sorted_items = sorted(items, key=get_item_sort_key)
                
                # Create grid of items
                cols = st.columns(len(sorted_items) if len(sorted_items) <= 4 else 4)
                for idx, outfit_item in enumerate(sorted_items):
                    item = outfit_item.get('item')
                    with cols[idx % 4]:
                        item_id = item.get('id')
                        st.markdown(f"**Item #{item_id}**")
                        
                        # Try to display image - make it clickable
                        image_path = item.get('image_path')
                        if image_path:
                            try:
                                # Fetch image from backend API
                                success, image_data = st.session_state.api_client.get_item_image(item_id)
                                if success and image_data:
                                    if st.button("View Details", key=f"view_detail_browse_{item_id}", use_container_width=True):
                                        st.session_state.selected_outfit_item = outfit_item
                                        st.rerun()
                                    st.image(image_data)
                            except Exception as e:
                                st.caption("📷 Image unavailable")
                        else:
                            st.caption("📷 No image")
                        
                        # Display categories
                        st.markdown("---")
                        
                        # Main category
                        main_cats = item.get('main_category_indices', [])
                        if main_cats and st.session_state.category_mappings:
                            main_idx = main_cats[0]
                            if isinstance(st.session_state.category_mappings, dict) and 'main' in st.session_state.category_mappings:
                                main_name = st.session_state.category_mappings['main'].get(str(main_idx), f"Main #{main_idx}")
                                st.caption(f"📂 **{main_name}**")
                        
                        # Sub categories
                        sub_cats = item.get('sub_category_indices', [])
                        if sub_cats and st.session_state.category_mappings:
                            if isinstance(st.session_state.category_mappings, dict) and 'sub' in st.session_state.category_mappings:
                                sub_names = []
                                for sub_idx in sub_cats[:2]:  # Show first 2
                                    sub_name = st.session_state.category_mappings['sub'].get(str(sub_idx), f"Sub #{sub_idx}")
                                    sub_names.append(sub_name)
                                if sub_names:
                                    st.caption(f"🏷️ {', '.join(sub_names)}")
            
            # Scores section
            st.markdown("---")
            st.markdown("### Ratings")
            col_sys, col_user = st.columns(2)
            
            with col_sys:
                system_rating = current_outfit.get('system_rating') or 0
                # Convert backend rating (0-1) to display (0-5)
                system_rating_display = system_rating * 5
                st.metric("System Score", f"{system_rating_display:.1f}/5 ⭐")
            
            with col_user:
                user_rating = current_outfit.get('user_rating')
                if user_rating is None:
                    st.metric("Your Rating", "Not rated")
                else:
                    # Convert backend rating (0-1) to display (0-5)
                    user_rating_display = user_rating * 5
                    st.metric("Your Rating", f"⭐ {user_rating_display:.1f}/5")
        
        with col2:
            st.markdown("### Actions")
            
            # Rating slider (0-5 display, 0-1 backend)
            st.markdown("**Rate this outfit (0-5):**")
            rating_display = st.slider(
                "Rating",
                min_value=0.0,
                max_value=5.0,
                step=0.5,
                value=user_rating * 5 if user_rating else 2.5,
                label_visibility="collapsed",
                key=f"rating_slider_{outfit_id}"
            )
            
            # Convert display rating (0-5) to backend rating (0-1)
            rating_backend = rating_display / 5.0
            
            if st.button("⭐ Submit Rating", use_container_width=True, key=f"submit_rating_{outfit_id}"):
                success, _ = st.session_state.api_client.rate_outfit(outfit_id, rating_backend)
                if success:
                    st.success(f"✅ Rated {rating_display:.1f}/5 stars!")
                    st.session_state.outfits_list = []
                    st.rerun()
                else:
                    st.error("Failed to rate outfit")
            
            st.markdown("---")
            st.markdown("**Quick actions:**")
            col_like, col_dislike = st.columns(2)
            
            with col_like:
                if st.button("👍 Like (5/5)", use_container_width=True, key=f"like_{outfit_id}"):
                    success, _ = st.session_state.api_client.rate_outfit(outfit_id, 1.0)
                    if success:
                        st.success("✅ Liked!")
                        st.session_state.outfits_list = []
                        st.rerun()
                    else:
                        st.error("Failed to rate outfit")
            
            with col_dislike:
                if st.button("👎 Dislike (0/5)", use_container_width=True, key=f"dislike_{outfit_id}"):
                    success, _ = st.session_state.api_client.rate_outfit(outfit_id, 0.0)
                    if success:
                        st.success("✅ Disliked!")
                        st.session_state.outfits_list = []
                        st.rerun()
                    else:
                        st.error("Failed to rate outfit")
            
            st.markdown("---")
            st.markdown("**Navigation:**")
            
            col_next, col_prev = st.columns(2)
            with col_next:
                if st.button("➡️ Next", use_container_width=True, key=f"next_{outfit_id}"):
                    st.session_state.current_outfit_index += 1
                    st.rerun()
            
            with col_prev:
                if st.button("⬅️ Prev", use_container_width=True, key=f"prev_{outfit_id}"):
                    st.session_state.current_outfit_index = max(0, st.session_state.current_outfit_index - 1)
                    st.rerun()
            
            st.markdown("---")
            
            if st.button("🗑️ Delete", use_container_width=True, type="secondary", key=f"delete_{outfit_id}"):
                if st.session_state.api_client.delete_outfit(outfit_id)[0]:
                    st.success("✅ Outfit deleted!")
                    st.session_state.outfits_list = []
                    st.session_state.current_outfit_index = 0
                    st.rerun()
                else:
                    st.error("Failed to delete outfit")
            
            # Info
            st.caption(f"Outfit {st.session_state.current_outfit_index % len(sorted_outfits) + 1} of {len(sorted_outfits)}")


def _show_all_outfits_mode():
    """Display all outfits in grid mode."""
    st.markdown("## 📋 All Outfits")
    st.markdown("View and manage all outfits")
    
    # Load category mappings if not loaded
    if not st.session_state.category_mappings:
        success, mappings = st.session_state.api_client.get_categories()
        if success:
            st.session_state.category_mappings = mappings
    
    # Sort by rating
    sorted_outfits = sorted(st.session_state.outfits_list,
                           key=lambda x: (x.get('user_rating') or -1, x.get('system_rating') or 0),
                           reverse=True)
    
    # Create columns for outfit cards
    cols = st.columns(3)
    
    for idx, outfit in enumerate(sorted_outfits):
        outfit_id = outfit['id']
        items = outfit.get('items', [])
        system_rating = outfit.get('system_rating') or 0
        user_rating = outfit.get('user_rating')
        
        with cols[idx % 3]:
            with st.container(border=True):
                st.markdown(f"### 👕 Outfit #{outfit_id}")
                
                # Display all items in outfit with images and categories
                if items:
                    for item_idx, outfit_item in enumerate(items):
                        item = outfit_item.get('item')
                        item_id = item.get('id')
                        
                        # Image with click to view details
                        image_path = item.get('image_path')
                        if image_path:
                            try:
                                # Fetch image from backend API
                                success, image_data = st.session_state.api_client.get_item_image(item_id)
                                if success and image_data:
                                    if st.button("View Details", key=f"view_detail_all_{item_id}_{outfit_id}", use_container_width=True):
                                        st.session_state.selected_outfit_item = outfit_item
                                        st.rerun()
                                    st.image(image_data)
                            except Exception as e:
                                st.caption("📷 Image unavailable")
                        else:
                            st.caption("📷 No image")
                        
                        # Item info with category
                        st.markdown(f"**Item #{item_id}**")
                        
                        # Main category
                        main_cats = item.get('main_category_indices', [])
                        if main_cats and st.session_state.category_mappings:
                            main_idx = main_cats[0]
                            if isinstance(st.session_state.category_mappings, dict) and 'main' in st.session_state.category_mappings:
                                main_name = st.session_state.category_mappings['main'].get(str(main_idx), f"Main #{main_idx}")
                                st.caption(f"📂 {main_name}")
                        
                        if item_idx < len(items) - 1:
                            st.divider()
                    
                    st.markdown("---")
                    st.caption(f"**{len(items)} items total**")
                
                # Ratings
                st.markdown("**Ratings:**")
                st.markdown(f"🤖 System: {system_rating:.2f}")
                if user_rating is not None:
                    st.markdown(f"👤 Your Rating: ⭐ {user_rating:.1f}/5")
                else:
                    st.markdown(f"👤 Your Rating: Not rated")
                
                st.markdown("---")
                
                # Action buttons
                col_like, col_dislike, col_del = st.columns(3)
                
                with col_like:
                    if st.button("👍", key=f"card_like_{outfit_id}", use_container_width=True):
                        success, _ = st.session_state.api_client.rate_outfit(outfit_id, 1.0)
                        if success:
                            st.rerun()
                
                with col_dislike:
                    if st.button("👎", key=f"card_dislike_{outfit_id}", use_container_width=True):
                        success, _ = st.session_state.api_client.rate_outfit(outfit_id, 0.0)
                        if success:
                            st.rerun()
                
                with col_del:
                    if st.button("🗑️", key=f"card_delete_{outfit_id}", use_container_width=True):
                        if st.session_state.api_client.delete_outfit(outfit_id)[0]:
                            st.session_state.outfits_list = []  # Reset list to refresh
                            st.rerun()
