import streamlit as st
import pandas as pd

# Cấu hình trang web
st.set_page_config(page_title="VN-Tracking Dashboard", layout="wide")

# ---- MÃ CSS GỘP CHUNG: CHỐNG SỤT LÚN, POPUP VÀ DARKMODE GÓC TRÁI ----
st.markdown("""
    <style>
        /* 1. Ẩn các nút rác của Streamlit */
        [data-testid="stStatusWidget"], .stDeployButton, header[data-testid="stHeader"] {display: none !important;}
        
        /* 2. Chuyển Running xuống góc dưới bên trái (Nhấc lên 70px nhường chỗ cho công tắc) */
        [data-testid="stSpinner"] {
            position: fixed !important; bottom: 70px !important; left: 20px !important; z-index: 99999 !important;
            background-color: var(--secondary-background-color); border-radius: 8px; padding: 5px 15px; width: fit-content !important;
        }
        
        /* 3. KHÓA CỨNG CHIỀU CAO TRÁNH GIẬT MÀN HÌNH */
        .stMainBlockContainer { min-height: 100vh; }
        div[data-testid="stTabs"] { min-height: 800px; }
        
        /* 4. CSS CHO POPUP MANGA APP Ở GÓC DƯỚI BÊN PHẢI */
        .floating-widget {
            position: fixed; bottom: 20px; right: 20px; z-index: 999999; 
            display: flex; flex-direction: column; align-items: flex-end; font-family: sans-serif;
        }
        #popup-toggle { display: none; }
        .popup-btn {
            background-color: #ff4b4b; color: white; padding: 10px 20px; border-radius: 50px; cursor: pointer;
            font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.3); text-align: center; transition: 0.3s; user-select: none;
        }
        .popup-btn:hover { background-color: #ff3333; transform: scale(1.05); }
        .popup-iframe-container {
            display: none; margin-bottom: 15px; width: 420px; height: 550px; border-radius: 12px;
            overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); background: #0e1117; border: 1px solid #444;
        }
        #popup-toggle:checked ~ .popup-iframe-container { display: block; }
        #popup-toggle:checked ~ .popup-btn::after { content: "Đóng Manga App ❌"; }
        #popup-toggle:not(:checked) ~ .popup-btn::after { content: "Mở Manga Translator 🚀"; }
        
        /* 5. CSS CHO CÔNG TẮC DARK/LIGHT MODE GÓC TRÁI DƯỚI */
        .theme-switch-wrapper {
            position: fixed; bottom: 20px; left: 20px; z-index: 999999;
            box-shadow: 0 4px 10px rgba(0,0,0,0.3); border-radius: 34px;
        }
        .theme-switch {
            display: inline-block; height: 34px; position: relative; width: 64px; margin: 0;
        }
        .theme-switch input { display:none; }
        .theme-slider {
            background-color: #2b2b2b; bottom: 0; cursor: pointer; left: 0; position: absolute; right: 0; top: 0; 
            transition: .4s; border-radius: 34px; border: 1px solid #555; overflow: hidden;
        }
        .theme-slider:before {
            background-color: #fff; bottom: 3px; content: ""; height: 26px; left: 4px; position: absolute; 
            transition: .4s; width: 26px; border-radius: 50%; z-index: 3; box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        }
        input:checked + .theme-slider { background-color: #e0e0e0; border-color: #bbb; }
        input:checked + .theme-slider:before { transform: translateX(28px); background-color: #222; }
        .icon-theme { position: absolute; top: 5px; font-size: 16px; z-index: 2; }
        .sun-icon { right: 7px; }
        .moon-icon { left: 7px; }
        
        /* Hắc ma pháp Invert Màu Giao Diện */
        body:has(#dark-mode-toggle:checked) .stApp {
            filter: invert(1) hue-rotate(180deg);
        }
        /* Bảo vệ hình ảnh, nút popup và iframe Manga App không bị lộn màu */
        body:has(#dark-mode-toggle:checked) iframe,
        body:has(#dark-mode-toggle:checked) img,
        body:has(#dark-mode-toggle:checked) .popup-btn {
            filter: invert(1) hue-rotate(180deg); 
        }
    </style>

    <div class="floating-widget">
        <input type="checkbox" id="popup-toggle">
        <div class="popup-iframe-container">
            <iframe src="https://manga-deepseek-grok-9cmlbuigomauxjg9st4jfd.streamlit.app/?embed=true" width="100%" height="100%" frameborder="0"></iframe>
        </div>
        <label for="popup-toggle" class="popup-btn"></label>
    </div>
    
    <div class="theme-switch-wrapper" title="Đổi giao diện Sáng/Tối">
        <label class="theme-switch" for="dark-mode-toggle">
            <input type="checkbox" id="dark-mode-toggle">
            <div class="theme-slider">
                <span class="icon-theme sun-icon">☀️</span>
                <span class="icon-theme moon-icon">🌙</span>
            </div>
        </label>
    </div>
""", unsafe_allow_html=True)

# ---- CẤU HÌNH ĐA NGÔN NGỮ & LƯU TRỮ TRẠNG THÁI (CACHE) ----
if 'lang' not in st.session_state: st.session_state.lang = 'vi'
if 'df_nay_old' not in st.session_state: st.session_state.df_nay_old = None
if 'df_sau_old' not in st.session_state: st.session_state.df_sau_old = None

# Bố cục nút chọn ngôn ngữ
col_title, col_lang = st.columns([8, 2])

with col_lang:
    st.write("") 
    chon_ngon_ngu = st.selectbox(
        "🌐 Ngôn ngữ / 言語", 
        ["Tiếng Việt", "日本語"], 
        index=0 if st.session_state.lang == 'vi' else 1
    )
    st.session_state.lang = 'vi' if chon_ngon_ngu == "Tiếng Việt" else 'ja'

# Từ điển Dịch thuật
dict_lang = {
    'vi': {
        'title': "📊 Quản lý tiến độ Team Việt Nam",
        'filter_title': "### 🔍 Bộ lọc hiển thị",
        'cv_nay': "Công việc (Tuần Này):",
        'nguoi_nay': "Người thực hiện (Tuần Này):",
        'cv_sau': "Công việc (Tuần Sau):",
        'nguoi_sau': "Người thực hiện (Tuần Sau):",
        'tab1': "📌 THÔNG TIN TUẦN NÀY",
        'tab2': "⏭️ THÔNG TIN TUẦN SAU",
        'time': "🗓️ Thời gian làm việc:",
        'deadline': "🚨 DEADLINE CHÚ Ý:",
        'no_filter': "Không có tác phẩm nào khớp với bộ lọc!",
        'no_task': "Tuần sau hiện chưa có task nào được phân công!",
        'metric_total': "Tổng số Task đang hiển thị",
        'metric_retouch': "Số task Retouch (レタッチ)",
        'metric_type': "Số task Lettering (写植)",
        'not_update': "Chưa cập nhật",
        'cols': ['Công việc', 'Tên tác phẩm', 'Chương', 'Tập', 'Số trang', 'NXB', 'Ngày bắt đầu', 'Deadline (Nộp)', 'VN', 'Người thực hiện', 'QC Nội bộ', 'Quản lý', 'Trạng thái', 'Bắt đầu', 'Ghi chú']
    },
    'ja': {
        'title': "📊 ベトナムチーム進捗管理",
        'filter_title': "### 🔍 表示フィルター",
        'cv_nay': "作業内容 (今週):",
        'nguoi_nay': "作業者 (今週):",
        'cv_sau': "作業内容 (来週):",
        'nguoi_sau': "作業者 (来週):",
        'tab1': "📌 今週の情報",
        'tab2': "⏭️ 来週の情報",
        'time': "🗓️ 勤務期間:",
        'deadline': "🚨 ご注意の締め切り:",
        'no_filter': "フィルターに一致する作品はありません！",
        'no_task': "来週のタスクはまだ割り当てられていません！",
        'metric_total': "表示中のタスク総数",
        'metric_retouch': "レタッチタスク数",
        'metric_type': "写植タスク数",
        'not_update': "未更新",
        'cols': ['作業内容', '作品名', '話数', '巻数', 'ページ', '出版社', '開始日', '提出日', 'VN', '作業者', '社内QC', '進行管理', 'ステータス', '開始', '備考']
    }
}

t = dict_lang[st.session_state.lang]

with col_title:
    st.title(t['title'])

# 🚨 CHỈ CẦN DÁN LINK SHARE BÌNH THƯỜNG VÀO ĐÂY
url = "https://docs.google.com/spreadsheets/d/1ec_v1hsKu0oCOwyrFNgxckpoaq3Q02J4NdIchqbYE3s/edit?usp=sharing"

# Biến hình link Share thành link CSV
if "/edit" in url:
    csv_url = url.split("/edit")[0] + "/export?format=csv"
else:
    csv_url = url

# --- CÁC HÀM BỔ TRỢ XỬ LÝ DỮ LIỆU ---
def get_clean_dates(vals_list):
    valid = []
    for v in vals_list:
        v_str = str(v).strip()
        if v_str in ['nan', 'NaN', 'None', '']: continue
        v_lower = v_str.lower()
        if v_str in [':', '->', '-', '=>']: continue
        if 'tuần làm việc' in v_lower or 'deadline' in v_lower or 'số tác phẩm' in v_lower: continue
        if v_str.isnumeric() or len(v_str) < 5: continue
        valid.append(v_str)
    return valid

def clean_df(df):
    df = df.dropna(subset=['Công việc', 'Tên tác phẩm'])
    df = df[~df['Công việc'].astype(str).str.contains('Công việc|作業内容', na=False, case=False)]
    df = df[~df['Tên tác phẩm'].astype(str).str.contains('Tên tác phẩm|作品名|Tuần làm việc|Số tác phẩm', na=False, case=False)]
    df = df[df['Công việc'].astype(str).str.strip() != '']
    df = df[~df['Công việc'].astype(str).str.lower().isin(['nan', 'none'])]
    return df

def highlight_changes(df_new, df_old):
    if df_old is None or df_new.shape != df_old.shape:
        return pd.DataFrame('', index=df_new.index, columns=df_new.columns)
    
    mask = df_new.astype(str).values != df_old.astype(str).values
    style_list = []
    for row in mask:
        style_row = []
        for is_changed in row:
            if is_changed:
                style_row.append('background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold;')
            else:
                style_row.append('')
        style_list.append(style_row)
        
    return pd.DataFrame(style_list, index=df_new.index, columns=df_new.columns)

# --- TẠO VÙNG CHẠY ĐỘC LẬP MỖI 10 GIÂY ---
@st.fragment(run_every="10s")
def render_realtime_dashboard():
    try:
        df_raw = pd.read_csv(csv_url, usecols=list(range(1, 16)), header=None)
    except Exception as e:
        st.error("Lỗi tải dữ liệu. Hãy đảm bảo file Sheet đã bật quyền Share 'Anyone with the link'.")
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
                if any('tuần làm việc' in str(v).lower() for v in row_vals):
                    dates = get_clean_dates(row_vals)
                    if len(dates) >= 1: info_dict['start'] = dates[0]
                    if len(dates) >= 2: info_dict['end'] = dates[1]
                if any('deadline' in str(v).lower() for v in row_vals):
                    dates = get_clean_dates(row_vals)
                    if len(dates) >= 1: info_dict['deadline'] = dates[-1]

    if len(idx_tuan) > 1:
        df_tuan_nay = clean_df(df_raw.iloc[idx_tuan[0]:idx_tuan[1]].copy())
        df_tuan_sau = clean_df(df_raw.iloc[idx_tuan[1]:].copy())
    else:
        df_tuan_nay = clean_df(df_raw.iloc[idx_tuan[0]:].copy()) if len(idx_tuan) > 0 else df_raw.copy()
        df_tuan_sau = pd.DataFrame(columns=df_raw.columns)

    # ---- BỘ LỌC DỊCH THUẬT ĐA NGÔN NGỮ ----
    st.write(t['filter_title'])
    col_filter1, col_filter2 = st.columns(2)
    
    with col_filter1:
        cv_nay_list = df_tuan_nay["Công việc"].dropna().unique()
        mac_dinh_nay = [cv for cv in ["レタッチ", "写植"] if cv in cv_nay_list]
        cv_nay = st.multiselect(t['cv_nay'], options=cv_nay_list, default=mac_dinh_nay)
        nguoi_nay = st.multiselect(t['nguoi_nay'], options=df_tuan_nay["Người thực hiện"].dropna().unique())
        
    with col_filter2:
        cv_sau_list = df_tuan_sau["Công việc"].dropna().unique()
        mac_dinh_sau = [cv for cv in ["レタッチ", "写植"] if cv in cv_sau_list]
        cv_sau = st.multiselect(t['cv_sau'], options=cv_sau_list, default=mac_dinh_sau)
        nguoi_sau = st.multiselect(t['nguoi_sau'], options=df_tuan_sau["Người thực hiện"].dropna().unique())

    df_nay_filtered = df_tuan_nay[df_tuan_nay["Công việc"].isin(cv_nay)] if cv_nay else df_tuan_nay
    if nguoi_nay: df_nay_filtered = df_nay_filtered[df_nay_filtered["Người thực hiện"].isin(nguoi_nay)]

    df_sau_filtered = df_tuan_sau[df_tuan_sau["Công việc"].isin(cv_sau)] if cv_sau else df_tuan_sau
    if nguoi_sau: df_sau_filtered = df_sau_filtered[df_sau_filtered["Người thực hiện"].isin(nguoi_sau)]

    # ---- HIỂN THỊ DỮ LIỆU TABS ----
    tab1, tab2 = st.tabs([t['tab1'], t['tab2']])

    with tab1:
        st.info(f"**{t['time']}** {thong_tin_tuan_nay['start']} ➡️ {thong_tin_tuan_nay['end']} &nbsp;&nbsp;|&nbsp;&nbsp; **{t['deadline']}** {thong_tin_tuan_nay['deadline']}")
        if df_nay_filtered.empty:
            st.warning(t['no_filter'])
        else:
            df_nay_display = df_nay_filtered.copy()
            df_nay_display.index = range(1, len(df_nay_display) + 1)
            df_nay_display.columns = t['cols']
            
            df_nay_styled = df_nay_display.style.apply(lambda _: highlight_changes(df_nay_display, st.session_state.df_nay_old), axis=None)
            st.dataframe(df_nay_styled, use_container_width=True)
            st.session_state.df_nay_old = df_nay_display.copy()
            
            c1, c2, c3 = st.columns(3)
            c1.metric(t['metric_total'], len(df_nay_filtered))
            c2.metric(t['metric_retouch'], len(df_nay_filtered[df_nay_filtered["Công việc"] == "レタッチ"]))
            c3.metric(t['metric_type'], len(df_nay_filtered[df_nay_filtered["Công việc"] == "写植"]))

    with tab2:
        st.info(f"**{t['time']}** {thong_tin_tuan_sau['start']} ➡️ {thong_tin_tuan_sau['end']} &nbsp;&nbsp;|&nbsp;&nbsp; **{t['deadline']}** {thong_tin_tuan_sau['deadline']}")
        if df_tuan_sau.empty:
            st.warning(t['no_task'])
        else:
            df_sau_display = df_sau_filtered.copy()
            df_sau_display.index = range(1, len(df_sau_display) + 1)
            df_sau_display.columns = t['cols']
            
            df_sau_styled = df_sau_display.style.apply(lambda _: highlight_changes(df_sau_display, st.session_state.df_sau_old), axis=None)
            st.dataframe(df_sau_styled, use_container_width=True)
            st.session_state.df_sau_old = df_sau_display.copy()
            
            c4, c5, c6 = st.columns(3)
            c4.metric(t['metric_total'], len(df_sau_filtered))
            c5.metric(t['metric_retouch'], len(df_sau_filtered[df_sau_filtered["Công việc"] == "レタッチ"]))
            c6.metric(t['metric_type'], len(df_sau_filtered[df_sau_filtered["Công việc"] == "写植"]))

# Kích hoạt hàm
render_realtime_dashboard()
