"""Edit item page for modifying wardrobe items."""

import streamlit as st
from PIL import Image
from pathlib import Path


def show_edit_item():
    """Display item edit page."""
    st.markdown("# ✏️ Edit Item")
    
    # Initialize session state
    if 'edit_item_id' not in st.session_state:
        st.session_state.edit_item_id = None
    
    if 'wardrobe_items' not in st.session_state:
        st.session_state.wardrobe_items = []
    
    if 'category_mappings' not in st.session_state:
        st.session_state.category_mappings = None
    
    # Create a container for the back button at the top
    back_col, _ = st.columns([0.15, 0.85])
    with back_col:
        if st.button("← Back", use_container_width=True, key="back_from_edit"):
            st.session_state.edit_item_id = None
            st.session_state.current_page = "Wardrobe"
            st.rerun()
    
    st.markdown("---")
    
    if not st.session_state.edit_item_id:
        st.info("No item selected. Please select an item from the Wardrobe page.")
        return
    
    # Load items if not loaded
    if not st.session_state.wardrobe_items:
        with st.spinner("Loading item details..."):
            success, items = st.session_state.api_client.get_wardrobe_items()
            if success:
                st.session_state.wardrobe_items = items
            else:
                st.error("Failed to load wardrobe items")
                return
    
    # Find the selected item
    selected_item = next(
        (item for item in st.session_state.wardrobe_items 
         if item['id'] == st.session_state.edit_item_id),
        None
    )
    
    if not selected_item:
        st.error("Item not found. Please select a valid item.")
        if st.button("Go Back to Wardrobe", key="back_item_not_found"):
            st.session_state.edit_item_id = None
            st.session_state.current_page = "Wardrobe"
            st.rerun()
        return
    
    item_id = selected_item['id']
    
    # Image preview
    st.markdown("## 📷 Item Image")
    image_path = selected_item.get('image_path')
    if image_path:
        try:
            # Fetch image from backend API
            success, image_data = st.session_state.api_client.get_item_image(item_id)
            if success and image_data:
                st.image(image_data, width=400)
            else:
                st.caption("📷 Image unavailable")
        except Exception as e:
            st.caption("📷 Image unavailable")
    else:
        st.caption("📷 No image")
    
    st.markdown("---")
    
    # Edit form
    st.markdown("## 🏷️ Categories & Attributes")
    
    # Initialize variables with defaults
    selected_main = None
    selected_sub = []
    selected_cat = []
    selected_rel = []
    available = selected_item.get('available', True)
    
    # Load category mappings if not loaded
    if not st.session_state.category_mappings:
        with st.spinner("Loading categories..."):
            success, result = st.session_state.api_client.get_categories()
            if success:
                st.session_state.category_mappings = result
                mappings = result
            else:
                st.error("Failed to load categories")
                mappings = None
    else:
        mappings = st.session_state.category_mappings
    
    if not mappings:
        st.error("Unable to load category mappings. Please refresh the page.")
        if st.button("Refresh"):
            st.session_state.category_mappings = None
            st.rerun()
        return
    
    # Verify mappings have expected structure
    if not isinstance(mappings, dict) or 'main_categories' not in mappings:
        st.error("⚠️ Unable to load categories. Please refresh the page and try again.")
        if st.button("🔄 Refresh"):
            st.session_state.category_mappings = None
            st.rerun()
        return
    
    st.subheader("📝 Edit Attributes")
    
    # Convert list format to dict format for easier use
    main_dict = {int(idx): name for idx, name in mappings.get('main_categories', [])}
    sub_dict = {int(idx): name for idx, name in mappings.get('sub_categories', [])}
    cat_dict = {int(idx): name for idx, name in mappings.get('categories', [])}
    rel_dict = {int(idx): name for idx, name in mappings.get('related_categories', [])}
    
    # Main Category
    if main_dict:
        current_main = selected_item.get('main_category_indices', [None])[0]
        
        if current_main and current_main in main_dict:
            default_idx = list(main_dict.keys()).index(current_main)
        else:
            default_idx = 0
        
        selected_main = st.selectbox(
            "Main Category",
            options=list(main_dict.keys()),
            format_func=lambda x: main_dict.get(x, str(x)),
            index=default_idx,
            key="main_cat_select"
        )
    
    # Sub Categories (multi-select)
    if sub_dict:
        current_sub = selected_item.get('sub_category_indices', [])
        selected_sub = st.multiselect(
            "Sub Categories",
            options=list(sub_dict.keys()),
            default=[s for s in current_sub if s in sub_dict],
            format_func=lambda x: sub_dict.get(x, str(x)),
            key="sub_cat_multi"
        )
    
    # Categories (multi-select)
    if cat_dict:
        current_cat = selected_item.get('category_indices', [])
        selected_cat = st.multiselect(
            "Categories",
            options=list(cat_dict.keys()),
            default=[c for c in current_cat if c in cat_dict],
            format_func=lambda x: cat_dict.get(x, str(x)),
            key=f"cat_multi_{item_id}"
        )
    
    # Related Categories (multi-select)
    if rel_dict:
        current_rel = selected_item.get('related_indices', [])
        selected_rel = st.multiselect(
            "Related Categories",
            options=list(rel_dict.keys()),
            default=[r for r in current_rel if r in rel_dict],
            format_func=lambda x: rel_dict.get(x, str(x)),
            key=f"rel_multi_{item_id}"
        )
    else:
        st.error("Unable to load categories. Please try again.")
    
    # Status
    st.markdown("---")
    available = st.checkbox(
        "Item is available",
        value=available,
        key="availability_check"
    )
    
    st.markdown("---")
    
    # Action buttons
    st.markdown("## 💾 Actions")
    save_col, delete_col, cancel_col = st.columns(3)
    
    with save_col:
        if st.button("💾 Save Changes", type="primary", use_container_width=True, key=f"save_{item_id}"):
            
            success_update = st.session_state.api_client.update_wardrobe_item(
                item_id,
                main_category_indices=[selected_main] if selected_main is not None else None,
                sub_category_indices=selected_sub,  # Send as-is, even if empty list
                category_indices=selected_cat,  # Send as-is, even if empty list
                related_indices=selected_rel,  # Send as-is, even if empty list
                available=available,
                is_correction=True
            )
            
            if success_update[0]:
                st.success(f"✅ Item #{item_id} updated successfully!")
                st.session_state.wardrobe_items = []  # Reset item cache to reflect changes
            else:
                st.error("❌ Could not update item. Please try again.")
    
    with delete_col:
        if st.button("🗑️ Delete Item", type="secondary", use_container_width=True, key=f"del_edit_{item_id}"):
            success = st.session_state.api_client.delete_wardrobe_item(item_id)
            if success[0]:
                st.success("✅ Item deleted!")
                st.session_state.edit_item_id = None
                st.session_state.wardrobe_items = []  # Reset list to refresh
                st.session_state.current_page = "Wardrobe"
                st.rerun()
            else:
                st.error("❌ Could not delete item. Please try again.")
    
    with cancel_col:
        if st.button("❌ Cancel", use_container_width=True, key=f"cancel_{item_id}"):
            st.session_state.edit_item_id = None
            st.session_state.current_page = "Wardrobe"
            st.rerun()
