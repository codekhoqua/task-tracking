import streamlit as st
import pandas as pd
import requests
from datetime import date
import time
import streamlit.components.v1 as components

# 1. CẤU HÌNH TRANG
st.set_page_config(page_title="VN-Tracking Dashboard", layout="wide", initial_sidebar_state="expanded")

# ---- MÃ CSS GỘP CHUNG ----
st.markdown("""
    <style>
        [data-testid="stStatusWidget"], .stDeployButton, [data-testid="stMainMenu"] {display: none !important;}
        header[data-testid="stHeader"] {background-color: transparent !important;}
        
        .stMainBlockContainer { min-height: 100vh; }
        div[data-testid="stTabs"] { min-height: 800px; }
        
        .floating-widget { position: fixed; bottom: 20px; right: 20px; z-index: 999999; display: flex; flex-direction: column; align-items: flex-end; font-family: sans-serif; }
        #popup-toggle { display: none; }
        .popup-btn { background-color: #ff4b4b; color: white; padding: 10px 20px; border-radius: 50px; cursor: pointer; font-weight: bold; box-shadow: 0 4px 10px rgba(0,0,0,0.3); text-align: center; transition: 0.3s; user-select: none; }
        .popup-btn:hover { background-color: #ff3333; transform: scale(1.05); }
        .popup-iframe-container { display: none; margin-bottom: 15px; width: 420px; height: 550px; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 30px rgba(0,0,0,0.5); background: #0e1117; border: 1px solid #444; }
        #popup-toggle:checked ~ .popup-iframe-container { display: block; }
        #popup-toggle:checked ~ .popup-btn::after { content: "Đóng Manga App ❌"; }
        #popup-toggle:not(:checked) ~ .popup-btn::after { content: "Mở Manga Translator 🚀"; }
        
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

# KHỞI TẠO BIẾN STATE
if 'lang' not in st.session_state: st.session_state.lang = 'vi'
if 'df_nay_old' not in st.session_state: st.session_state.df_nay_old = None
if 'df_sau_old' not in st.session_state: st.session_state.df_sau_old = None

# GIAO DIỆN CHỌN NGÔN NGỮ
col_title, col_lang = st.columns([8, 2])
with col_lang:
    st.write("") 
    chon_ngon_ngu = st.selectbox("🌐 Ngôn ngữ / 言語", ["Tiếng Việt", "日本語"], index=0 if st.session_state.lang == 'vi' else 1)
    st.session_state.lang = 'vi' if chon_ngon_ngu == "Tiếng Việt" else 'ja'

dict_lang = {
    'vi': {
        'title': "📊 Quản lý tiến độ Team Việt Nam", 'filter_title': "### 🔍 Bộ lọc hiển thị",
        'cv_nay': "Công việc (Tuần Này):", 'nguoi_nay': "Người thực hiện (Tuần Này):",
        'cv_sau': "Công việc (Tuần Sau):", 'nguoi_sau': "Người thực hiện (Tuần Sau):",
        'tab1': "📌 THÔNG TIN TUẦN NÀY", 'tab2': "⏭️ THÔNG TIN TUẦN SAU",
        'time': "🗓️ Thời gian làm việc:", 'deadline': "🚨 DEADLINE CHÚ Ý:",
        'no_filter': "Không có tác phẩm nào khớp với bộ lọc!", 'no_task': "Tuần sau hiện chưa có task nào được phân công!",
        'metric_total': "Tổng số Task", 'metric_retouch': "Số task Retouch", 'metric_type': "Số task Lettering",
        'not_update': "Chưa cập nhật",
        'cols': ['Công việc', 'Tên tác phẩm', 'Chương', 'Tập', 'Số trang', 'NXB', 'Ngày bắt đầu', 'Deadline (Nộp)', 'VN', 'Người thực hiện', 'QC Nội bộ', 'Quản lý', 'Trạng thái', 'Bắt đầu', 'Ghi chú'],
        'logtime_title': "⏱️ KHU VỰC BÁO CÁO TIẾN ĐỘ (LOGTIME & CHECKLIST)",
        'logtime_empty': "Hiện không có task nào để logtime.",
        'f_date': "📅 Ngày làm việc:",
        'f_cat': "📚 Loại truyện (カテゴリ):",
        'f_diff': "🔥 Độ khó (難易度):",
        'f_worker': "👤 Người làm:",
        'f_hours': "⏳ Số giờ làm hôm nay:",
        'f_pages': "📄 Số page HT (Tổng: {total}):",
        'f_note': "📝 Ghi chú thêm (nếu có):",
        'f_btn': "Lưu Logtime",
        'f_warn': "⚠️ Vui lòng nhập số giờ hoặc số trang trước khi lưu!",
        'f_sync': "⏳ Đang đẩy dữ liệu sang JP...",
        'f_succ': "✅ Đã lưu thành công cho {worker}: {hours} giờ, {pages} trang.",
        'f_err': "❌ Có lỗi xảy ra khi lưu vào Sheet JP."
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
        'f_date': "📅 作業日:",
        'f_cat': "📚 カテゴリ:",
        'f_diff': "🔥 難易度:",
        'f_worker': "👤 作業者:",
        'f_hours': "⏳ 今日の作業時間:",
        'f_pages': "📄 完了ページ数 (計: {total}):",
        'f_note': "📝 備考 (あれば):",
        'f_btn': "保存する",
        'f_warn': "⚠️ 保存する前に時間またはページ数を入力してください！",
        'f_sync': "⏳ データを送信中...",
        'f_succ': "✅ {worker} のデータを保存しました: {hours} 時間, {pages} ページ。",
        'f_err': "❌ エラーが発生しました。"
    }
}
t = dict_lang[st.session_state.lang]

with col_title: 
    st.title(t['title'])

url = "https://docs.google.com/spreadsheets/d/1ec_v1hsKu0oCOwyrFNgxckpoaq3Q02J4NdIchqbYE3s/edit?usp=sharing"
csv_url = url.split("/edit")[0] + "/export?format=csv" if "/edit" in url else url

def get_clean_dates(vals_list):
    valid = []
    for v in vals_list:
        v_str = str(v).strip()
        if v_str in ['nan', 'NaN', 'None', ''] or v_str in [':', '->', '-', '=>']: continue
        if 'tuần làm việc' in v_str.lower() or 'deadline' in v_str.lower() or 'số tác phẩm' in v_str.lower(): continue
        if not v_str.isnumeric() and len(v_str) >= 5: valid.append(v_str)
    return valid

def clean_df(df):
    df = df.dropna(subset=['Công việc', 'Tên tác phẩm'])
    df = df[~df['Công việc'].astype(str).str.contains('Công việc|作業内容', na=False, case=False)]
    df = df[~df['Tên tác phẩm'].astype(str).str.contains('Tên tác phẩm|作品名|Tuần làm việc|Số tác phẩm', na=False, case=False)]
    df = df[df['Công việc'].astype(str).str.strip() != '']
    return df[~df['Công việc'].astype(str).str.lower().isin(['nan', 'none'])]

def highlight_changes(df_new, df_old):
    if df_old is None or df_new.shape != df_old.shape: return pd.DataFrame('', index=df_new.index, columns=df_new.columns)
    mask = df_new.astype(str).values != df_old.astype(str).values
    return pd.DataFrame([['background-color: rgba(255, 75, 75, 0.2); color: #ff4b4b; font-weight: bold;' if is_changed else '' for is_changed in row] for row in mask], index=df_new.index, columns=df_new.columns)

def save_logtime(ngay_log, category, cong_viec, tac_pham, chuong, tap, so_trang_tong, nguoi_thuc_hien, so_gio, so_page, difficulty, ghi_chu):
    api_url = "https://script.google.com/macros/s/AKfycbwRgcwRvxBZPOMEyfKbWCDXpLsY1H5edxQtxF4xihgaVIJn-eiqbuDB_2yCU9XYR_MwAQ/exec" 
    payload = {
        "ngay_log": str(ngay_log), "category": category, "cong_viec": cong_viec, "tac_pham": tac_pham,
        "chuong": str(chuong) if pd.notna(chuong) else "", "tap": str(tap) if pd.notna(tap) else "",
        "so_trang_tong": str(so_trang_tong) if pd.notna(so_trang_tong) else "",
        "nguoi_thuc_hien": str(nguoi_thuc_hien) if pd.notna(nguoi_thuc_hien) else "",
        "so_gio": so_gio, "so_page": so_page, "difficulty": difficulty, "ghi_chu": ghi_chu
    }
    try: return requests.post(api_url, json=payload).status_code == 200
    except: return False


# =====================================================================
# HÀM RENDER CHECKLIST TRỰC QUAN 
# =====================================================================
def get_checklist_html(tac_pham_key, index, lang):
    txt = {
        'vi': {
            'step1': 'STEP 1: CHUẨN BỊ', 'step2': 'STEP 2: BẮT ĐẦU', 'step3': 'STEP 3: GIAO HÀNG',
            't1': 'Tạo Task DB_工程管理', 't2': 'N: notion済', 
            't3': 'Báo bắt đầu', 't4': 'O: 開始 (Bắt đầu)', 't5': 'Not Started → In Progress',
            't6': 'Báo hoàn thành', 't7': 'N: 納品済み', 't8': 'Trạng thái: Delivered',
            'copy_start': '📋 Copy Báo Bắt Đầu', 'ask_task': 'Trễ chỉ thị? (Hỏi Task)', 'copy_ask': '📋 Copy Hỏi Task',
            'copy_done': '📋 Copy Báo Hoàn Thành', 'copied': '✅ Đã Copy',
            'copy_deliver': '📋 Copy Báo Giao Hàng'
        },
        'ja': {
            'step1': 'STEP 1: 準備', 'step2': 'STEP 2: 着手', 'step3': 'STEP 3: 納品',
            't1': 'DB_工程管理にタスク作成', 't2': 'N列：notion済', 
            't3': '着手報告 (Asana)', 't4': 'O列：開始', 't5': 'Not Started → In Progress',
            't6': '完了報告 (Asana)', 't7': 'N列：納品済み', 't8': 'ステータス：Delivered',
            'copy_start': '📋 着手報告をコピー', 'ask_task': '指示遅れ？(確認する)', 'copy_ask': '📋 確認文をコピー',
            'copy_done': '📋 完了報告をコピー', 'copied': '✅ コピー完了',
            'copy_deliver': '📋 納品メッセージをコピー'
        }
    }
    l = txt[lang]
    
    return f"""
    <!DOCTYPE html>
    <html lang="{lang}">
    <head>
        <style>
            :root {{ --primary: #0f4c81; --bg: #f8f9fa; --text: #2c3e50; }}
            * {{ box-sizing: border-box; font-family: 'Segoe UI', sans-serif; }}
            body {{ background: transparent; color: var(--text); padding: 0; margin: 0; overflow: hidden; }}
            .grid-container {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 15px; width: 100%; align-items: start; }}
            .step-col {{ background: #fff; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px; }}
            .step-header {{ font-size: 11px; font-weight: 800; color: #15803d; margin-bottom: 8px; border-bottom: 1px solid #e2e8f0; padding-bottom: 4px; text-transform: uppercase; }}
            
            .task-row {{ display: flex; align-items: flex-start; gap: 8px; margin-bottom: 6px; padding: 2px 0; flex-wrap: wrap; }}
            .badge {{ font-size: 9px; padding: 2px 4px; border-radius: 2px; color: #fff; font-weight: bold; width: 50px; text-align: center; flex-shrink: 0; }}
            .notion {{ background: #000; }} .sheet {{ background: #107c41; }} .asana {{ background: #fc636b; }}
            
            .check-wrapper {{ position: relative; cursor: pointer; flex-grow: 1; display: flex; align-items: center; min-height: 18px; }}
            .check-wrapper input {{ display: none; }}
            .action-text {{ font-size: 11px; margin-left: 20px; transition: 0.2s; line-height: 1.2; font-weight: 600; color: #1e293b; }}
            .checkmark {{ position: absolute; top: 0; left: 0; width: 14px; height: 14px; background: #eee; border-radius: 3px; border: 1px solid #cbd5e1; }}
            
            .check-wrapper input:checked ~ .checkmark {{ background: #22c55e; border-color: #22c55e; }}
            .check-wrapper input:checked ~ .checkmark:after {{ content: ""; position: absolute; display: block; left: 4px; top: 1px; width: 3px; height: 7px; border: solid white; border-width: 0 2px 2px 0; transform: rotate(45deg); }}
            .check-wrapper input:checked ~ .action-text {{ text-decoration: line-through; color: #94a3b8; }}
            
            .snippet-box {{ background: #f8fafc; border: 1px dashed #cbd5e1; padding: 5px; border-radius: 4px; font-family: monospace; font-size: 9.5px; color: #334155; white-space: pre-line; margin-bottom: 4px; margin-left: 58px; line-height: 1.3; }}
            .btn-copy {{ display: inline-flex; align-items: center; background: #f1f5f9; border: 1px solid #cbd5e1; padding: 2px 6px; border-radius: 4px; font-size: 9px; cursor: pointer; color: #0f4c81; font-weight: bold; margin-left: 58px; margin-bottom: 8px; transition: 0.2s; }}
            .btn-copy:hover {{ background: #e2e8f0; }}
            .btn-copy.success {{ background: #22c55e; color: white; border-color: #16a34a; }}
            
            summary {{ font-size: 10px; font-weight: bold; color: #d97706; cursor: pointer; margin-left: 58px; margin-bottom: 4px; user-select: none; }}
        </style>
    </head>
    <body>
        <div class="grid-container">
            <div class="step-col">
                <div class="step-header">{l['step1']}</div>
                <div class="task-row">
                    <span class="badge notion">Notion</span>
                    <label class="check-wrapper"><input type="checkbox" id="t1_{index}"><span class="checkmark"></span><div class="action-text">{l['t1']}</div></label>
                </div>
                <div class="task-row">
                    <span class="badge sheet">Sheet</span>
                    <label class="check-wrapper"><input type="checkbox" id="t2_{index}"><span class="checkmark"></span><div class="action-text">{l['t2']}</div></label>
                </div>
            </div>
            
            <div class="step-col">
                <div class="step-header">{l['step2']}</div>
                <div class="task-row">
                    <span class="badge asana">Asana</span>
                    <label class="check-wrapper"><input type="checkbox" id="t3_{index}"><span class="checkmark"></span><div class="action-text">{l['t3']}</div></label>
                </div>
                <div class="snippet-box" id="msg_t3_{index}">(PC) cc @Shiori Fujimura @Miho Osada @Erika Kawasaki
===タスク着手===</div>
                <button class="btn-copy" onclick="copyText(this, 'msg_t3_{index}')">{l['copy_start']}</button>
                
                <details>
                    <summary>{l['ask_task']}</summary>
                    <div class="snippet-box" id="jp_t3_{index}">お疲れ様です。
写植工程を担当しております○○です。
本日が作業開始日となっておりますが、現時点でまだご指示をいただいておりません。
お手数をおかけいたしますが、ご確認のほどよろしくお願いいたします。</div>
                    <button class="btn-copy" onclick="copyText(this, 'jp_t3_{index}')">{l['copy_ask']}</button>
                </details>
                
                <div class="task-row">
                    <span class="badge sheet">Sheet</span>
                    <label class="check-wrapper"><input type="checkbox" id="t4_{index}"><span class="checkmark"></span><div class="action-text">{l['t4']}</div></label>
                </div>
                <div class="task-row">
                    <span class="badge notion">Notion</span>
                    <label class="check-wrapper"><input type="checkbox" id="t5_{index}"><span class="checkmark"></span><div class="action-text">{l['t5']}</div></label>
                </div>
            </div>

            <div class="step-col">
                <div class="step-header">{l['step3']}</div>
                <div class="task-row">
                    <span class="badge asana">Asana</span>
                    <label class="check-wrapper"><input type="checkbox" id="t6_{index}"><span class="checkmark"></span><div class="action-text">{l['t6']}</div></label>
                </div>
                <div class="snippet-box" id="msg_t6_{index}">(PC) cc @Shiori Fujimura @Miho Osada @Erika Kawasaki
===タスク完了===</div>
                <button class="btn-copy" onclick="copyText(this, 'msg_t6_{index}')">{l['copy_done']}</button>
                
                <div class="task-row">
                    <span class="badge sheet">Sheet</span>
                    <label class="check-wrapper"><input type="checkbox" id="t7_{index}"><span class="checkmark"></span><div class="action-text">{l['t7']}</div></label>
                </div>
                <div class="task-row">
                    <span class="badge notion">Notion</span>
                    <label class="check-wrapper"><input type="checkbox" id="t8_{index}"><span class="checkmark"></span><div class="action-text">{l['t8']}</div></label>
                </div>
                
                <div class="snippet-box" id="msg_t8_{index}">納品いたしました。
ご確認のほどよろしくお願いいたします。</div>
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
                    setTimeout(() => {{
                        btn.innerText = oldText;
                        btn.classList.remove("success");
                    }}, 2000);
                }}).catch(err => console.error('Lỗi copy', err));
            }}
            
            const tpKey = "{tac_pham_key}";
            // ĐÃ ĐIỀN LINK WEB APP CỦA BẠN:
            const API_URL = "https://script.google.com/macros/s/AKfycbxBBnAtd7tEfDG3wsFV6bmb7Gd_ciDGmgAlVWaChq2iuiMQ3hVeuNKyb3TcPmjscd60Cw/exec";
            
            const checks = document.querySelectorAll('input[type="checkbox"]');
            
            checks.forEach(cb => {{
                const rawId = cb.id.split('_')[0]; 
                const storageKey = tpKey + "_" + rawId;
                
                if (localStorage.getItem(storageKey) === 'true') cb.checked = true;
                
                cb.addEventListener('change', async (e) => {{
                    const isChecked = e.target.checked;
                    localStorage.setItem(storageKey, isChecked);
                    
                    if(API_URL.startsWith("http")) {{
                        fetch(API_URL, {{
                            method: "POST",
                            mode: "no-cors",
                            headers: {{ "Content-Type": "text/plain;charset=utf-8" }},
                            body: JSON.stringify({{ tac_pham: tpKey, checkbox_id: rawId, status: isChecked }})
                        }}).catch(()=>console.log("Lỗi Sync"));
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
                }}).catch(()=>console.log("Dùng Offline"));
            }}
        </script>
    </body>
    </html>
    """

# =====================================================================
# HÀM CẬP NHẬT DỮ LIỆU CHÍNH (LẶP MỖI 30S)
# =====================================================================
@st.fragment(run_every="30s")
def render_realtime_dashboard():
    try: df_raw = pd.read_csv(csv_url, usecols=list(range(1, 16)), header=None)
    except:
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

    st.write(t['filter_title'])
    col_filter1, col_filter2 = st.columns(2)
    with col_filter1:
        cv_nay_list = df_tuan_nay["Công việc"].dropna().unique()
        cv_nay = st.multiselect(t['cv_nay'], options=cv_nay_list)
        nguoi_nay = st.multiselect(t['nguoi_nay'], options=df_tuan_nay["Người thực hiện"].dropna().unique())
    with col_filter2:
        cv_sau_list = df_tuan_sau["Công việc"].dropna().unique()
        cv_sau = st.multiselect(t['cv_sau'], options=cv_sau_list)
        nguoi_sau = st.multiselect(t['nguoi_sau'], options=df_tuan_sau["Người thực hiện"].dropna().unique())

    df_nay_filtered = df_tuan_nay[df_tuan_nay["Công việc"].isin(cv_nay)] if cv_nay else df_tuan_nay
    if nguoi_nay: df_nay_filtered = df_nay_filtered[df_nay_filtered["Người thực hiện"].isin(nguoi_nay)]
    df_sau_filtered = df_tuan_sau[df_tuan_sau["Công việc"].isin(cv_sau)] if cv_sau else df_tuan_sau
    if nguoi_sau: df_sau_filtered = df_sau_filtered[df_sau_filtered["Người thực hiện"].isin(nguoi_sau)]

    tab1, tab2 = st.tabs([t['tab1'], t['tab2']])

    with tab1:
        st.info(f"**{t['time']}** {thong_tin_tuan_nay['start']} ➡️ {thong_tin_tuan_nay['end']} &nbsp;&nbsp;|&nbsp;&nbsp; **{t['deadline']}** {thong_tin_tuan_nay['deadline']}")
        if df_nay_filtered.empty: st.warning(t['no_filter'])
        else:
            df_nay_display = df_nay_filtered.copy()
            df_nay_display.index = range(1, len(df_nay_display) + 1)
            df_nay_display.columns = t['cols']
            st.dataframe(df_nay_display.style.apply(lambda _: highlight_changes(df_nay_display, st.session_state.df_nay_old), axis=None), use_container_width=True)
            st.session_state.df_nay_old = df_nay_display.copy()
            
            c1, c2, c3 = st.columns(3)
            c1.metric(t['metric_total'], len(df_nay_filtered))
            c2.metric(t['metric_retouch'], len(df_nay_filtered[df_nay_filtered["Công việc"] == "レタッチ"]))
            c3.metric(t['metric_type'], len(df_nay_filtered[df_nay_filtered["Công việc"] == "写植"]))

        st.markdown("---")
        st.subheader(t['logtime_title'])
        
        if df_nay_filtered.empty: st.info(t['logtime_empty'])
        else:
            for index, row in df_nay_filtered.iterrows():
                tp_name = str(row['Công việc']).strip() + " - " + str(row['Tên tác phẩm']).strip()
                
                with st.expander(f"➕ {tp_name}"):
                    # ĐÃ ĐIỀU CHỈNH HEIGHT VỀ 330 ĐỂ VỪA KHÍT GIAO DIỆN MỚI
                    components.html(get_checklist_html(tp_name, index, st.session_state.lang), height=330, scrolling=False)
                    
                    with st.form(key=f"form_log_{index}"):
                        ngay_log = st.date_input(t['f_date'], value=date.today(), key=f"date_{index}")
                        
                        c_cat, c_diff, c_worker = st.columns(3)
                        with c_cat: loai_truyen = st.selectbox(t['f_cat'], ["単行本", "読切", "連載"], index=0, key=f"cat_{index}")
                        with c_diff: do_kho = st.selectbox(t['f_diff'], ["", "低", "中", "高"], index=0, key=f"diff_{index}")
                        with c_worker:
                            worker_options = ["Tan-タン", "Vinh-ジン", "Kim-キム", "Thao-タオ", "Hieu-コウ", "Anh-アイン", "Khuong-クォン", "Anh-ケ", "Thang-タンコイ"]
                            current_worker = str(row['Người thực hiện']).strip()
                            if pd.notna(row['Người thực hiện']) and current_worker != "" and current_worker not in worker_options:
                                worker_options.append(current_worker)
                            
                            default_idx = worker_options.index(current_worker) if pd.notna(row['Người thực hiện']) and current_worker in worker_options else 0
                            nguoi_lam_final = st.selectbox(t['f_worker'], worker_options, index=default_idx, key=f"sel_worker_{index}")

                        col1, col2 = st.columns(2)
                        with col1: so_gio = st.number_input(t['f_hours'], min_value=0.0, step=0.5, key=f"gio_{index}")
                        
                        so_trang_tong = row['Số trang'] if pd.notna(row['Số trang']) else 0
                        with col2: so_page = st.number_input(t['f_pages'].format(total=so_trang_tong), min_value=0, step=1, key=f"page_{index}")
                        
                        ghi_chu_log = st.text_input(t['f_note'], key=f"note_{index}")
                        
                        submit_col, msg_col = st.columns([2, 8])
                        with submit_col:
                            submit_btn = st.form_submit_button(t['f_btn'])
                            
                        if submit_btn:
                            with msg_col: 
                                if so_gio == 0 and so_page == 0: 
                                    st.warning(t['f_warn'])
                                else:
                                    with st.spinner(t['f_sync']):
                                        is_success = save_logtime(ngay_log, loai_truyen, row['Công việc'], row['Tên tác phẩm'], row['Chương'], row['Tập'], row['Số trang'], nguoi_lam_final, so_gio, so_page, do_kho, ghi_chu_log)
                                    
                                    if is_success: 
                                        st.success(t['f_succ'].format(worker=nguoi_lam_final, hours=so_gio, pages=so_page))
                                    else: 
                                        st.error(t['f_err'])

    with tab2:
        st.info(f"**{t['time']}** {thong_tin_tuan_sau['start']} ➡️ {thong_tin_tuan_sau['end']} &nbsp;&nbsp;|&nbsp;&nbsp; **{t['deadline']}** {thong_tin_tuan_sau['deadline']}")
        if df_tuan_sau.empty: st.warning(t['no_task'])
        else:
            df_sau_display = df_sau_filtered.copy()
            df_sau_display.index = range(1, len(df_sau_display) + 1)
            df_sau_display.columns = t['cols']
            st.dataframe(df_sau_display.style.apply(lambda _: highlight_changes(df_sau_display, st.session_state.df_sau_old), axis=None), use_container_width=True)
            st.session_state.df_sau_old = df_sau_display.copy()
            
            c4, c5, c6 = st.columns(3)
            c4.metric(t['metric_total'], len(df_sau_filtered))
            c5.metric(t['metric_retouch'], len(df_sau_filtered[df_sau_filtered["Công việc"] == "レタッチ"]))
            c6.metric(t['metric_type'], len(df_sau_filtered[df_sau_filtered["Công việc"] == "写植"]))

render_realtime_dashboard()
