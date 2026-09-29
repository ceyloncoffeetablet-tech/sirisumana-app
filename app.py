import json
import os
import time
from google import genai
from google.genai import types
from PIL import Image
import pandas as pd
import plotly.express as px
import streamlit as st

# Page Configuration
st.set_page_config(
    page_title="සිරි සුමන පිරිවෙන් ලකුණු පද්ධතිය",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Admin Password & API Configuration
ADMIN_PASSWORD = "sirisumana123"

# Streamlit Secrets හරහා ආරක්ෂිතව API Key එක ලබා ගැනීම
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY", "")

# Permanent Data Files
DATA_FILE = "student_marks.json"
ROSTER_FILE = "student_roster.json"


# Helper Functions for Marks Data Persistence
def load_marks_data():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        df = pd.DataFrame(data)
        if "Year" not in df.columns:
          df["Year"] = "2026"
        if "Status" not in df.columns:
          df["Status"] = "Locked"
        return df
    except Exception:
      pass
  return pd.DataFrame(
      columns=["Student ID", "Grade", "Year", "Term", "Subject", "Marks", "Status"]
  )


def save_marks_data(df):
  data = df.to_dict(orient="records")
  with open(DATA_FILE, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)


# Helper Functions for Roster Persistence
def load_roster_data():
  if os.path.exists(ROSTER_FILE):
    try:
      with open(ROSTER_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return {}


def save_roster_data(roster):
  with open(ROSTER_FILE, "w", encoding="utf-8") as f:
    json.dump(roster, f, ensure_ascii=False, indent=4)


# Always load persistent data
st.session_state.student_data = load_marks_data()
st.session_state.roster_data = load_roster_data()

# Header
st.title("🏫 මහා/දෙනු/ සිරිසුමන ද්විභාෂා පිරිවෙන")
st.caption("ශිෂ්‍ය සාධන හා ලේඛන කළමනාකරණ පද්ධතිය - විභාග අංශය")
st.divider()

# Sidebar Authentication & UI Zoom Control
st.sidebar.title("🔑 පද්ධති ප්‍රවේශය (Login)")
role = st.sidebar.radio(
    "ඔබගේ කාර්යභාරය තෝරන්න:",
    ["පන්තිභාර ගුරු (Teacher)", "විදුහල්පති/Admin (Principal)"],
)

admin_access = False
if role == "විදුහල්පති/Admin (Principal)":
  password = st.sidebar.text_input("Admin මුරපදය (Password):", type="password")
  if password == ADMIN_PASSWORD:
    admin_access = True
    st.sidebar.success("Admin විදියට සාර්ථකව Log වුණා!")
  elif password:
    st.sidebar.error("වැරදි මුරපදයකි!")

st.sidebar.divider()

# App UI Zoom Control Settings
st.sidebar.subheader("🔍 App Zoom & අකුරු ප්‍රමාණය")
zoom_level = st.sidebar.select_slider(
    "පද්ධතියේ Font Size එක තෝරන්න:",
    options=["සාමාන්‍ය (Normal)", "විශාල (Large)", "ඉතා විශාල (Extra Large)"],
    value="සාමාන්‍ය (Normal)",
)

if zoom_level == "විශාල (Large)":
  st.markdown(
      """
        <style>
            html, body, [class*="css"] { font-size: 18px !important; }
            input { font-size: 18px !important; height: 45px !important; }
            .stSelectbox, .stNumberInput { font-size: 18px !important; }
        </style>
    """,
      unsafe_allow_html=True,
  )
elif zoom_level == "ඉතා විශාල (Extra Large)":
  st.markdown(
      """
        <style>
            html, body, [class*="css"] { font-size: 21px !important; }
            input { font-size: 21px !important; height: 50px !important; }
            .stSelectbox, .stNumberInput { font-size: 21px !important; }
        </style>
    """,
      unsafe_allow_html=True,
  )

# TAB NAVIGATION
tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 ශිෂ්‍ය නාම ලේඛනය",
    "📝 ලකුණු ඇතුළත් කිරීම",
    "📄 විෂයානුබද්ධ විශ්ලේෂණය (නිල වාර්තාව)",
    "👤 ශිෂ්‍යානුබද්ධ විශ්ලේෂණය",
    "🏫 සමස්ත පන්ති විශ්ලේෂණය",
    "⚙️ දත්ත පාලනය හා සංස්කරණය",
])

# Grade List including Foundation Grade & English Medium
GRADES = [
    "මූලික ශ්‍රේණිය",
    "1 ශ්‍රේණිය",
    "2 ශ්‍රේණිය",
    "3 ශ්‍රේණිය",
    "4 ශ්‍රේණිය",
    "5 ශ්‍රේණිය",
    "English Medium 1",
    "English Medium 2",
    "English Medium 3",
    "English Medium 4",
    "English Medium 5",
]

# Years List
YEARS = ["2025", "2026", "2027", "2028", "2029", "2030"]

# List of all 10 subjects (Updated to 'සංස්කෘත')
SUBJECTS = [
    "ත්‍රිපිටක ධර්මය (Tripitaka)",
    "සිංහල (Sinhala)",
    "පාලි (Pali)",
    "සංස්කෘත (Sanskrit)",
    "ගණිතය (Maths)",
    "ඉංග්‍රීසි (English)",
    "ඉතිහාසය (History)",
    "සමාජ විද්‍යාව (Social Sci.)",
    "සෞඛ්‍ය විද්‍යාව (Health Sci.)",
    "භූගෝල විද්‍යාව (Geog. Phy.)",
]


# Helper Function for Grading
def get_grade(marks):
  try:
    m = float(marks)
  except:
    return "Absent"
  if m >= 75:
    return "A"
  elif m >= 65:
    return "B"
  elif m >= 50:
    return "C"
  elif m >= 35:
    return "S"
  else:
    return "F"


# ----------------------------------------------------
# TAB 0: STUDENT ROSTER MANAGEMENT
# ----------------------------------------------------
with tab0:
  st.header("📋 පන්ති අනුව ශිෂ්‍ය නාම ලේඛනය ලියාපදිංචිය")
  st.info("මෙහි පන්තියට අදාළ ශිෂ්‍ය විභාග අංක ලියාපදිංචි කර තැබිය හැක.")

  col_r_meta1, col_r_meta2 = st.columns(2)
  with col_r_meta1:
    r_grade = st.selectbox("ශ්‍රේණිය / පන්තිය තෝරන්න:", GRADES, key="r_grade")
  with col_r_meta2:
    r_year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="r_year")

  reg_id = st.text_input("ඇතුළත් වීමේ අංකය / විභාග අංකය (උදා: 3000):")

  if st.button("➕ ශිෂ්‍ය අංකය පන්තියට Save කරන්න", type="primary"):
    if reg_id:
      if r_grade not in st.session_state.roster_data:
        st.session_state.roster_data[r_grade] = []
      if reg_id not in st.session_state.roster_data[r_grade]:
        st.session_state.roster_data[r_grade].append(reg_id)
        save_roster_data(st.session_state.roster_data)
        st.success(
            f"විභාග අංක {reg_id} ශිෂ්‍යයා {r_grade} පන්තියට සාර්ථකව සේව් විය!"
        )
        st.rerun()
      else:
        st.warning("මෙම විභාග අංකය දැනටමත් ඇතුළත් කර ඇත.")
    else:
      st.warning("කරුණාකර විභාග අංකය ඇතුළත් කරන්න.")

  st.divider()
  st.subheader(f"📌 {r_grade} දැනට ලියාපදිංචි සිසුන්ගේ අංක")
  if (
      r_grade in st.session_state.roster_data
      and st.session_state.roster_data[r_grade]
  ):
    roster_df = pd.DataFrame(
        st.session_state.roster_data[r_grade], columns=["විභාග අංකය"]
    )
    st.dataframe(roster_df, use_container_width=True)
  else:
    st.write("මෙම පන්තියට තවමත් සිසුන් ලියාපදිංචි කර නැත.")

# ----------------------------------------------------
# TAB 1: DATA ENTRY (MANUAL / PHOTO / PDF)
# ----------------------------------------------------
with tab1:
  st.header("ශිෂ්‍ය ලකුණු ඇතුළත් කිරීම")

  entry_method = st.radio(
      "ඇතුළත් කිරීමේ ක්‍රමය තෝරන්න:",
      [
          "📸 Photo එකක් upload කර Scan කිරීම (AI Scan)",
          "📄 PDF File එකක් upload කර Scan කිරීම (PDF Scan)",
          "✍️ අතින් එකින් එක ටයිප් කිරීම (Manual Entry)",
      ],
      horizontal=True,
  )
  st.divider()

  # METHOD 1: PHOTO AI SCAN
  if "Photo" in entry_method:
    st.subheader("📸 ඡායාරූපයක් (Photo Image) මඟින් ලකුණු ලබා ගැනීම")
    uploaded_img = st.file_uploader(
        "ලකුණු පත්‍රිකාවේ Image එක Upload කරන්න (JPG/PNG)",
        type=["jpg", "jpeg", "png"],
    )

    if uploaded_img:
      img = Image.open(uploaded_img)
      with st.expander("🔍 ඡායාරූපය Zoom කර බලන්න", expanded=True):
        img_width = st.slider(
            "Zoom Level:",
            min_value=300,
            max_value=1500,
            value=700,
            step=50,
            key="img_zoom",
        )
        st.image(img, caption="Upload කරන ලද Image එක", width=img_width)

    col_scan1, col_scan2, col_scan3 = st.columns(3)
    with col_scan1:
      scan_grade = st.selectbox("ශ්‍රේණිය / පන්තිය:", GRADES, key="img_scan_grade")
    with col_scan2:
      scan_year = st.selectbox("වර්ෂය:", YEARS, index=1, key="img_scan_year")
    with col_scan3:
      scan_term = st.selectbox(
          "වාරය:", ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"], key="img_scan_term"
      )

    if uploaded_img and st.button(
        "🔍 Photo එක Scan කර දත්ත ලබා ගන්න", type="primary", key="btn_img_scan"
    ):
      if not GEMINI_API_KEY:
        st.error(
            "කරුණාකර Streamlit Secrets හි GEMINI_API_KEY සකසා ඇති බව තහවුරු"
            " කරන්න."
        )
      else:
        try:
          with st.spinner(
              "AI මඟින් Photo එක පරීක්ෂා කරමින් පවතී (ටිකක් රැඳී"
              " සිටින්න)..."
          ):
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt_text = (
                "මෙම ඡායාරූපයෙහි ඇති ශිෂ්‍ය ලකුණු ලේඛනයෙන් සෑම ශිෂ්‍යයෙකුගේම"
                " විභාග අංකය (Student ID) සහ ලකුණු පහත JSON ආකෘතියෙන් ලබාදෙන්න.\n"
                "අවශ්‍ය විෂයන්: ත්‍රිපිටක ධර්මය (Tripitaka), සිංහල (Sinhala),"
                " පාලි (Pali), සංස්කෘත (Sanskrit), ගණිතය (Maths), ඉංග්‍රීසි"
                " (English), ඉතිහාසය (History), සමාජ විද්‍යාව (Social Sci.),"
                " සෞඛ්‍ය විද්‍යාව (Health Sci.), භූගෝල විද්‍යාව (Geog. Phy.)\n"
                "ලකුණු නැතිනම් හෝ නොපැමිණි නම් 'Absent' හෝ 0 යොදන්න.\n"
                "JSON Format:\n"
                '[{"Student ID": "3017", "Marks": {"ත්‍රිපිටක ධර්මය'
                ' (Tripitaka)": 48, "සිංහල (Sinhala)": 62, "පාලි (Pali)": 60,'
                ' "සංස්කෘත (Sanskrit)": 55, "ගණිතය (Maths)": 59, "ඉංග්‍රීසි'
                ' (English)": 31, "ඉතිහාසය (History)": 0, "සමාජ විද්‍යාව (Social'
                ' Sci.)": 0, "සෞඛ්‍ය විද්‍යාව (Health Sci.)": 0, "භූගෝල විද්‍යාව'
                ' (Geog. Phy.)": 0}}]\n'
                "වෙනත් කිසිදු අමතර සටහනක් නොලියා pure JSON පමණක් ලබාදෙන්න."
            )

            max_retries = 3
            response = None
            for attempt in range(max_retries):
              try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=[img, prompt_text]
                )
                break
              except Exception as err:
                if "503" in str(err) and attempt < max_retries - 1:
                  time.sleep(3)
                  continue
                else:
                  raise err

            raw_json = (
                response.text.strip()
                .replace("```json", "")
                .replace("```", "")
            )
            extracted_students = json.loads(raw_json)

            new_rows = []
            for st_data in extracted_students:
              s_id = str(st_data.get("Student ID", ""))
              s_marks = st_data.get("Marks", {})
              for sub, mark in s_marks.items():
                if sub in SUBJECTS:
                  status_val = (
                      "Absent"
                      if str(mark).strip().lower() in ["absent", "ab", "abs"]
                      else "Locked"
                  )
                  m_val = (
                      0
                      if status_val == "Absent"
                      else (int(mark) if str(mark).isdigit() else 0)
                  )
                  new_rows.append({
                      "Student ID": s_id,
                      "Grade": scan_grade,
                      "Year": scan_year,
                      "Term": scan_term,
                      "Subject": sub,
                      "Marks": m_val,
                      "Status": status_val,
                  })
            if new_rows:
              extracted_df = pd.DataFrame(new_rows)
              st.session_state.student_data = pd.concat(
                  [st.session_state.student_data, extracted_df],
                  ignore_index=True,
              )
              save_marks_data(st.session_state.student_data)
              st.success("✅ Photo එකෙන් දත්ත සාර්ථකව ඇතුළත් කරගන්නා ලදී!")
              st.dataframe(extracted_df, use_container_width=True)
        except Exception as e:
          st.error(f"දෝෂයක් සිදු විය: {str(e)}")

  # METHOD 2: PDF AI SCAN
  elif "PDF" in entry_method:
    st.subheader("📄 PDF File එකක් මඟින් ලකුණු ලබා ගැනීම")
    uploaded_pdf = st.file_uploader(
        "ලකුණු පත්‍රිකාවේ PDF File එක Upload කරන්න", type=["pdf"]
    )

    col_pdf1, col_pdf2, col_pdf3 = st.columns(3)
    with col_pdf1:
      pdf_grade = st.selectbox("ශ්‍රේණිය / පන්තිය:", GRADES, key="pdf_scan_grade")
    with col_pdf2:
      pdf_year = st.selectbox("වර්ෂය:", YEARS, index=1, key="pdf_scan_year")
    with col_pdf3:
      pdf_term = st.selectbox(
          "වාරය:", ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"], key="pdf_scan_term"
      )

    if uploaded_pdf and st.button(
        "📄 PDF එක Scan කර දත්ත ලබා ගන්න", type="primary", key="btn_pdf_scan"
    ):
      if not GEMINI_API_KEY:
        st.error(
            "කරුණාකර Streamlit Secrets හි GEMINI_API_KEY සකසා ඇති බව තහවුරු"
            " කරන්න."
        )
      else:
        try:
          with st.spinner(
              "AI මඟින් PDF එක පරීක්ෂා කරමින් පවතී (ටිකක් රැඳී"
              " සිටින්න)..."
          ):
            client = genai.Client(api_key=GEMINI_API_KEY)
            pdf_bytes = uploaded_pdf.read()

            pdf_part = types.Part.from_bytes(
                data=pdf_bytes, mime_type="application/pdf"
            )

            prompt_text = (
                "මෙම PDF ගොනුවෙහි ඇති ශිෂ්‍ය ලකුණු ලේඛනයෙන් සෑම ශිෂ්‍යයෙකුගේම"
                " විභාග අංකය (Student ID) සහ ලකුණු පහත JSON ආකෘතියෙන් ලබාදෙන්න.\n"
                "අවශ්‍ය විෂයන්: ත්‍රිපිටක ධර්මය (Tripitaka), සිංහල (Sinhala),"
                " පාලි (Pali), සංස්කෘත (Sanskrit), ගණිතය (Maths), ඉංග්‍රීසි"
                " (English), ඉතිහාසය (History), සමාජ විද්‍යාව (Social Sci.),"
                " සෞඛ්‍ය විද්‍යාව (Health Sci.), භූගෝල විද්‍යාව (Geog. Phy.)\n"
                "ලකුණු නැතිනම් හෝ නොපැමිණි නම් 'Absent' හෝ 0 යොදන්න.\n"
                "JSON Format:\n"
                '[{"Student ID": "3017", "Marks": {"ත්‍රිපිටක ධර්මය'
                ' (Tripitaka)": 48, "සිංහල (Sinhala)": 62, "පාලි (Pali)": 60,'
                ' "සංස්කෘත (Sanskrit)": 55, "ගණිතය (Maths)": 59, "ඉංග්‍රීසි'
                ' (English)": 31, "ඉතිහාසය (History)": 0, "සමාජ විද්‍යාව (Social'
                ' Sci.)": 0, "සෞඛ්‍ය විද්‍යාව (Health Sci.)": 0, "භූගෝල විද්‍යාව'
                ' (Geog. Phy.)": 0}}]\n'
                "වෙනත් කිසිදු අමතර සටහනක් නොලියා pure JSON පමණක් ලබාදෙන්න."
            )

            max_retries = 3
            response = None
            for attempt in range(max_retries):
              try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash", contents=[pdf_part, prompt_text]
                )
                break
              except Exception as err:
                if "503" in str(err) and attempt < max_retries - 1:
                  time.sleep(3)
                  continue
                else:
                  raise err

            raw_json = (
                response.text.strip()
                .replace("```json", "")
                .replace("```", "")
            )
            extracted_students = json.loads(raw_json)

            new_rows = []
            for st_data in extracted_students:
              s_id = str(st_data.get("Student ID", ""))
              s_marks = st_data.get("Marks", {})
              for sub, mark in s_marks.items():
                if sub in SUBJECTS:
                  status_val = (
                      "Absent"
                      if str(mark).strip().lower() in ["absent", "ab", "abs"]
                      else "Locked"
                  )
                  m_val = (
                      0
                      if status_val == "Absent"
                      else (int(mark) if str(mark).isdigit() else 0)
                  )
                  new_rows.append({
                      "Student ID": s_id,
                      "Grade": pdf_grade,
                      "Year": pdf_year,
                      "Term": pdf_term,
                      "Subject": sub,
                      "Marks": m_val,
                      "Status": status_val,
                  })
            if new_rows:
              extracted_df = pd.DataFrame(new_rows)
              st.session_state.student_data = pd.concat(
                  [st.session_state.student_data, extracted_df],
                  ignore_index=True,
              )
              save_marks_data(st.session_state.student_data)
              st.success("✅ PDF එකෙන් දත්ත සාර්ථකව ඇතුළත් කරගන්නා ලදී!")
              st.dataframe(extracted_df, use_container_width=True)
        except Exception as e:
          st.error(f"දෝෂයක් සිදු විය: {str(e)}")

  # METHOD 3: MANUAL ENTRY
  else:
    col1, col2 = st.columns(2)
    with col1:
      grade = st.selectbox("ශ්‍රේණිය / පන්තිය තෝරන්න:", GRADES, key="entry_grade")
      year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="entry_year")
      term = st.selectbox(
          "වාරය තෝරන්න:",
          ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"],
          key="entry_term",
      )

      roster_list = st.session_state.roster_data.get(grade, [])
      if roster_list:
        selected_student_option = st.selectbox(
            "ලියාපදිංචි සිසුන්ගෙන් තෝරන්න (නැතහොත් පහළින් ටයිප් කරන්න):",
            ["-- අලුතින් ටයිප් කරන්න --"] + roster_list,
        )
        if selected_student_option != "-- අලුතින් ටයිප් කරන්න --":
          student_id = st.text_input(
              "ඇතුළත් වීමේ අංකය / විභාග අංකය:", value=selected_student_option
          )
        else:
          student_id = st.text_input(
              "ඇතුළත් වීමේ අංකය / විභාග අංකය (Index No):"
          )
      else:
        student_id = st.text_input("ඇතුළත් වීමේ අංකය / විභාග අංකය (Index No):")

    with col2:
      st.subheader("විෂයයන් 10 සහ ලකුණු (හෝ නොපැමිණී නම් Absent තෝරන්න)")
      marks_dict = {}
      status_dict = {}
      for sub in SUBJECTS:
        col_m1, col_m2 = st.columns([2, 1])
        with col_m1:
          marks_dict[sub] = st.number_input(
              f"{sub} ලකුණු:",
              min_value=0,
              max_value=100,
              value=0,
              step=1,
              key=f"m_{sub}",
          )
        with col_m2:
          is_absent = st.checkbox(
              "Absent (නොපැමිණී)", key=f"abs_{sub}", value=False
          )
          status_dict[sub] = "Absent" if is_absent else "Locked"

    is_locked = False
    if not st.session_state.student_data.empty:
      check_df = st.session_state.student_data[
          (st.session_state.student_data["Student ID"] == student_id)
          & (st.session_state.student_data["Year"] == year)
          & (st.session_state.student_data["Term"] == term)
          & (st.session_state.student_data["Status"] == "Locked")
      ]
      if not check_df.empty:
        is_locked = True

    st.divider()

    if is_locked and not admin_access:
      st.error(
          "⛔ මෙම ශිෂ්‍යයාගේ මෙම වර්ෂයේ සහ වාරයේ ලකුණු දැනටමත් Lock කර ඇත."
          " වෙනස් කිරීමට Admin අමතන්න."
      )
    else:
      btn_col1, btn_col2 = st.columns(2)
      with btn_col1:
        if st.button(
            "💾 තාවකාලිකව සුරකින්න (Save Draft)", use_container_width=True
        ):
          if student_id:
            st.session_state.student_data = st.session_state.student_data[
                ~(
                    (st.session_state.student_data["Student ID"] == student_id)
                    & (st.session_state.student_data["Year"] == year)
                    & (st.session_state.student_data["Term"] == term)
                )
            ]
            new_rows = []
            for sub, mark in marks_dict.items():
              st_val = (
                  "Absent" if status_dict[sub] == "Absent" else "Draft"
              )
              m_val = 0 if st_val == "Absent" else mark
              new_rows.append({
                  "Student ID": student_id,
                  "Grade": grade,
                  "Year": year,
                  "Term": term,
                  "Subject": sub,
                  "Marks": m_val,
                  "Status": st_val,
              })
            st.session_state.student_data = pd.concat(
                [st.session_state.student_data, pd.DataFrame(new_rows)],
                ignore_index=True,
            )
            save_marks_data(st.session_state.student_data)
            st.success("ලකුණු තාවකාලිකව සුරකින ලදී (Draft Mode)!")
          else:
            st.warning("කරුණාකර ශිෂ්‍ය අංකය ඇතුළත් කරන්න.")

      with btn_col2:
        if st.button(
            "🔒 සම්පූර්ණයෙන් යවා Lock කරන්න (Final Submit)",
            type="primary",
            use_container_width=True,
        ):
          if student_id:
            st.session_state.student_data = st.session_state.student_data[
                ~(
                    (st.session_state.student_data["Student ID"] == student_id)
                    & (st.session_state.student_data["Year"] == year)
                    & (st.session_state.student_data["Term"] == term)
                )
            ]
            new_rows = []
            for sub, mark in marks_dict.items():
              st_val = status_dict[sub]
              m_val = 0 if st_val == "Absent" else mark
              new_rows.append({
                  "Student ID": student_id,
                  "Grade": grade,
                  "Year": year,
                  "Term": term,
                  "Subject": sub,
                  "Marks": m_val,
                  "Status": st_val,
              })
            st.session_state.student_data = pd.concat(
                [st.session_state.student_data, pd.DataFrame(new_rows)],
                ignore_index=True,
            )
            save_marks_data(st.session_state.student_data)
            st.success("ලකුණු සාර්ථකව පද්ධතියට එක් කර Lock කරන ලදී!")
          else:
            st.warning("කරුණාකර ශිෂ්‍ය අංකය ඇතුළත් කරන්න.")

# ----------------------------------------------------
# TAB 2: SUBJECT-WISE OFFICIAL PRINT FORM
# ----------------------------------------------------
with tab2:
  st.header("📄 වාර පරීක්ෂණ ප්‍රතිඵල විශ්ලේෂණ වාර්තාව")

  col_sel1, col_sel2, col_sel3, col_sel4 = st.columns(4)
  with col_sel1:
    sel_grade = st.selectbox("ශ්‍රේණිය තෝරන්න:", GRADES, key="sub_grade")
  with col_sel2:
    sel_year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="sub_year")
  with col_sel3:
    sel_term = st.selectbox(
        "වාරය තෝරන්න:",
        ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"],
        key="sub_term",
    )
  with col_sel4:
    sel_subject = st.selectbox("විෂය තෝරන්න:", SUBJECTS, key="sub_subject")

  st.divider()

  sub_df = st.session_state.student_data[
      (st.session_state.student_data["Grade"] == sel_grade)
      & (st.session_state.student_data["Year"] == sel_year)
      & (st.session_state.student_data["Term"] == sel_term)
      & (st.session_state.student_data["Subject"] == sel_subject)
  ].copy()

  if sub_df.empty:
    st.info(
        "තෝරාගත් පන්තිය, වර්ෂය, වාරය සහ විෂය සඳහා කිසිදු දත්තයක් ඇතුළත් කර"
        " නොමැත."
    )
  else:
    sub_df["සාමාර්ථය"] = sub_df.apply(
        lambda r: (
            "Absent"
            if str(r.get("Status")) == "Absent"
            else get_grade(r["Marks"])
        ),
        axis=1,
    )
    sub_df["සාධන මට්ටම"] = sub_df.apply(
        lambda r: (
            "Absent"
            if str(r.get("Status")) == "Absent"
            else f"{int(r['Marks'])}%"
        ),
        axis=1,
    )
    sub_df["ප්‍රගති මැනීම"] = sub_df.apply(
        lambda r: (
            "නොපැමිණී"
            if str(r.get("Status")) == "Absent"
            else (
                "යහපත්"
                if r["Marks"] >= 65
                else ("මධ්‍යම" if r["Marks"] >= 35 else "දුර්වල")
            )
        ),
        axis=1,
    )
    sub_df["විශ්ලේෂණයන්"] = sub_df.apply(
        lambda r: (
            "විභාගයට නොපැමිණ ඇත"
            if str(r.get("Status")) == "Absent"
            else (
                "ලකුණු මට්ටම උසස් කරගත යුතුය"
                if r["Marks"] < 50
                else "සාධනීය මට්ටමක පවතී"
            )
        ),
        axis=1,
    )

    display_sub_df = sub_df.reset_index(drop=True)
    display_sub_df.index += 1
    display_sub_df = display_sub_df.reset_index().rename(
        columns={"index": "අනු අංකය", "Student ID": "විභාග අංකය"}
    )
    show_table = display_sub_df[[
        "අනු අංකය",
        "විභාග අංකය",
        "සාධන මට්ටම",
        "සාමාර්ථය",
        "ප්‍රගති මැනීම",
        "විශ්ලේෂණයන්",
    ]]

    st.dataframe(show_table, use_container_width=True)

    non_absent_sub = sub_df[sub_df["Status"] != "Absent"]
    r1_30 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] >= 1) & (non_absent_sub["Marks"] <= 30)
        ]
    )
    r30_40 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 30) & (non_absent_sub["Marks"] <= 40)
        ]
    )
    r40_50 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 40) & (non_absent_sub["Marks"] <= 50)
        ]
    )
    r50_60 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 50) & (non_absent_sub["Marks"] <= 60)
        ]
    )
    r60_70 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 60) & (non_absent_sub["Marks"] <= 70)
        ]
    )
    r70_80 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 70) & (non_absent_sub["Marks"] <= 80)
        ]
    )
    r80_90 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 80) & (non_absent_sub["Marks"] <= 90)
        ]
    )
    r90_100 = len(
        non_absent_sub[
            (non_absent_sub["Marks"] > 90) & (non_absent_sub["Marks"] <= 100)
        ]
    )
    r_abs = len(sub_df[sub_df["Status"] == "Absent"])

    rows_html = ""
    for idx, row in show_table.iterrows():
      rows_html += f"""
            <tr>
                <td style="border:1px solid #000; padding:5px; text-align:center;">{row['අනු අංකය']}</td>
                <td style="border:1px solid #000; padding:5px; text-align:center;">{row['විභාග අංකය']}</td>
                <td style="border:1px solid #000; padding:5px; text-align:center;">{row['සාධන මට්ටම']}</td>
                <td style="border:1px solid #000; padding:5px; text-align:center;">{row['සාමාර්ථය']}</td>
                <td style="border:1px solid #000; padding:5px; text-align:center;">{row['ප්‍රගති මැනීම']}</td>
                <td style="border:1px solid #000; padding:5px;">{row['විශ්ලේෂණයන්']}</td>
            </tr>
            """

    html_doc = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>ප්‍රතිඵල විශ්ලේෂණ වාර්තාව</title>
            <style>
                body {{ font-family: 'Arial', sans-serif; padding: 20px; color: #000; }}
                .header-box {{ border: 2px solid #000; padding: 10px; text-align: center; font-weight: bold; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ border: 1px solid #000; padding: 6px; text-align: left; font-size: 13px; }}
                th {{ background-color: #f2f2f2; text-align: center; }}
                .flex-container {{ display: flex; justify-content: space-between; margin-top: 20px; }}
                .dist-table {{ width: 45%; }}
                .notes-box {{ width: 50%; border: 1px solid #000; padding: 10px; font-size: 13px; }}
                .signatures {{ margin-top: 50px; display: flex; justify-content: space-between; text-align: center; font-weight: bold; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="header-box">
                <h2 style="margin:2px;">මහ/දෙනු/ සිරිසුමන ද්විභාෂා පිරිවෙණ</h2>
                <h3 style="margin:2px;">විභාග අංශය</h3>
                <p style="margin:2px;">වාර පරීක්ෂණ ප්‍රතිඵල විශ්ලේෂණ වාර්තාව ({sel_term}) - {sel_year}</p>
                <div style="display:flex; justify-content:space-between; margin-top:10px;">
                    <span>ශ්‍රේණිය :- {sel_grade}</span>
                    <span>වර්ෂය :- {sel_year}</span>
                    <span>විෂය :- {sel_subject}</span>
                </div>
            </div>

            <table>
                <thead>
                    <tr>
                        <th style="width:10%;">අනු අංකය</th>
                        <th style="width:20%;">විභාග අංකය</th>
                        <th style="width:15%;">සාධන මට්ටම</th>
                        <th style="width:15%;">සාමාර්ථය</th>
                        <th style="width:15%;">ප්‍රගති මැනීම</th>
                        <th style="width:25%;">විශ්ලේෂණයන්</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            <div class="flex-container">
                <div class="dist-table">
                    <h4>📊 ලකුණු පරාස අනුව සාධන මට්ටමට ළඟාවීම</h4>
                    <table>
                        <tr><th>ලකුණු පරාසය</th><th>සිසුන් ගණන</th></tr>
                        <tr><td>01-30</td><td style="text-align:center;">{r1_30}</td></tr>
                        <tr><td>30-40</td><td style="text-align:center;">{r30_40}</td></tr>
                        <tr><td>40-50</td><td style="text-align:center;">{r40_50}</td></tr>
                        <tr><td>50-60</td><td style="text-align:center;">{r50_60}</td></tr>
                        <tr><td>60-70</td><td style="text-align:center;">{r60_70}</td></tr>
                        <tr><td>70-80</td><td style="text-align:center;">{r70_80}</td></tr>
                        <tr><td>80-90</td><td style="text-align:center;">{r80_90}</td></tr>
                        <tr><td>90-100</td><td style="text-align:center;">{r90_100}</td></tr>
                        <tr><td>නොපැමිණී (Absent)</td><td style="text-align:center;">{r_abs}</td></tr>
                    </table>
                </div>

                <div class="notes-box">
                    <h4>📝 ප්‍රතිඵල සමාලෝචනය පිළිබඳ පොදු විශ්ලේෂණ සටහන</h4>
                    <p>විෂයභාර ගුරුභවතාගේ නිගමන හා සටහන්:</p>
                    <p style="margin-top:20px; border-bottom:1px dotted #000; min-height:80px;">මෙම වාරයේ පන්තියේ සමස්ත සාධන මට්ටම යහපත් තත්වයක පවතී. අඩු ලකුණු ලබාගත් සිසුන් සඳහා විශේෂ වැඩසටහන් ක්‍රියාත්මක කළ යුතුය.</p>
                </div>
            </div>

            <div class="signatures">
                <div>...............................................<br>(විෂයභාර ගුරුභවතා)</div>
                <div>...............................................<br>(අංශ ප්‍රධාන ගුරුභවතා)</div>
                <div>...............................................<br>(පරිවේණාධිපති හිමි)</div>
            </div>
        </body>
        </html>
        """

    st.download_button(
        label="📥 නිල වාර්තාව Download කරගන්න (Printable Document)",
        data=html_doc,
        file_name=f"{sel_grade}_{sel_year}_{sel_subject}_Report.html",
        mime="text/html",
        type="primary",
        use_container_width=True,
    )

# ----------------------------------------------------
# TAB 3: STUDENT-WISE DEEP ANALYSIS
# ----------------------------------------------------
with tab3:
  st.header("👤 ශිෂ්‍යානුබද්ධ ප්‍රගති විශ්ලේෂණය")
  if st.session_state.student_data.empty:
    st.info("විශ්ලේෂණය සඳහා කිසිදු දත්තයක් ඇතුළත් කර නොමැත.")
  else:
    st_year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="st_year")

    filtered_by_year = st.session_state.student_data[
        st.session_state.student_data["Year"] == st_year
    ]
    if filtered_by_year.empty:
      st.info("මෙම වර්ෂය සඳහා දත්ත නොමැත.")
    else:
      student_list = filtered_by_year["Student ID"].unique()
      selected_student = st.selectbox(
          "විශ්ලේෂණය සඳහා ශිෂ්‍ය අංකය තෝරන්න:", student_list, key="st_select"
      )

      student_df = filtered_by_year[
          filtered_by_year["Student ID"] == selected_student
      ]
      s_grade = student_df["Grade"].iloc[0]

      st.subheader(
          f"විභාග අංකය: {selected_student} | ශ්‍රේණිය: {s_grade} | වර්ෂය:"
          f" {st_year}"
      )

      plot_df = student_df.copy()
      plot_df["DisplayMarks"] = plot_df.apply(
          lambda r: 0 if str(r.get("Status")) == "Absent" else r["Marks"], axis=1
      )

      fig = px.bar(
          plot_df,
          x="Subject",
          y="DisplayMarks",
          color="Term",
          barmode="group",
          title=f"{st_year} වර්ෂයේ වාර 3 හි විෂයයන් 10 ලකුණු සංසන්දනය",
          text_auto=True,
      )
      st.plotly_chart(fig, use_container_width=True)

      # Duplicate දත්ත නිසා දෝෂ මඟහරවා ගැනීමට pivot_table භාවිතා කර ඇත
      pivot_df = (
          student_df.pivot_table(
              index="Subject", columns="Term", values="Marks", aggfunc="first"
          )
          .fillna(0)
      )
      st.write("### වාර 3 හි විෂයයන් අනුව ලකුණු සාරාංශය")
      st.dataframe(pivot_df, use_container_width=True)

# ----------------------------------------------------
# TAB 4: CLASS OVERALL ANALYSIS
# ----------------------------------------------------
with tab4:
  st.header("🏫 සමස්ත පන්ති සාධන විශ්ලේෂණය")
  if st.session_state.student_data.empty:
    st.info("විශ්ලේෂණය සඳහා කිසිදු දත්තයක් ඇතුළත් කර නොමැත.")
  else:
    col_cl1, col_cl2, col_cl3 = st.columns(3)
    with col_cl1:
      c_grade = st.selectbox("නිරීක්ෂණයට ශ්‍රේණිය තෝරන්න:", GRADES, key="cl_grade")
    with col_cl2:
      c_year = st.selectbox("නිරීක්ෂණයට වර්ෂය තෝරන්න:", YEARS, index=1, key="cl_year")
    with col_cl3:
      c_term = st.selectbox(
          "නිරීක්ෂණයට වාරය තෝරන්න:",
          ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"],
          key="cl_term",
      )

    class_df = st.session_state.student_data[
        (st.session_state.student_data["Grade"] == c_grade)
        & (st.session_state.student_data["Year"] == c_year)
        & (st.session_state.student_data["Term"] == c_term)
    ]

    if class_df.empty:
      st.warning("මෙම පන්තිය, වර්ෂය සහ වාරය සඳහා දත්ත නොමැත.")
    else:
      valid_class_df = class_df[class_df["Status"] != "Absent"]
      fig_class = px.box(
          valid_class_df,
          x="Subject",
          y="Marks",
          points="all",
          title=(
              f"{c_grade} ({c_year}) - {c_term} විෂයයන් අනුව ලකුණු ව්‍යාප්තිය"
          ),
      )
      st.plotly_chart(fig_class, use_container_width=True)

# ----------------------------------------------------
# TAB 5: DATA MANAGEMENT & EDITING CENTER
# ----------------------------------------------------
with tab5:
  st.header("⚙️ දත්ත පාලනය හා සංස්කරණ මධ්‍යස්ථානය")
  st.info(
      "පහත වගුවේ ඇති දත්ත (Student ID, Year, Term, Marks, Status ආදී ඕනෑම"
      " දෙයක්) ඔබට සෘජුවම සංස්කරණය (Edit) කළ හැක. නොපැමිණි සිසුන් සඳහා Status"
      " එක 'Absent' ලෙස වෙනස් කළ හැක."
  )

  # Using st.data_editor for interactive data editing
  edited_df = st.data_editor(
      st.session_state.student_data,
      num_rows="dynamic",
      use_container_width=True,
      key="student_data_editor",
  )

  col_ed1, col_ed2 = st.columns(2)
  with col_ed1:
    if st.button(
        "💾 සංස්කරණය කළ දත්ත Save කරන්න",
        type="primary",
        use_container_width=True,
    ):
      st.session_state.student_data = edited_df
      save_marks_data(st.session_state.student_data)
      st.success("දත්ත සාර්ථකව සංස්කරණය කර සුරකින ලදී!")
      st.rerun()

  st.divider()
  st.subheader("🧹 දත්ත ඉවත් කිරීම හා කළමනාකරණය")

  col_del1, col_del2 = st.columns(2)
  with col_del1:
    if st.button(
        "🗑️ පරීක්ෂණ දත්ත සියල්ල ඉවත් කරන්න (Clear All Data)",
        type="secondary",
        use_container_width=True,
    ):
      st.session_state.student_data = pd.DataFrame(columns=[
          "Student ID",
          "Grade",
          "Year",
          "Term",
          "Subject",
          "Marks",
          "Status",
      ])
      save_marks_data(st.session_state.student_data)
      st.success("සියලු දත්ත සාර්ථකව පද්ධතියෙන් ඉවත් කරන ලදී!")
      st.rerun()

  with col_del2:
    if admin_access:
      if st.button(
          "🔓 සියලුම Locked Data Unlock කරන්න (Admin Only)",
          use_container_width=True,
      ):
        st.session_state.student_data["Status"] = "Draft"
        save_marks_data(st.session_state.student_data)
        st.success("සියලුම දත්ත Unlock කරන ලදී!")
        st.rerun()
