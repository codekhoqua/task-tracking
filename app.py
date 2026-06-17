import streamlit as st
import pandas as pd
import requests
from datetime import date
import time
import streamlit.components.v1 as components

# =====================================================================
# 1. CẤU HÌNH TRANG & MÃ CSS GỘP CHUNG (UI CẢI TIẾN)
# =====================================================================
st.set_page_config(page_title="VN-Tracking Dashboard", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
    <style>
        [data-testid="stStatusWidget"], .stDeployButton, [data-testid="stMainMenu"] {display: none !important;}
        header[data-testid="stHeader"] {background-color: transparent !important;}
        .stMainBlockContainer { min-height: 100vh; padding-top: 2rem; }
        div[data-testid="stTabs"] { min-height: 800px; }
        button[data-baseweb="tab"] { font-size: 16px !important; font-weight: 600 !important; }
        .floating-widget { position: fixed; bottom: 20px; right: 20px; z-index: 999999; display: flex; flex-direction: column; align-items: flex-end; font-family: sans-serif; }
        #popup-toggle { display: none; }
        .popup-btn { background-color: #ff4b4b; color: white; padding: 10px 20px; border-radius: 50px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 15px rgba(255,75,75,0.4); text-align: center; transition: 0.3s; user-select: none; }
        .popup-btn:hover { background-color: #ff3333; transform: translateY(-2px); box-shadow: 0 6px 20px rgba(255,75,75,0.6); }
        .popup-iframe-container { display: none; margin-bottom: 15px; width: 420px; height: 550px; border-radius: 16px; overflow: hidden; box-shadow: 0 10px 40px rgba(0,0,0,0.5); background: #0e1117; border: 1px solid #444; }
        #popup-toggle:checked ~ .popup-iframe-container { display: block; animation: fadeUp 0.3s ease; }
        #popup-toggle:checked ~ .popup-btn::after { content: "Đóng Manga App ❌"; }
        #popup-toggle:not(:checked) ~ .popup-btn::after { content: "Mở Manga Translator 🚀"; }
        @keyframes fadeUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
        .theme-switch-wrapper { position: fixed; bottom: 20px; left: 20px; z-index: 999999; box-shadow: 0 4px 10px rgba(0,0,0,0.3); border-radius: 34px; }
        .theme-switch { display: inline-block; height: 34px; position: relative; width: 64px; margin: 0; }
        .theme-switch input { display:none; }
        .theme-slider { background-color: #2b2b2b; bottom: 0; cursor: pointer; left: 0; position: absolute; right: 0; top: 0; transition: .4s; border-radius: 34px; border: 1px solid #555; overflow: hidden; }
        .theme-slider:before { background-color: #fff; bottom: 3px; content: ""; height: 26px; left: 4px; position: absolute; transition: .4s; width: 26px; border-radius: 50%; z-index: 3; box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
        input:checked + .theme-slider { background-color: #e0e0e0; border-color: #bbb; }
        input:checked + .theme-slider:before { transform: translateX(28px); background-color: #222; }
        .icon-theme { position: absolute; top: 5px; font-size: 16px; z-index: 2; }
        .sun-icon { right: 7px; }
        .moon-icon { left: 7px; }
        body:has(#dark-mode-toggle:checked) .stApp { filter: invert(1) hue-rotate(180deg); }
        body:has(#dark-mode-toggle:checked) iframe, body:has(#dark-mode-toggle:checked) img, body:has(#dark-mode-toggle:checked) .popup-btn { filter: invert(1) hue-rotate(180deg);  }
    </style>
""", unsafe_allow_html=True)

# =====================================================================
# 2. CƠ SỞ DỮ LIỆU TÀI KHOẢN VÀ LINK DỮ LIỆU
# =====================================================================
USER_SHEET_URL = "https://docs.google.com/spreadsheets/d/1VLlDF5XoXt0Rz0ACZ3EZRKcKWFnIRXptMPbQthimNE0/export?format=csv&gid=0"

# 🔴🔴🔴 DÁN LINK WEB APP MỚI CỦA BẠN VÀO ĐÂY LÀ ĐỦ: 🔴🔴🔴
CHECKLIST_API_URL = "https://script.google.com/macros/s/AKfycbyguXQno1gohakWqgfTwd0uP-b9BNkkExBcXIe23O267Jr2cXBX2JDSuS0_EVu_uv-7/exec"

@st.cache_data(ttl=60)
def load_users_from_sheet(url):
    try:
        df_users = pd.read_csv(url).dropna(subset=['Username', 'Password'])
        return {str(row.iloc[0]).strip(): {"password": str(row.iloc[1]).strip(), "role": str(row.iloc[2]).strip().lower()} for _, row in df_users.iterrows()}
    except Exception as e:
        return {}

# 🟢 Tính năng đọc dữ liệu Real-time thay cho CSV
@st.cache_data(ttl=2) 
def load_checklist_data(api_url):
    try:
        if api_url == "" or "DÁN_LINK" in api_url: return pd.DataFrame()
        res = requests.get(api_url, timeout=10)
        data = res.json()
        if isinstance(data, list) and len(data) > 0: return pd.DataFrame(data)
        return pd.DataFrame(columns=['Tên Tác Phẩm', 'Checkbox ID', 'Trạng Thái', 'Thời Gian'])
    except Exception as e:
        return pd.DataFrame(columns=['Tên Tác Phẩm', 'Checkbox ID', 'Trạng Thái', 'Thời Gian'])

USER_DB = load_users_from_sheet(USER_SHEET_URL)

if 'lang' not in st.session_state: st.session_state.lang = 'vi'
if 'df_nay_old' not in st.session_state: st.session_state.df_nay_old = None
if 'df_sau_old' not in st.session_state: st.session_state.df_sau_old = None
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_user' not in st.session_state: st.session_state.current_user = None
if 'user_role' not in st.session_state: st.session_state.user_role = None
if 'success_logs' not in st.session_state: st.session_state.success_logs = {}

# =====================================================================
# 3. HỆ THỐNG ĐĂNG NHẬP
# =====================================================================
if not st.session_state.logged_in:
    st.markdown("<br><br><h2 style='text-align: center; color: #0f4c81;'>🔐 Đăng nhập VN-Tracking Dashboard</h2>", unsafe_allow_html=True)
    col_login1, col_login2, col_login3 = st.columns([1, 1, 1])
    with col_login2:
        with st.form("login_form"):
            username = st.selectbox("Tài khoản (Người thực hiện)", options=[""] + list(USER_DB.keys()))
            password = st.text_input("Mật khẩu", type="password")
            submit_login = st.form_submit_button("Đăng nhập", use_container_width=True)
            
            if submit_login:
                if username == "":
                    st.warning("Vui lòng chọn tài khoản!")
                elif username in USER_DB and USER_DB[username]["password"] == password:
                    st.session_state.logged_in = True
                    st.session_state.current_user = username
                    st.session_state.user_role = USER_DB[username]["role"]
                    st.success("Đăng nhập thành công! Đang tải dữ liệu...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Mật khẩu không chính xác!")
    st.stop()

# =====================================================================
# 4. GIAO DIỆN HEADER, SIDEBAR ĐỔI PASS VÀ ĐA NGÔN NGỮ
# =====================================================================
col_logout1, col_logout2 = st.columns([9, 1])
with col_logout1:
    st.info(f"👤 Đang đăng nhập: **{st.session_state.current_user}** | Quyền: **{st.session_state.user_role.upper()}**")
with col_logout2:
    if st.button("🚪 Đăng xuất", use_container_width=True):
        st.session_state.logged_in = False
        st.session_state.current_user = None
        st.session_state.user_role = None
        st.session_state.success_logs = {}
        st.rerun()

CHANGE_PASS_API = "https://script.google.com/macros/s/AKfycbxLWNSqylAHWvkY4JKNvCTpDQMiL2Vgl8_EYEhBI7Ob7OTcIVRXXiJmBQzDa4oNMAVK/exec"

with st.sidebar:
    st.markdown("### 🔑 Đổi mật khẩu")
    with st.form("change_pass_form", clear_on_submit=True):
        old_pass = st.text_input("Mật khẩu cũ", type="password")
        new_pass = st.text_input("Mật khẩu mới", type="password")
        confirm_pass = st.text_input("Xác nhận mật khẩu mới", type="password")
        submit_pass = st.form_submit_button("Lưu thay đổi", use_container_width=True)

        if submit_pass:
            if not old_pass or not new_pass or not confirm_pass:
                st.error("Vui lòng điền đầy đủ thông tin!")
            elif new_pass != confirm_pass:
                st.error("Mật khẩu xác nhận không khớp!")
            elif old_pass != USER_DB[st.session_state.current_user]["password"]:
                st.error("Mật khẩu cũ không chính xác!")
            elif new_pass == old_pass:
                st.warning("Mật khẩu mới phải khác mật khẩu cũ!")
            else:
                with st.spinner("Đang cập nhật mật khẩu..."):
                    try:
                        res = requests.post(CHANGE_PASS_API, json={"username": st.session_state.current_user, "old_password": old_pass, "new_password": new_pass})
                        result = res.json()
                        if result.get("status") == "success":
                            st.success("Đổi mật khẩu thành công!")
                            load_users_from_sheet.clear()
                            USER_DB[st.session_state.current_user]["password"] = new_pass
                        else: st.error(f"Lỗi: {result.get('message')}")
                    except Exception as e:
                        st.error("Lỗi kết nối!")

col_title, col_lang = st.columns([8, 2])
with col_lang:
    st.write("") 
    chon_ngon_ngu = st.selectbox("🌐 Ngôn ngữ / 言語", ["Tiếng Việt", "日本語"], index=0 if st.session_state.lang == 'vi' else 1, label_visibility="collapsed")
    st.session_state.lang = 'vi' if chon_ngon_ngu == "Tiếng Việt" else 'ja'

dict_lang = {
    'vi': {
        'title': "📊 Quản lý tiến độ Team Việt Nam", 'filter_title': "### 🔍 Bộ lọc hiển thị",
        'cv_nay': "Công việc (Tuần Này):", 'nguoi_nay': "Người thực hiện (Tuần Này):",
        'cv_sau': "Công việc (Tuần Sau):", 'nguoi_sau': "Người thực hiện (Tuần Sau):",
        'tab1': "📌 THÔNG TIN TUẦN NÀY", 'tab2': "⏭️ THÔNG TIN TUẦN SAU",
        'time': "🗓️ Thời gian làm việc:", 'deadline': "🚨 DEADLINE CHÚ Ý:",
        'no_filter': "Không có tác phẩm nào khớp với bộ lọc hoặc không có task của bạn!", 'no_task': "Tuần sau hiện chưa có task nào được phân công!",
        'metric_total': "Tổng số Task", 'metric_retouch': "Số task Retouch", 'metric_type': "Số task Lettering",
        'not_update': "Chưa cập nhật",
        'cols': ['Công việc', 'Tên tác phẩm', 'Chương', 'Tập', 'Số trang', 'NXB', 'Ngày bắt đầu', 'Deadline (Nộp)', 'VN', 'Người thực hiện', 'QC Nội bộ', 'Quản lý', 'Trạng thái', 'Bắt đầu', 'Ghi chú'],
        'logtime_title': "⏱️ KHU VỰC BÁO CÁO TIẾN ĐỘ (LOGTIME & CHECKLIST)",
        'logtime_empty': "Hiện không có task nào để logtime.",
        'f_date': "📅 Ngày làm việc:", 'f_cat': "📚 Loại truyện:", 'f_diff': "🔥 Độ khó:", 'f_worker': "👤 Người làm:",
        'f_hours': "⏳ Giờ làm hôm nay:", 'f_pages': "📄 Số page HT (Tổng: {total}):", 'f_note': "📝 Ghi chú thêm:",
        'f_btn': "Lưu Logtime", 'f_warn': "⚠️ Vui lòng nhập số giờ hoặc số trang!", 'f_sync': "⏳ Đang lưu...",
        'f_succ': "✅ Đã lưu: {worker} - {hours}h - {pages}tr.", 'f_err': "❌ Có lỗi xảy ra."
    },
    'ja': {
        'title': "📊 ベトナムチーム進捗管理", 'filter_title': "### 🔍 表示フィルター",
        'cv_nay': "作業内容 (今週):", 'nguoi_nay': "作業者 (今週):",
        'cv_sau': "作業内容 (来週):", 'nguoi_sau': "作業者 (来週):",
        'tab1': "📌 今週の情報", 'tab2': "⏭️ 来週の情報",
        'time': "🗓️ 勤務期間:", 'deadline': "🚨 ご注意の締め切り:",
        'no_filter': "フィルターに一致する作品はありません！", 'no_task': "来週のタスクはまだ割り当てられていません！",
        'metric_total': "表示中のタスク総数", 'metric_retouch': "レタッチタスク数", 'metric_type': "写植タスク数",
        'not_update': "未更新",
        'cols': ['作業内容', '作品名', '話数', '巻数', 'ページ', '出版社', '開始日', '提出日', 'VN', '作業者', '社内QC', '進行管理', 'ステータス', '開始', '備考'],
        'logtime_title': "⏱️ 進捗報告エリア (ログタイム＆チェックリスト)",
        'logtime_empty': "現在、報告するタスクはありません。",
        'f_date': "📅 作業日:", 'f_cat': "📚 カテゴリ:", 'f_diff': "🔥 難易度:", 'f_worker': "👤 作業者:",
        'f_hours': "⏳ 今日の作業時間:", 'f_pages': "📄 完了ページ数 (計: {total}):", 'f_note': "📝 備考:",
        'f_btn': "保存する", 'f_warn': "⚠️ 時間またはページ数を入力してください！", 'f_sync': "⏳ 送信中...",
        'f_succ': "✅ 保存完了: {worker} - {hours}h - {pages}p.", 'f_err': "❌ エラーが発生しました。"
    }
}
t = dict_lang[st.session_state.lang]

with col_title: 
    st.title(t['title'])

# =====================================================================
# 5. CÁC HÀM XỬ LÝ DỮ LIỆU CỐT LÕI
# =====================================================================
url = "https://docs.google.com/spreadsheets/d/1ec_v1hsKu0oCOwyrFNgxckpoaq3Q02J4NdIchqbYE3s/edit?usp=sharing"
csv_url = url.split("/edit")[0] + "/export?format=csv" if "/edit" in url else url

def get_clean_dates(vals_list):
    valid = []
    for v in vals_list:
        v_str = str(v).strip()
        if v_str in ['nan', 'NaN', 'None', ''] or v_str in [':', '->', '-', '=>']: continue
        if 'tuần' not in v_str.lower() and 'deadline' not in v_str.lower() and not v_str.isnumeric() and len(v_str) >= 5: valid.append(v_str)
    return valid

def clean_df(df):
    df = df.dropna(subset=['Công việc', 'Tên tác phẩm'])
    df = df[~df['Công việc'].astype(str).str.contains('Công việc|作業内容', na=False, case=False)]
    df = df[df['Công việc'].astype(str).str.strip() != '']
    return df[~df['Công việc'].astype(str).str.lower().isin(['nan', 'none'])]

def highlight_changes(df_new, df_old):
    if df_old is None or df_new.shape != df_old.shape: return pd.DataFrame('', index=df_new.index, columns=df_new.columns)
    mask = df_new.astype(str).values != df_old.astype(str).values
    return pd.DataFrame([['background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold;' if is_changed else '' for is_changed in row] for row in mask], index=df_new.index, columns=df_new.columns)

def save_logtime(ngay_log, category, cong_viec, tac_pham, chuong, tap, so_trang_tong, nguoi_thuc_hien, so_gio, so_page, difficulty, ghi_chu):
    api_url = "https://script.google.com/macros/s/AKfycbwRgcwRvxBZPOMEyfKbWCDXpLsY1H5edxQtxF4xihgaVIJn-eiqbuDB_2yCU9XYR_MwAQ/exec" 
    payload = { "ngay_log": str(ngay_log), "category": category, "cong_viec": cong_viec, "tac_pham": tac_pham, "chuong": str(chuong) if pd.notna(chuong) else "", "tap": str(tap) if pd.notna(tap) else "", "so_trang_tong": str(so_trang_tong) if pd.notna(so_trang_tong) else "", "nguoi_thuc_hien": str(nguoi_thuc_hien) if pd.notna(nguoi_thuc_hien) else "", "so_gio": so_gio, "so_page": so_page, "difficulty": difficulty, "ghi_chu": ghi_chu }
    try: return requests.post(api_url, json=payload).status_code == 200
    except: return False

def get_checklist_html(tac_pham_key, index, lang, api_url):
    txt = {
        'vi': {
            'step1': 'STEP 1: CHUẨN BỊ', 'step2': 'STEP 2: BẮT ĐẦU', 'step3': 'STEP 3: GIAO HÀNG',
            't1': 'Tạo Task DB_工程管理', 't2': 'N: notion済', 't3': 'Báo bắt đầu', 't4': 'O: 開始 (Bắt đầu)', 't5': 'Not Started → In Progress',
            't6': 'Báo hoàn thành', 't7': 'N: 納品済み', 't8': 'Trạng thái: Delivered',
            'copy_start': '📋 Copy Báo Bắt Đầu', 'ask_task': 'Trễ chỉ thị? (Hỏi Task)', 'copy_ask': '📋 Copy Hỏi Task',
            'copy_done': '📋 Copy Báo Hoàn Thành', 'copied': '✅ Đã Copy', 'copy_deliver': '📋 Copy Báo Giao Hàng'
        },
        'ja': {
            'step1': 'STEP 1: 準備', 'step2': 'STEP 2: 着手', 'step3': 'STEP 3: 納品',
            't1': 'DB_工程管理に作成', 't2': 'N列：notion済', 't3': '着手報告 (Asana)', 't4': 'O列：開始', 't5': 'Not Started → In Progress',
            't6': '完了報告 (Asana)', 't7': 'N列：納品済み', 't8': 'ステータス：Delivered',
            'copy_start': '📋 着手報告コピー', 'ask_task': '指示遅れ？', 'copy_ask': '📋 確認文コピー',
            'copy_done': '📋 完了報告コピー', 'copied': '✅ コピー完了', 'copy_deliver': '📋 納品メッセージコピー'
        }
    }
    l = txt[lang]
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <style>
            :root {{ --primary: #0f4c81; --bg: #f8f9fa; --text: #2c3e50; }}
            * {{ box-sizing: border-box; font-family: 'Segoe UI', system-ui, sans-serif; }}
            body {{ background: transparent; color: var(--text); padding: 5px; margin: 0; overflow: hidden; }}
            
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 18px; width: 100%; align-items: stretch; }}
            .step-col {{ 
                background: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; padding: 14px; 
                height: 100%; display: flex; flex-direction: column; 
                box-shadow: 0 4px 10px rgba(0,0,0,0.03); transition: transform 0.2s, box-shadow 0.2s;
            }}
            .step-col:hover {{ transform: translateY(-2px); box-shadow: 0 8px 15px rgba(0,0,0,0.08); border-color: #cbd5e1; }}
            .step-header {{ font-size: 12px; font-weight: 800; color: #16a34a; margin-bottom: 12px; border-bottom: 2px solid #f1f5f9; padding-bottom: 6px; text-transform: uppercase; letter-spacing: 0.5px; }}
            
            .task-row {{ display: flex; align-items: flex-start; gap: 10px; margin-bottom: 8px; padding: 4px 0; flex-wrap: wrap; }}
            .badge {{ font-size: 9px; padding: 3px 6px; border-radius: 4px; color: #fff; font-weight: bold; width: 52px; text-align: center; flex-shrink: 0; letter-spacing: 0.2px; }}
            .notion {{ background: #000; }} .sheet {{ background: #107c41; }} .asana {{ background: #fc636b; }}
            
            .check-wrapper {{ position: relative; cursor: pointer; flex-grow: 1; display: flex; align-items: center; min-height: 20px; }}
            .check-wrapper input {{ display: none; }}
            .action-text {{ font-size: 11.5px; margin-left: 24px; transition: 0.2s; line-height: 1.3; font-weight: 500; color: #334155; }}
            .checkmark {{ position: absolute; top: 1px; left: 0; width: 16px; height: 16px; background: #f8fafc; border-radius: 4px; border: 1.5px solid #cbd5e1; transition: 0.2s; }}
            
            .check-wrapper:hover .checkmark {{ border-color: #94a3b8; background: #f1f5f9; }}
            .check-wrapper input:checked ~ .checkmark {{ background: #22c55e; border-color: #22c55e; }}
            .check-wrapper input:checked ~ .checkmark:after {{ content: ""; position: absolute; display: block; left: 5px; top: 1px; width: 3px; height: 8px; border: solid white; border-width: 0 2px 2px 0; transform: rotate(45deg); }}
            .check-wrapper input:checked ~ .action-text {{ text-decoration: line-through; color: #94a3b8; font-weight: 400; }}
            
            .snippet-box {{ background: #f8fafc; border: 1px dashed #cbd5e1; padding: 6px 8px; border-radius: 6px; font-family: monospace; font-size: 9.5px; color: #475569; white-space: pre-line; margin-bottom: 6px; margin-left: 62px; line-height: 1.4; }}
            .btn-copy {{ display: inline-flex; align-items: center; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 4px 8px; border-radius: 6px; font-size: 9.5px; cursor: pointer; color: #0f4c81; font-weight: 600; margin-left: 62px; margin-bottom: 10px; transition: 0.2s; }}
            .btn-copy:hover {{ background: #e2e8f0; border-color: #94a3b8; color: #000; }}
            .btn-copy.success {{ background: #22c55e; color: white; border-color: #16a34a; }}
            
            summary {{ font-size: 10.5px; font-weight: 600; color: #d97706; cursor: pointer; margin-left: 62px; margin-bottom: 6px; user-select: none; transition: 0.2s; }}
            summary:hover {{ color: #b45309; }}
        </style>
    </head>
    <body>
        <div class="grid-container">
            <div class="step-col">
                <div class="step-header">{l['step1']}</div>
                <div class="task-row"><span class="badge notion">Notion</span><label class="check-wrapper"><input type="checkbox" id="t1_{index}"><span class="checkmark"></span><div class="action-text">{l['t1']}</div></label></div>
                <div class="task-row"><span class="badge sheet">Sheet</span><label class="check-wrapper"><input type="checkbox" id="t2_{index}"><span class="checkmark"></span><div class="action-text">{l['t2']}</div></label></div>
            </div>
            
            <div class="step-col">
                <div class="step-header">{l['step2']}</div>
                <div class="task-row"><span class="badge asana">Asana</span><label class="check-wrapper"><input type="checkbox" id="t3_{index}"><span class="checkmark"></span><div class="action-text">{l['t3']}</div></label></div>
                <div class="snippet-box" id="msg_t3_{index}">(PC) cc @Shiori Fujimura @Miho Osada @Erika Kawasaki\n===タスク着手===</div>
                <button class="btn-copy" onclick="copyText(this, 'msg_t3_{index}')">{l['copy_start']}</button>
                <details><summary>{l['ask_task']}</summary><div class="snippet-box" id="jp_t3_{index}">お疲れ様です。\n写植工程を担当しております○○です。\n本日が作業開始日となっておりますが、現時点でまだご指示をいただいておりません。\nお手数をおかけいたしますが、ご確認のほどよろしくお願いいたします。</div><button class="btn-copy" onclick="copyText(this, 'jp_t3_{index}')">{l['copy_ask']}</button></details>
                <div class="task-row"><span class="badge sheet">Sheet</span><label class="check-wrapper"><input type="checkbox" id="t4_{index}"><span class="checkmark"></span><div class="action-text">{l['t4']}</div></label></div>
                <div class="task-row"><span class="badge notion">Notion</span><label class="check-wrapper"><input type="checkbox" id="t5_{index}"><span class="checkmark"></span><div class="action-text">{l['t5']}</div></label></div>
            </div>

            <div class="step-col">
                <div class="step-header">{l['step3']}</div>
                <div class="task-row"><span class="badge asana">Asana</span><label class="check-wrapper"><input type="checkbox" id="t6_{index}"><span class="checkmark"></span><div class="action-text">{l['t6']}</div></label></div>
                <div class="snippet-box" id="msg_t6_{index}">(PC) cc @Shiori Fujimura @Miho Osada @Erika Kawasaki\n===タスク完了===</div>
                <button class="btn-copy" onclick="copyText(this, 'msg_t6_{index}')">{l['copy_done']}</button>
                <div class="task-row"><span class="badge sheet">Sheet</span><label class="check-wrapper"><input type="checkbox" id="t7_{index}"><span class="checkmark"></span><div class="action-text">{l['t7']}</div></label></div>
                <div class="task-row"><span class="badge notion">Notion</span><label class="check-wrapper"><input type="checkbox" id="t8_{index}"><span class="checkmark"></span><div class="action-text">{l['t8']}</div></label></div>
                <div class="snippet-box" id="msg_t8_{index}">納品いたしました。\nご確認のほどよろしくお願いいたします。</div>
                <button class="btn-copy" onclick="copyText(this, 'msg_t8_{index}')">{l['copy_deliver']}</button>
            </div>
        </div>
        
        <script>
            function copyText(btn, id) {{
                const text = document.getElementById(id).textContent;
                navigator.clipboard.writeText(text).then(() => {{
                    const oldText = btn.innerText;
                    btn.innerText = "{l['copied']}";
                    btn.classList.add("success");
                    setTimeout(() => {{ btn.innerText = oldText; btn.classList.remove("success"); }}, 2000);
                }});
            }}
            
            const tpKey = "{tac_pham_key}";
            
            // Link API đã được đồng bộ tự động từ code Python xuống đây!
            const API_URL = "{api_url}";
            
            const checks = document.querySelectorAll('input[type="checkbox"]');
            
            checks.forEach(cb => {{
                const rawId = cb.id.split('_')[0]; 
                const storageKey = tpKey + "_" + rawId;
                if (localStorage.getItem(storageKey) === 'true') cb.checked = true;
                
                cb.addEventListener('change', async (e) => {{
                    const isChecked = e.target.checked;
                    localStorage.setItem(storageKey, isChecked);
                    if(API_URL.startsWith("http")) {{
                        fetch(API_URL, {{ method: "POST", mode: "no-cors", headers: {{ "Content-Type": "text/plain;charset=utf-8" }}, body: JSON.stringify({{ tac_pham: tpKey, checkbox_id: rawId, status: isChecked }}) }});
                    }}
                }});
            }});
            
            if(API_URL.startsWith("http")) {{
                fetch(API_URL + "?tac_pham=" + encodeURIComponent(tpKey))
                .then(res => res.json())
                .then(data => {{
                    checks.forEach(cb => {{
                        const rawId = cb.id.split('_')[0];
                        if(data[rawId] !== undefined) {{
                            cb.checked = (data[rawId] === true || data[rawId] === "true");
                            localStorage.setItem(tpKey + "_" + rawId, cb.checked);
                        }}
                    }});
                }});
            }}
        </script>
    </body>
    </html>
    """

# =====================================================================
# 6. RENDER DỮ LIỆU & ÁP DỤNG QUYỀN (ROLE-BASED)
# =====================================================================
@st.fragment(run_every="30s")
def render_realtime_dashboard():
    try: df_raw = pd.read_csv(csv_url, usecols=list(range(1, 16)), header=None)
    except:
        st.error("Lỗi tải dữ liệu chính.")
        return
        
    df_raw.columns = ['Công việc', 'Tên tác phẩm', 'Chương', 'Tập', 'Số trang', 'NXB', 'Ngày bắt đầu', 'Deadline (Nộp)', 'VN', 'Người thực hiện', 'QC Nội bộ', 'Quản lý', 'Trạng thái', 'Bắt đầu', 'Ghi chú']
    idx_tuan = df_raw[df_raw.apply(lambda row: row.astype(str).str.contains('Tuần làm việc', case=False, na=False).any(), axis=1)].index

    thong_tin_tuan_nay = {"start": t['not_update'], "end": t['not_update'], "deadline": t['not_update']}
    thong_tin_tuan_sau = {"start": t['not_update'], "end": t['not_update'], "deadline": t['not_update']}

    for idx_list, info_dict in [(idx_tuan[:1], thong_tin_tuan_nay), (idx_tuan[1:2], thong_tin_tuan_sau)]:
        if len(idx_list) > 0:
            start_idx = idx_list[0]
            for i in range(start_idx, min(start_idx + 5, len(df_raw))):
                row_vals = df_raw.iloc[i].dropna().astype(str).str.strip().tolist()
                dates = get_clean_dates(row_vals)
                if any('tuần' in str(v).lower() for v in row_vals) and len(dates) >= 2:
                    info_dict['start'], info_dict['end'] = dates[0], dates[1]
                if any('deadline' in str(v).lower() for v in row_vals) and len(dates) >= 1:
                    info_dict['deadline'] = dates[-1]

    df_tuan_nay = clean_df(df_raw.iloc[idx_tuan[0]:idx_tuan[1]].copy()) if len(idx_tuan) > 1 else clean_df(df_raw.iloc[idx_tuan[0]:].copy()) if len(idx_tuan) > 0 else df_raw.copy()
    df_tuan_sau = clean_df(df_raw.iloc[idx_tuan[1]:].copy()) if len(idx_tuan) > 1 else pd.DataFrame(columns=df_raw.columns)

    if st.session_state.user_role == "member":
        df_tuan_nay = df_tuan_nay[df_tuan_nay["Người thực hiện"].astype(str).str.contains(st.session_state.current_user, na=False, regex=False)]
        df_tuan_sau = df_tuan_sau[df_tuan_sau["Người thực hiện"].astype(str).str.contains(st.session_state.current_user, na=False, regex=False)]

    st.write(t['filter_title'])
    col_f1, col_f2 = st.columns(2)
    with col_f1:
        cv_nay = st.multiselect(t['cv_nay'], options=df_tuan_nay["Công việc"].dropna().unique())
        nguoi_nay = st.multiselect(t['nguoi_nay'], options=list(USER_DB.keys())) if st.session_state.user_role == "leader" else []
    with col_f2:
        cv_sau = st.multiselect(t['cv_sau'], options=df_tuan_sau["Công việc"].dropna().unique())
        nguoi_sau = st.multiselect(t['nguoi_sau'], options=list(USER_DB.keys())) if st.session_state.user_role == "leader" else []

    df_nay_f = df_tuan_nay[df_tuan_nay["Công việc"].isin(cv_nay)] if cv_nay else df_tuan_nay
    if nguoi_nay: df_nay_f = df_nay_f[df_nay_f["Người thực hiện"].astype(str).str.contains('|'.join(nguoi_nay), na=False, regex=True)]
    
    df_sau_f = df_tuan_sau[df_tuan_sau["Công việc"].isin(cv_sau)] if cv_sau else df_tuan_sau
    if nguoi_sau: df_sau_f = df_sau_f[df_sau_f["Người thực hiện"].astype(str).str.contains('|'.join(nguoi_sau), na=False, regex=True)]

    tab_names = [t['tab1'], t['tab2']]
    if st.session_state.user_role == "leader": 
        tab_names.append("👑 BẢNG ĐIỀU KHIỂN (LEADER)")
    
    tabs = st.tabs(tab_names)

    # === TAB 1: TUẦN NÀY ===
    with tabs[0]:
        st.info(f"**{t['time']}** {thong_tin_tuan_nay['start']} ➡️ {thong_tin_tuan_nay['end']} &nbsp;&nbsp;|&nbsp;&nbsp; **{t['deadline']}** {thong_tin_tuan_nay['deadline']}")
        if df_nay_f.empty: st.warning(t['no_filter'])
        else:
            df_display = df_nay_f.copy()
            df_display.columns = t['cols']
            st.dataframe(df_display.style.apply(lambda _: highlight_changes(df_display, st.session_state.df_nay_old), axis=None), use_container_width=True, hide_index=True)
            st.session_state.df_nay_old = df_display.copy()
            
            with st.container(border=True):
                c1, c2, c3 = st.columns(3)
                c1.metric(t['metric_total'], len(df_nay_f))
                c2.metric(t['metric_retouch'], len(df_nay_f[df_nay_f["Công việc"] == "レタッチ"]))
                c3.metric(t['metric_type'], len(df_nay_f[df_nay_f["Công việc"] == "写植"]))

        st.markdown("---")
        st.subheader(t['logtime_title'])
        if df_nay_f.empty: st.info(t['logtime_empty'])
        else:
            for index, row in df_nay_f.iterrows():
                tp_name = str(row['Công việc']).strip() + " - " + str(row['Tên tác phẩm']).strip()
                worker_name = str(row['Người thực hiện']).strip()
                
                with st.expander(f"📝 {tp_name}  |  👤 {worker_name}"):
                    # Đưa thẳng CHECKLIST_API_URL từ trên đầu xuống đây
                    components.html(get_checklist_html(tp_name, index, st.session_state.lang, CHECKLIST_API_URL), height=340, scrolling=False)
                    
                    with st.form(key=f"form_log_{index}"):
                        c_cat, c_diff, c_worker, c_date = st.columns([1.5, 1.5, 2, 1.5])
                        with c_cat: loai_truyen = st.selectbox(t['f_cat'], ["単行本", "読切", "連載"], index=0, key=f"cat_{index}")
                        with c_diff: do_kho = st.selectbox(t['f_diff'], ["", "低", "中", "高"], index=0, key=f"diff_{index}")
                        with c_worker:
                            workers = list(USER_DB.keys())
                            if pd.notna(worker_name) and worker_name and worker_name not in workers: workers.append(worker_name)
                            nguoi_lam_final = st.selectbox(t['f_worker'], workers, index=workers.index(worker_name) if worker_name in workers else 0, key=f"sel_worker_{index}")
                        with c_date: ngay_log = st.date_input(t['f_date'], value=date.today(), key=f"date_{index}")

                        col1, col2, col3 = st.columns([2, 2, 4])
                        with col1: so_gio = st.number_input(t['f_hours'], min_value=0.0, step=0.5, key=f"gio_{index}")
                        with col2: so_page = st.number_input(t['f_pages'].format(total=row['Số trang'] if pd.notna(row['Số trang']) else 0), min_value=0, step=1, key=f"page_{index}")
                        with col3: ghi_chu_log = st.text_input(t['f_note'], key=f"note_{index}")
                        
                        sub_c, msg_c = st.columns([2, 8])
                        with sub_c: submit_btn = st.form_submit_button(t['f_btn'])
                            
                        if submit_btn:
                            with msg_c: 
                                if so_gio == 0 and so_page == 0: st.warning(t['f_warn'])
                                else:
                                    with st.spinner(t['f_sync']):
                                        if save_logtime(ngay_log, loai_truyen, row['Công việc'], row['Tên tác phẩm'], row['Chương'], row['Tập'], row['Số trang'], nguoi_lam_final, so_gio, so_page, do_kho, ghi_chu_log): 
                                            msg = t['f_succ'].format(worker=nguoi_lam_final, hours=so_gio, pages=so_page)
                                            st.session_state.success_logs[index] = msg
                                            st.success(msg)
                                        else: st.error(t['f_err'])
                        elif index in st.session_state.success_logs:
                            with msg_c: st.success(st.session_state.success_logs[index])

    # === TAB 2: TUẦN SAU ===
    with tabs[1]:
        st.info(f"**{t['time']}** {thong_tin_tuan_sau['start']} ➡️ {thong_tin_tuan_sau['end']} &nbsp;&nbsp;|&nbsp;&nbsp; **{t['deadline']}** {thong_tin_tuan_sau['deadline']}")
        if df_sau_f.empty: st.warning(t['no_task'])
        else:
            df_display = df_sau_f.copy()
            df_display.columns = t['cols']
            st.dataframe(df_display.style.apply(lambda _: highlight_changes(df_display, st.session_state.df_sau_old), axis=None), use_container_width=True, hide_index=True)
            st.session_state.df_sau_old = df_display.copy()
            with st.container(border=True):
                c4, c5, c6 = st.columns(3)
                c4.metric(t['metric_total'], len(df_sau_f))
                c5.metric(t['metric_retouch'], len(df_sau_f[df_sau_f["Công việc"] == "レタッチ"]))
                c6.metric(t['metric_type'], len(df_sau_f[df_sau_f["Công việc"] == "写植"]))

    # === TAB 3: DASHBOARD LEADER ===
    if st.session_state.user_role == "leader":
        with tabs[2]:
            c_head1, c_head2 = st.columns([8, 2])
            with c_head1:
                st.subheader("📊 Bảng Theo Dõi Tiến Độ Checklist (Theo Thời Gian Thực)")
            with c_head2:
                if st.button("🔄 Làm mới dữ liệu", use_container_width=True):
                    load_checklist_data.clear()
            
            df_check = load_checklist_data(CHECKLIST_API_URL)
            
            if df_check.empty:
                st.warning("⚠️ Chưa có dữ liệu Checklist. Đang chờ đồng bộ...")
            else:
                df_check['Trạng Thái'] = df_check['Trạng Thái'].astype(str).str.upper().isin(['TRUE', '1', 'T'])
                df_check_latest = df_check.drop_duplicates(subset=['Tên Tác Phẩm', 'Checkbox ID'], keep='last')

                dashboard_data = []
                for _, row in df_nay_f.iterrows():
                    tp_name = str(row['Công việc']).strip() + " - " + str(row['Tên tác phẩm']).strip()
                    worker = str(row['Người thực hiện']).strip()
                    
                    task_checks = df_check_latest[df_check_latest['Tên Tác Phẩm'] == tp_name]
                    checked_count = task_checks[task_checks['Trạng Thái'] == True]['Checkbox ID'].nunique()
                    
                    if checked_count == 0: status = "⏳ Chưa Bắt Đầu"
                    elif checked_count == 8: status = "✅ Đã Giao Hàng"
                    else: status = "🔥 Đang Tiến Hành"
                    
                    progress = int((checked_count / 8) * 100)
                    dashboard_data.append({
                        "Tên Tác Phẩm": tp_name,
                        "Người Thực Hiện": worker,
                        "Tiến Độ (%)": progress,
                        "Trạng Thái": status
                    })
                
                df_dash = pd.DataFrame(dashboard_data)
                st.dataframe(
                    df_dash,
                    column_config={
                        "Tiến Độ (%)": st.column_config.ProgressColumn(
                            "Tiến Độ (%)",
                            help="Tỷ lệ hoàn thành dựa trên số lượng checkbox đã đánh dấu",
                            format="%d%%",
                            min_value=0,
                            max_value=100,
                        ),
                    },
                    hide_index=True,
                    use_container_width=True
                )

# GỌI HÀM RENDER
render_realtime_dashboard()
