import streamlit as st
import time
from src.backend.ollama_client import load_messages, save_messages, clear_chat
from src.backend.ollama_client import ollama_chat, ollama_chat_stream
from typing import List, Dict, Any, Optional

# HÀM MỚI: Khởi tạo session state
def initialize_session_state():
    """Khởi tạo tất cả session state - LUÔN VÀO chat_history_1.json ĐẦU TIÊN"""
    # DANH SÁCH CONVERSATIONS
    if "conversations" not in st.session_state:
        conversations = []
       
        # ===== LUÔN ƯU TIÊN chat_history_1.json ĐẦU TIÊN =====
        messages_1 = load_messages("chat_history_1.json")
       
        if messages_1:
            conversations.append({
                "id": 1,
                "name": "Thanh niên nghiêm túc",
                "messages": messages_1,
                "active": True
            })
        else:
            conversations.append({
                "id": 1,
                "name": "Thanh niên nghiêm túc",
                "messages": [{"role": "ai", "content": "Có cần giúp gì hong?🥱"}],
                "active": True
            })
            save_messages(conversations[0]["messages"], "chat_history_1.json")
       
        import os, glob
        from src.backend.ollama_client import history_path
       
        chat_files = glob.glob(history_path("chat_history_*.json"))
        for filepath in chat_files:
            filename = os.path.basename(filepath)
            if filename == "chat_history_1.json":
                continue
           
            try:
                conv_id = int(filename.replace("chat_history_", "").replace(".json", ""))
                if conv_id > 1:
                    messages = load_messages(filename)
                    if messages:
                        conversations.append({
                            "id": conv_id,
                            "name": f"Thanh niên nghiêm túc {conv_id}",
                            "messages": messages,
                            "active": False
                        })
            except:
                continue
       
        conversations.sort(key=lambda x: x["id"])
       
        st.session_state.conversations = conversations
        st.session_state.current_conversation_id = 1
   
    if "next_conversation_id" not in st.session_state:
        max_id = max([conv["id"] for conv in st.session_state.conversations]) if st.session_state.conversations else 0
        st.session_state.next_conversation_id = max_id + 1
   
    if "show_conversation_list" not in st.session_state:
        st.session_state.show_conversation_list = False
   
    if "confirm_delete" not in st.session_state:
        st.session_state.confirm_delete = False
   
    if "delete_conv_id" not in st.session_state:
        st.session_state.delete_conv_id = None

    # === Khởi tạo bg_theme và streaming_mode ===
    if "bg_theme" not in st.session_state:
        st.session_state.bg_theme = "Mặc định (Xanh dương)"
    if "streaming_mode" not in st.session_state:
        st.session_state.streaming_mode = True

# HÀM MỚI: Lưu conversation ra file riêng
def save_conversation_to_file(conversation_id: int, messages: List[Dict]):
    filename = f"chat_history_{conversation_id}.json"
    save_messages(messages, filename)

def apply_custom_styles():
    # === Đổi nền theo theme ===
    bg_map = {
        "Mặc định (Xanh dương)": "linear-gradient(to right, #000428, #004e92)",
        "Tím hồng": "linear-gradient(to right, #4a148c, #880e4f)",
        "Cam vàng": "linear-gradient(to right, #ff512f, #f09819)",
        "Xanh lá": "linear-gradient(to right, #11998e, #38ef7d)",
        "Xám bạc": "linear-gradient(to right, #606c88, #3f4c6b)"
    }
    current_bg = bg_map.get(st.session_state.bg_theme, bg_map["Mặc định (Xanh dương)"])

    st.markdown(
        f"""
        <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            background: {current_bg};
            height: 100vh;
            display: grid;
            place-items: center;
        }}
        header {{
            visibility: hidden;
        }}
        .block-container {{
            padding-top: 0rem; padding-bottom: 0rem;
        }}
       
        /* KHUNG CHAT TRẮNG VỚI HEADER XANH Ở TRÊN */
        .stApp {{
            width: 400px;
            height: 680px;
            background: #ffffff;
            border-radius: 20px;
            overflow: hidden;
            box-shadow: 0 12px 24px rgba(0, 0, 0, 0.2);
            display: flex;
            flex-direction: column;
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
        }}
       
        /* CSS cho tin nhắn */
        [data-testid="stChatMessageContent"] p {{
            color: black !important;
        }}
       
        div[data-testid="stChatMessage"][data-message-author="user"]
        [data-testid="stChatMessageContent"] p {{
            color: #000000 !important;
            font-weight: 500;
        }}
       
        div[data-testid="stChatMessage"][data-message-author="assistant"]
        [data-testid="stChatMessageContent"] p {{
            color: #333333 !important;
        }}

        /* Vòng tròn xoay không chữ */
        .stSpinner > div {{
            width: 50px !important;
            height: 50px !important;
            border: 6px solid rgba(0, 74, 173, 0.2) !important;
            border-top: 6px solid #004aad !important;
            border-radius: 50% !important;
            animation: spin 1s linear infinite !important;
        }}
        .stSpinner > div::after {{
            content: none !important;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
   
    st.markdown(
        """
        <style>
        .stChatMessage * {
            color: #000000 !important;
        }
        div[data-testid="stChatMessage"],
        div[data-testid="stChatMessage"] *,
        div[data-testid="stChatMessageContent"],
        div[data-testid="stChatMessageContent"] *,
        .stChatMessage p,
        .stChatMessage span,
        .stChatMessage div {
            color: #000000 !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

def ui():
    # Đã gọi initialize_session_state() ở main_ui()
    apply_custom_styles()
   
    current_messages = []
    for conv in st.session_state.conversations:
        if conv["active"]:
            current_messages = conv["messages"]
            break
   
    if not current_messages:
        current_messages = [{"role": "ai", "content": "Có cần giúp gì hong?🥱"}]
   
    header_container = st.container()
    with header_container:
        current_conv_name = "Thanh niên nghiêm túc"
        for conv in st.session_state.conversations:
            if conv["active"]:
                current_conv_name = conv["name"]
                break
       
        st.markdown(f"""
        <div style="
            position: fixed;
            top: calc(50% - 340px);
            left: 50%;
            transform: translateX(-50%);
            width: 400px;
            background: #004aad;
            color: white;
            padding: 15px 20px;
            border-radius: 20px 20px 0 0;
            z-index: 100;
            box-sizing: border-box;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.2em; font-weight: bold;">
                    {current_conv_name}
                </span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    button_container = st.container()
    with button_container:
        st.markdown(
        """
        <style>
        div[data-testid="stPopover"] > div:first-child {
            background-color: #004aad !important;
            border: 2px solid #004aad !important;
            position: fixed;
            top: 10px;
            right: 20px;
            z-index: 200;
            border-radius: 10px !important;
            color: white !important;
        }
        div[data-testid="stPopover"] > div:first-child * {
            color: white !important;
        }
        div[data-testid="stPopover"] button {
            background-color: rgba(0, 74, 173, 1) !important;
            color: white !important;
            border: 1px solid rgba(255,255,255,0.2) !important;
        }
        div[data-testid="stPopover"] button:hover {
            background-color: rgba(255,255,255,0.2) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
        )
       
        popover = st.popover("•••", help="Menu")
       
        with popover:
            # === Đổi nền ===
            st.markdown("**🎨 Đổi nền**")
            themes = ["Mặc định (Xanh dương)", "Tím hồng", "Cam vàng", "Xanh lá", "Xám bạc"]
            selected = st.selectbox("Chọn nền", themes, index=themes.index(st.session_state.bg_theme) if st.session_state.bg_theme in themes else 0, label_visibility="collapsed")
            if selected != st.session_state.bg_theme:
                st.session_state.bg_theme = selected
                st.rerun()

            st.divider()

            # === Chế độ phản hồi ===
            st.markdown("**Chế độ phản hồi**")
            col_stream, col_instant = st.columns(2)
            with col_stream:
                if st.button("Streaming", type="primary" if st.session_state.streaming_mode else "secondary", use_container_width=True):
                    st.session_state.streaming_mode = True
                    st.rerun()
            with col_instant:
                if st.button("Instant", type="primary" if not st.session_state.streaming_mode else "secondary", use_container_width=True):
                    st.session_state.streaming_mode = False
                    st.rerun()

            st.divider()

            if st.button("🗑️ Xóa đoạn chat", key="delete_chat_button", use_container_width=True, type="secondary"):
                st.session_state.confirm_delete = not st.session_state.get("confirm_delete", False)
                st.rerun()
           
            if st.session_state.get("confirm_delete", False):
                st.warning("Bạn có chắc chắn muốn xóa?")
                col_yes, col_no = st.columns(2)
                with col_yes:
                    if st.button("✅ Có", use_container_width=True, key="confirm_yes"):
                        clear_chat()
                        st.session_state.confirm_delete = False
                        st.rerun()
                with col_no:
                    if st.button("❌ Không", use_container_width=True, key="confirm_no"):
                        st.session_state.confirm_delete = False
                        st.rerun()

            if st.button("➕ Tạo hội thoại mới", key="new_conversation_button", use_container_width=True, type="secondary"):
                existing_ids = {conv["id"] for conv in st.session_state.conversations}
                new_id = 2
                while new_id in existing_ids:
                    new_id += 1
                new_name = f"Thanh niên nghiêm túc {new_id}"
                for conv in st.session_state.conversations:
                    conv["active"] = False
                new_conversation = {
                    "id": new_id,
                    "name": new_name,
                    "messages": [{"role": "ai", "content": "Có cần giúp gì hong?🥱"}],
                    "active": True
                }
                st.session_state.conversations.append(new_conversation)
                st.session_state.current_conversation_id = new_id
                save_conversation_to_file(new_id, new_conversation["messages"])
                st.toast(f"Đã tạo: {new_name} 🎉", icon="✅")
                st.rerun()
           
            if st.button("📋 Danh sách đoạn chat", key="list_conversations_button", use_container_width=True, type="secondary"):
                st.session_state.show_conversation_list = not st.session_state.show_conversation_list
                st.rerun()
           
            if st.session_state.show_conversation_list:
                st.markdown("*Chuyển đến:*")
                for conv in st.session_state.conversations:
                    col_switch, col_delete = st.columns([4, 1])
                    with col_switch:
                        if st.button(f"{'🔵 ' if conv['active'] else '⚪ '}{conv['name']}", key=f"switch_to_{conv['id']}", use_container_width=True, type="secondary" if not conv['active'] else "primary"):
                            for c in st.session_state.conversations:
                                c["active"] = False
                            conv["active"] = True
                            st.session_state.current_conversation_id = conv["id"]
                            st.session_state.show_conversation_list = False
                            st.rerun()
                    with col_delete:
                        if len(st.session_state.conversations) > 1:
                            if st.button("🗑️", key=f"delete_conv_{conv['id']}", help=f"Xóa {conv['name']}", type="secondary"):
                                st.session_state.delete_conv_id = conv["id"]
                                st.rerun()
                        else:
                            st.empty()
                
                if st.session_state.delete_conv_id is not None:
                    conv_to_delete = next((c for c in st.session_state.conversations if c["id"] == st.session_state.delete_conv_id), None)
                    if conv_to_delete:
                        st.divider()
                        st.warning(f"Xóa hoàn toàn '{conv_to_delete['name']}'?")
                        col_yes, col_no = st.columns(2)
                        with col_yes:
                            if st.button("✅ Xóa vĩnh viễn", key="confirm_delete_conv", type="primary"):
                                st.session_state.conversations = [c for c in st.session_state.conversations if c["id"] != st.session_state.delete_conv_id]
                                import os
                                from src.backend.ollama_client import history_path
                                filepath = history_path(f"chat_history_{st.session_state.delete_conv_id}.json")
                                if os.path.exists(filepath):
                                    os.remove(filepath)
                                if conv_to_delete["active"] and st.session_state.conversations:
                                    st.session_state.conversations[0]["active"] = True
                                st.session_state.delete_conv_id = None
                                st.toast(f"Đã xóa: {conv_to_delete['name']}", icon="🗑️")
                                st.rerun()
                        with col_no:
                            if st.button("❌ Hủy bỏ", key="cancel_delete_conv", use_container_width=True):
                                st.session_state.delete_conv_id = None
                                st.rerun()

    st.markdown('<div class="chat-content">', unsafe_allow_html=True)
   
    for message in current_messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
   
    st.markdown('</div>', unsafe_allow_html=True)
   
    if prompt := st.chat_input("Nhắn tin cho Thanh niên nghiêm túc ..."):
        active_conv = None
        for conv in st.session_state.conversations:
            if conv["active"]:
                active_conv = conv
                break
       
        if active_conv:
            active_conv["messages"].append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("ai"):
                with st.spinner(""):
                    if st.session_state.streaming_mode:
                        response_stream = ollama_chat_stream(active_conv["messages"])
                        full_response = st.write_stream(response_stream)
                    else:
                        full_response = ollama_chat(active_conv["messages"])
                        st.markdown(full_response)
           
            active_conv["messages"].append({"role": "ai", "content": full_response})
            save_conversation_to_file(active_conv["id"], active_conv["messages"])
            st.rerun()

def main_ui():
    # === FIXED: Khởi tạo trước khi dùng style ===
    initialize_session_state()
    apply_custom_styles()
    ui()
