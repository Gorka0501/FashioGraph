"""Wardrobe management page for viewing and editing items."""

import streamlit as st
from PIL import Image
from pathlib import Path
import tempfile


def show_wardrobe():
    """Display wardrobe with grid layout and quick actions.
    
    **Responsive Design Features:**
    - Grid layout adapts based on screen width (4 columns on desktop, reduces on mobile)
    - Touch-friendly button sizing for mobile devices
    - Flexible filtering options collapse on smaller screens
    - Container-based layout for better responsiveness
    
    **Key Actions:**
    - ✏️ Edit: Modify item details (colors, sizes, categories, notes)
    - 🟢/🔴 Toggle Availability: Mark items as clean/dirty or available/unavailable
    - 🗑️ Delete: Remove items from wardrobe permanently
    """
    st.markdown("# 👗 Wardrobe")
    
    # Ensure storage config is loaded from backend
    try:
        from config import FrontendStorageConfig
    except ImportError:
        from .config import FrontendStorageConfig
    
    if not FrontendStorageConfig.get_user_image_dir():
        success, config = st.session_state.api_client.fetch_storage_config()
        if success:
            st.sidebar.success("✅ Storage config loaded")
        else:
            st.sidebar.warning("⚠️ Could not load storage config")
    
    # Initialize session state
    if 'selected_item_id' not in st.session_state:
        st.session_state.selected_item_id = None
    
    if 'wardrobe_items' not in st.session_state:
        st.session_state.wardrobe_items = []
    
    if 'category_mappings' not in st.session_state:
        st.session_state.category_mappings = None
    
    if 'upload_complete' not in st.session_state:
        st.session_state.upload_complete = False
    
    if 'edit_item_id' not in st.session_state:
        st.session_state.edit_item_id = None
    
    if 'selected_main_cat' not in st.session_state:
        st.session_state.selected_main_cat = "All"
    
    if 'selected_sub_cat' not in st.session_state:
        st.session_state.selected_sub_cat = "All"
    
    if 'show_available' not in st.session_state:
        st.session_state.show_available = True
    
    if 'show_dirty' not in st.session_state:
        st.session_state.show_dirty = True
    
    # Add new item section
    st.markdown("## ➕ Add New Item")
    
    # Only show uploader if upload is not complete
    if not st.session_state.upload_complete:
        uploaded_file = st.file_uploader("Upload clothing image", type=['jpg', 'jpeg', 'png'], key="file_uploader")
        
        if uploaded_file:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                st.image(uploaded_file)
            
            with col2:
                st.markdown("### Preview")
                st.write(f"**Filename**: {uploaded_file.name}")
                st.write(f"**Size**: {uploaded_file.size / 1024:.1f} KB")
                
                if st.button("📤 Analyze & Upload", type="primary", use_container_width=True):
                    with st.spinner("Analyzing image and uploading to backend..."):
                        # Save uploaded file to temp location
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp_file:
                            tmp_file.write(uploaded_file.getbuffer())
                            temp_path = Path(tmp_file.name)
                        
                        try:
                            # Send to backend for analysis and storage
                            # Backend will save image and store in database
                            success, response = st.session_state.api_client.add_wardrobe_item(temp_path)
                            
                            if success:
                                item_id = response.get('id')
                                st.success(f"✅ Image analyzed and saved on backend! Item ID: {item_id}")
                                
                                # Display the item that was added
                                st.markdown("### Item Added")
                                st.write(f"**Item ID**: {item_id}")
                                st.write(f"**Categories**: {', '.join([str(c) for c in response.get('category_indices', [])])}")
                                st.info("📁 Image is stored on the backend and accessible from any device")
                                
                                st.session_state.wardrobe_items = []  # Reset to refresh list
                                st.session_state.upload_complete = True
                                import time
                                time.sleep(1)  # Give user time to see the success message
                                st.rerun()
                            
                            else:
                                st.error("❌ Could not analyze image. Please try again.")
                        
                        finally:
                            # Clean up temp file
                            if temp_path.exists():
                                temp_path.unlink()
    else:
        # Show success message and reset button
        st.success("✅ Item added! Ready to upload another.")
        if st.button("➕ Upload Another Item", use_container_width=True):
            st.session_state.upload_complete = False
            st.rerun()
    
    st.markdown("---")
    
    # Wardrobe items grid
    st.markdown("## 📦 Your Items")
    
    # Responsive refresh button - moves to help column on mobile
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("🔄 Refresh", use_container_width=True, help="Reload items from server"):
            st.session_state.wardrobe_items = []
            st.rerun()
    
    # Load items if not loaded
    if not st.session_state.wardrobe_items:
        success, items = st.session_state.api_client.get_wardrobe_items()
        if success:
            st.session_state.wardrobe_items = items
            st.info(f"Loaded {len(items)} items")
        else:
            st.error("Failed to load wardrobe items")
    
    if st.session_state.wardrobe_items:
        # Responsive filters with category selection
        st.markdown("### 🔍 Filter Options")
        
        # Load category mappings if not loaded
        if st.session_state.category_mappings is None:
            success, categories = st.session_state.api_client.get_categories()
            if success:
                st.session_state.category_mappings = categories
        
        # Create responsive filter layout
        # On wide screens: all filters in one row
        # On narrow screens: stack filters for better readability
        filter_cols = st.columns([1, 1, 1.2, 1.2], gap="small")
        
        with filter_cols[0]:
            st.session_state.show_available = st.checkbox(
                "Available",
                value=st.session_state.show_available,
                help="Show clean items ready to wear"
            )
        
        with filter_cols[1]:
            st.session_state.show_dirty = st.checkbox(
                "Dirty",
                value=st.session_state.show_dirty,
                help="Show items that need washing"
            )
        
        with filter_cols[2]:
            search_id = st.text_input(
                "Search ID",
                "",
                placeholder="Item #...",
                help="Find items by ID"
            )
        
        with filter_cols[3]:
            st.empty()
        
        # Category filters (expandable section for cleaner UI)
        with st.expander("📂 Filter by Category", expanded=False):
            cat_cols = st.columns([1, 1], gap="medium")
            
            with cat_cols[0]:
                if st.session_state.category_mappings:
                    main_categories = st.session_state.category_mappings.get('main_categories', [])
                    main_cat_dict = {str(item[1]): int(item[0]) for item in main_categories}
                    main_cat_list = ["All"] + sorted(list(main_cat_dict.keys()))
                    
                    st.session_state.selected_main_cat = st.selectbox(
                        "Main Category",
                        main_cat_list,
                        index=main_cat_list.index(st.session_state.selected_main_cat) if st.session_state.selected_main_cat in main_cat_list else 0,
                        help="Filter by main clothing category"
                    )
                else:
                    st.info("Loading categories...")
            
            with cat_cols[1]:
                if st.session_state.category_mappings:
                    sub_categories = st.session_state.category_mappings.get('sub_categories', [])
                    sub_cat_dict = {str(item[1]): int(item[0]) for item in sub_categories}
                    sub_cat_list = ["All"] + sorted(list(sub_cat_dict.keys()))
                    
                    st.session_state.selected_sub_cat = st.selectbox(
                        "Sub Category",
                        sub_cat_list,
                        index=sub_cat_list.index(st.session_state.selected_sub_cat) if st.session_state.selected_sub_cat in sub_cat_list else 0,
                        help="Filter by subcategory"
                    )
                else:
                    st.info("Loading categories...")
        
        # Convert selected categories to IDs for filtering
        selected_main = None
        selected_sub = None
        
        if st.session_state.category_mappings:
            main_categories = st.session_state.category_mappings.get('main_categories', [])
            main_cat_dict = {str(item[1]): int(item[0]) for item in main_categories}
            if st.session_state.selected_main_cat != "All" and st.session_state.selected_main_cat in main_cat_dict:
                selected_main = main_cat_dict[st.session_state.selected_main_cat]
            
            sub_categories = st.session_state.category_mappings.get('sub_categories', [])
            sub_cat_dict = {str(item[1]): int(item[0]) for item in sub_categories}
            if st.session_state.selected_sub_cat != "All" and st.session_state.selected_sub_cat in sub_cat_dict:
                selected_sub = sub_cat_dict[st.session_state.selected_sub_cat]
        
        # Filter items based on all criteria
        filtered_items = []
        for item in st.session_state.wardrobe_items:
            is_available = item.get('available', True)
            item_id = str(item.get('id', ''))
            categories = item.get('categories', {})
            
            # Availability filter
            if not st.session_state.show_available and is_available:
                continue
            if not st.session_state.show_dirty and not is_available:
                continue
            
            # ID search filter
            if search_id and search_id not in item_id:
                continue
            
            # Main category filter
            if selected_main is not None:
                item_main_cat = categories.get('main')
                if item_main_cat != selected_main:
                    continue
            
            # Sub category filter
            if selected_sub is not None:
                item_sub_cat = categories.get('sub')
                if item_sub_cat != selected_sub:
                    continue
            
            filtered_items.append(item)
        
        # Sort items by category order: all-body(0), tops(2), bottoms(1), shoes(5), accessories
        category_order = {0: 0, 2: 1, 1: 2, 5: 3, 3: 4, 4: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10}
        def get_item_sort_key(item):
            main_cat = item.get('categories', {}).get('main', 999)
            return category_order.get(main_cat, 999)
        filtered_items.sort(key=get_item_sort_key)
        
        # Display grid with responsive columns
        st.write("")  # Add spacing
        
        # Show item count
        if filtered_items:
            st.markdown(f"**Showing {len(filtered_items)} item(s)**")
        
        cols = st.columns(4)
        
        for idx, item in enumerate(filtered_items):
            item_id = item.get('id')
            available = item.get('available', True)
            image_path = item.get('image_path')
            
            with cols[idx % 4]:
                with st.container(border=True):
                    # Image
                    if image_path:
                        try:
                            # Fetch image from backend API
                            item_id = item.get('id')
                            success, image_data = st.session_state.api_client.get_item_image(item_id)
                            if success and image_data:
                                st.image(image_data)
                            else:
                                st.caption("📷 Image unavailable")
                        except:
                            st.caption("📷 Image unavailable")
                    else:
                        st.caption("📷 No image")
                    
                    # Item info
                    status = "✅" if available else "🔴"
                    st.markdown(f"**{status} Item #{item_id}**")
                    
                    st.markdown("---")
                    st.markdown("**Actions:**")
                    
                    # EDIT BUTTON - Full width on all screens
                    if st.button(
                        "✏️ Edit Item",
                        key=f"edit_item_{item_id}",
                        use_container_width=True,
                        help="Open editor to change colors, size, categories, notes, and ratings"
                    ):
                        st.session_state.edit_item_id = item_id
                        st.rerun()
                    
                    # TOGGLE AVAILABILITY - Full width on all screens
                    btn_text = "🟢 Mark Unavailable (Dirty)" if available else "🔴 Mark Available (Clean)"
                    
                    if st.button(
                        btn_text,
                        key=f"toggle_avail_{item_id}",
                        use_container_width=True,
                        help="Change item status: Clean/Available ↔ Dirty/Unavailable"
                    ):
                        with st.spinner(f"Updating item #{item_id}..."):
                            success, response = st.session_state.api_client.update_wardrobe_item(
                                item_id,
                                available=not available
                            )
                            if success:
                                new_status = "Available ✅" if not available else "Unavailable 🔴"
                                st.success(f"Item #{item_id} is now {new_status}")
                                st.session_state.wardrobe_items = []
                                st.rerun()
                            else:
                                st.error("❌ Could not update item. Please try again.")
                    
                    # DELETE BUTTON - Full width on all screens
                    if st.button(
                        "🗑️ Delete Item",
                        key=f"delete_{item_id}",
                        use_container_width=True,
                        help="Permanently remove this item from your wardrobe (cannot be undone)"
                    ):
                        with st.spinner(f"Deleting item #{item_id}..."):
                            success, response = st.session_state.api_client.delete_wardrobe_item(item_id)
                            if success:
                                st.success(f"Item #{item_id} deleted successfully")
                                st.session_state.wardrobe_items = []
                                st.rerun()
                            else:
                                st.error("❌ Could not delete item. Please try again.")
    else:
        st.info("No items in wardrobe yet. Add your first item above!")
