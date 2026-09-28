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
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")

# Permanent Data Files
DATA_FILE = "student_marks.json"
ROSTER_FILE = "student_roster.json"


# Helper Functions for Marks Data Persistence
def load_marks_data():
  if os.path.exists(DATA_FILE):
    try:
      with open(DATA_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        if data:
          df = pd.DataFrame(data)
          required_cols = [
              "Student ID",
              "Grade",
              "Year",
              "Term",
              "Subject",
              "Marks",
              "Status",
          ]
          for col in required_cols:
            if col not in df.columns:
              df[col] = ""
          if "Year" not in df.columns:
            df["Year"] = "2026"
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

# Grade List
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


# Function to get subjects based on grade
def get_subjects_for_grade(grade_name):
  if grade_name in ["මූලික ශ්‍රේණිය", "1 ශ්‍රේණිය", "2 ශ්‍රේණිය"]:
    return [
        "ත්‍රිපිටක ධර්මය (Tripitaka)",
        "සිංහල (Sinhala)",
        "පාලි (Pali)",
        "සංස්කෘත (Sanskrit)",
        "ගණිතය (Maths)",
        "ඉංග්‍රීසි (English)",
    ]
  else:
    return [
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
  except Exception:
    return str(marks)


# Automatic Data Cleaner & Mapper for Imported CSV
def clean_imported_dataframe(df):
  col_rename = {}
  for col in df.columns:
    c_lower = str(col).strip().lower()
    if "student" in c_lower or "id" in c_lower or "අංක" in c_lower:
      col_rename[col] = "Student ID"
    elif "grade" in c_lower or "ශ්‍රේණි" in c_lower:
      col_rename[col] = "Grade"
    elif "year" in c_lower or "වර්ෂ" in c_lower:
      col_rename[col] = "Year"
    elif "term" in c_lower or "වාර" in c_lower:
      col_rename[col] = "Term"
    elif "subject" in c_lower or "විෂය" in c_lower:
      col_rename[col] = "Subject"
    elif "mark" in c_lower or "ලකුණු" in c_lower:
      col_rename[col] = "Marks"
    elif "status" in c_lower:
      col_rename[col] = "Status"
  df = df.rename(columns=col_rename)

  required_cols = [
      "Student ID",
      "Grade",
      "Year",
      "Term",
      "Subject",
      "Marks",
      "Status",
  ]
  for col in required_cols:
    if col not in df.columns:
      df[col] = ""

  def clean_grade_name(g):
    g_str = str(g).strip()
    for valid_g in GRADES:
      if valid_g in g_str or g_str in valid_g:
        return valid_g
    return g_str

  def clean_subject_name(s):
    s_str = str(s).strip()
    all_possible_subs = [
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
    for valid_s in all_possible_subs:
      base_name = valid_s.split("(")[0].strip()
      if base_name in s_str or s_str in valid_s:
        return valid_s
    return s_str

  df["Grade"] = df["Grade"].apply(clean_grade_name)
  df["Subject"] = df["Subject"].apply(clean_subject_name)
  df["Year"] = df["Year"].astype(str).str.strip()
  df["Term"] = df["Term"].astype(str).str.strip()
  df["Student ID"] = df["Student ID"].astype(str).str.strip()

  return df[required_cols]


# ----------------------------------------------------
# TAB 0: STUDENT ROSTER MANAGEMENT
# ----------------------------------------------------
with tab0:
  st.header("📋 පන්ති අනුව ශිෂ්‍ය නාම ලේඛනය ලියාපදිංචිය")
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
# TAB 1: DATA ENTRY
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

  if "Photo" in entry_method:
    st.subheader("📸 ඡායාරූපයක් මඟින් ලකුණු ලබා ගැනීම")
    uploaded_img = st.file_uploader(
        "ලකුණු පත්‍රිකාවේ Image එක Upload කරන්න", type=["jpg", "jpeg", "png"]
    )

    if uploaded_img is not None:
      st.image(
          uploaded_img,
          caption="අප්ලෝඩ් කරන ලද ලකුණු පත්‍රිකාව (විශාල කර බැලිය හැක)",
          use_container_width=True,
      )

    col_scan1, col_scan2, col_scan3 = st.columns(3)
    with col_scan1:
      scan_grade = st.selectbox("ශ්‍රේණිය / පන්තිය:", GRADES, key="img_scan_grade")
    with col_scan2:
      scan_year = st.selectbox("වර්ෂය:", YEARS, index=1, key="img_scan_year")
    with col_scan3:
      scan_term = st.selectbox(
          "වාරය:", ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"], key="img_scan_term"
      )

    current_scan_subjects = get_subjects_for_grade(scan_grade)

    if uploaded_img and st.button(
        "🔍 Photo එක Scan කර දත්ත ලබා ගන්න", type="primary", key="btn_img_scan"
    ):
      if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        st.error("කරුණාකර API Key එක සකසන්න.")
      else:
        success_scan = False
        response = None
        with st.spinner(
            "AI මඟින් Photo එක පරීක්ෂා කරමින් පවතී... (ටිකක් රැඳී සිටින්න)"
        ):
          client = genai.Client(api_key=GEMINI_API_KEY)
          sub_list_str = ", ".join(current_scan_subjects)
          prompt_text = (
              f"මෙම ඡායාරූපයෙහි ඇති ශිෂ්‍ය ලකුණු ලේඛනයෙන් සෑම ශිෂ්‍යයෙකුගේම"
              f" විභාග අංකය (Student ID) සහ ලකුණු පහත JSON ආකෘතියෙන් ලබාදෙන්න.\n"
              f"අවශ්‍ය විෂයන් පමණක්: {sub_list_str}\n"
              "සිසුවෙකු නොපැමිණ ඇත්නම් ලකුණු සඳහා 'AB' ලෙස යොදන්න."
          )

          # Retry mechanism for 503 or transient errors
          for attempt in range(3):
            try:
              response = client.models.generate_content(
                  model="gemini-3.8-flash",
                  contents=[Image.open(uploaded_img), prompt_text],
              )
              success_scan = True
              break
            except Exception as api_err:
              if "503" in str(api_err) or "UNAVAILABLE" in str(api_err):
                time.sleep(3)
              else:
                raise api_err

        if success_scan and response:
          try:
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
                if sub in current_scan_subjects:
                  m_val = str(mark).strip().upper()
                  if m_val != "AB":
                    try:
                      m_val = int(mark)
                    except Exception:
                      m_val = 0
                  new_rows.append({
                      "Student ID": s_id,
                      "Grade": scan_grade,
                      "Year": scan_year,
                      "Term": scan_term,
                      "Subject": sub,
                      "Marks": m_val,
                      "Status": "Locked",
                  })
            if new_rows:
              extracted_df = pd.DataFrame(new_rows)
              st.session_state.student_data = pd.concat(
                  [st.session_state.student_data, extracted_df],
                  ignore_index=True,
              )
              save_marks_data(st.session_state.student_data)
              st.success("✅ දත්ත සාර්ථකව ඇතුළත් කරගන්නා ලදී!")
          except Exception as e:
            st.error(f"දත්ත සැකසීමේ දෝෂයක් සිදු විය: {str(e)}")
        else:
          st.error(
              "⚠️ සේවාව තාවකාලිකව කාර්යබහුලයි. කරුණාකර තවත් වාරයක් 'Photo එක"
              " Scan කර දත්ත ලබා ගන්න' බටන් එක ක්ලික් කරන්න."
          )

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

    current_pdf_subjects = get_subjects_for_grade(pdf_grade)

    if uploaded_pdf and st.button(
        "📄 PDF එක Scan කර දත්ත ලබා ගන්න", type="primary", key="btn_pdf_scan"
    ):
      if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        st.error("කරුණාකර API Key එක සකසන්න.")
      else:
        success_pdf = False
        response = None
        with st.spinner(
            "AI මඟින් PDF එක පරීක්ෂා කරමින් පවතී... (ටිකක් රැඳී සිටින්න)"
        ):
          client = genai.Client(api_key=GEMINI_API_KEY)
          pdf_bytes = uploaded_pdf.read()
          pdf_part = types.Part.from_bytes(
              data=pdf_bytes, mime_type="application/pdf"
          )
          sub_list_str = ", ".join(current_pdf_subjects)
          prompt_text = (
              f"මෙම PDF ගොනුවෙහි ඇති ශිෂ්‍ය ලකුණු ලේඛනයෙන් සෑම ශිෂ්‍යයෙකුගේම"
              f" විභාග අංකය (Student ID) සහ ලකුණු පහත JSON ආකෘතියෙන් ලබාදෙන්න.\n"
              f"අවශ්‍ය විෂයන් පමණක්: {sub_list_str}\n"
              "සිසුවෙකු නොපැමිණ ඇත්නම් ලකුණු සඳහා 'AB' ලෙස යොදන්න."
          )

          for attempt in range(3):
            try:
              response = client.models.generate_content(
                  model="gemini-2.5-flash", contents=[pdf_part, prompt_text]
              )
              success_pdf = True
              break
            except Exception as api_err:
              if "503" in str(api_err) or "UNAVAILABLE" in str(api_err):
                time.sleep(3)
              else:
                raise api_err

        if success_pdf and response:
          try:
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
                if sub in current_pdf_subjects:
                  m_val = str(mark).strip().upper()
                  if m_val != "AB":
                    try:
                      m_val = int(mark)
                    except Exception:
                      m_val = 0
                  new_rows.append({
                      "Student ID": s_id,
                      "Grade": pdf_grade,
                      "Year": pdf_year,
                      "Term": pdf_term,
                      "Subject": sub,
                      "Marks": m_val,
                      "Status": "Locked",
                  })
            if new_rows:
              extracted_df = pd.DataFrame(new_rows)
              st.session_state.student_data = pd.concat(
                  [st.session_state.student_data, extracted_df],
                  ignore_index=True,
              )
              save_marks_data(st.session_state.student_data)
              st.success("✅ දත්ත සාර්ථකව ඇතුළත් කරගන්නා ලදී!")
          except Exception as e:
            st.error(f"දත්ත සැකසීමේ දෝෂයක් සිදු විය: {str(e)}")
        else:
          st.error(
              "⚠️ සේවාව තාවකාලිකව කාර්යබහුලයි. කරුණාකර තවත් වාරයක් උත්සාහ"
              " කරන්න."
          )

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
      current_subjects = get_subjects_for_grade(grade)
      student_id = st.text_input("ඇතුළත් වීමේ අංකය / විභාග අංකය (Index No):")

    with col2:
      st.subheader(f"{grade} සඳහා අදාළ විෂයයන් සහ ලකුණු")
      marks_dict = {}
      for sub in current_subjects:
        marks_dict[sub] = st.text_input(
            f"{sub} ලකුණු (ලකුණු හෝ AB):", value="0", key=f"manual_{sub}"
        )

    if st.button(
        "💾 ලකුණු සුරකින්න (Save Marks)", type="primary", use_container_width=True
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
          m_val = mark.strip().upper()
          if m_val != "AB":
            try:
              m_val = int(mark)
            except Exception:
              m_val = 0
          new_rows.append({
              "Student ID": student_id,
              "Grade": grade,
              "Year": year,
              "Term": term,
              "Subject": sub,
              "Marks": m_val,
              "Status": "Locked",
          })
        st.session_state.student_data = pd.concat(
            [st.session_state.student_data, pd.DataFrame(new_rows)],
            ignore_index=True,
        )
        save_marks_data(st.session_state.student_data)
        st.success("ලකුණු සාර්ථකව සුරකින ලදී!")
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
  available_subjects_for_report = get_subjects_for_grade(sel_grade)
  with col_sel2:
    sel_year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="sub_year")
  with col_sel3:
    sel_term = st.selectbox(
        "වාරය තෝරන්න:",
        ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"],
        key="sub_term",
    )
  with col_sel4:
    sel_subject = st.selectbox(
        "විෂය තෝරන්න:", available_subjects_for_report, key="sub_subject"
    )

  st.divider()

  if not st.session_state.student_data.empty:
    sub_df = st.session_state.student_data[
        (st.session_state.student_data["Grade"] == sel_grade)
        & (st.session_state.student_data["Year"] == sel_year)
        & (st.session_state.student_data["Term"] == sel_term)
        & (st.session_state.student_data["Subject"] == sel_subject)
    ].copy()
  else:
    sub_df = pd.DataFrame()

  if sub_df.empty:
    st.info("තෝරාගත් විෂය සඳහා කිසිදු දත්තයක් ඇතුළත් කර නොමැත.")
  else:
    sub_df["සාමාර්ථය"] = sub_df["Marks"].apply(get_grade)
    sub_df["සාධන මට්ටම"] = sub_df["Marks"].apply(
        lambda x: "AB" if str(x).upper() == "AB" else f"{x}%"
    )
    display_sub_df = sub_df.reset_index(drop=True)
    display_sub_df.index += 1
    display_sub_df = display_sub_df.reset_index().rename(
        columns={"index": "අනු අංකය", "Student ID": "විභාග අංකය"}
    )
    st.dataframe(
        display_sub_df[["අනු අංකය", "විභාග අංකය", "Marks", "සාමාර්ථය"]],
        use_container_width=True,
    )

# ----------------------------------------------------
# TAB 3: STUDENT-WISE DEEP ANALYSIS
# ----------------------------------------------------
with tab3:
  st.header("👤 ශිෂ්‍යානුබද්ධ ප්‍රගති විශ්ලේෂණය")
  if st.session_state.student_data.empty:
    st.info("දත්ත නොමැත.")
  else:
    st_year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="st_year")
    filtered_by_year = st.session_state.student_data[
        st.session_state.student_data["Year"] == st_year
    ]
    if not filtered_by_year.empty and "Student ID" in filtered_by_year.columns:
      student_list = filtered_by_year["Student ID"].unique()
      selected_student = st.selectbox("විභාග අංකය තෝරන්න:", student_list)
      student_df = filtered_by_year[
          filtered_by_year["Student ID"] == selected_student
      ]
      plot_df = student_df.copy()
      plot_df["NumericMarks"] = pd.to_numeric(
          plot_df["Marks"], errors="coerce"
      ).fillna(0)
      fig = px.bar(
          plot_df,
          x="Subject",
          y="NumericMarks",
          color="Term",
          barmode="group",
          title=f"{st_year} වර්ෂයේ ලකුණු සංසන්දනය",
      )
      st.plotly_chart(fig, use_container_width=True)
    else:
      st.info("මෙම වර්ෂය සඳහා දත්ත නොමැත.")

# ----------------------------------------------------
# TAB 4: CLASS OVERALL ANALYSIS
# ----------------------------------------------------
with tab4:
  st.header("🏫 සමස්ත පන්ති සාධන විශ්ලේෂණය")
  if st.session_state.student_data.empty:
    st.info("දත්ත නොමැත.")
  else:
    col_cl1, col_cl2, col_cl3 = st.columns(3)
    with col_cl1:
      c_grade = st.selectbox("ශ්‍රේණිය:", GRADES, key="cl_grade")
    with col_cl2:
      c_year = st.selectbox("වර්ෂය:", YEARS, index=1, key="cl_year")
    with col_cl3:
      c_term = st.selectbox(
          "වාරය:", ["1 වන වාරය", "2 වන වාරය", "3 වන වාරය"], key="cl_term"
      )

    class_df = st.session_state.student_data[
        (st.session_state.student_data["Grade"] == c_grade)
        & (st.session_state.student_data["Year"] == c_year)
        & (st.session_state.student_data["Term"] == c_term)
    ].copy()

    if not class_df.empty:
      class_df["NumericMarks"] = pd.to_numeric(
          class_df["Marks"], errors="coerce"
      ).fillna(0)
      fig_class = px.box(
          class_df,
          x="Subject",
          y="NumericMarks",
          points="all",
          title=f"{c_grade} ({c_year}) - {c_term} ලකුණු ව්‍යාප්තිය",
      )
      st.plotly_chart(fig_class, use_container_width=True)
    else:
      st.info("මෙම තේරීමට අදාළ දත්ත නොමැත.")

# ----------------------------------------------------
# TAB 5: DATA MANAGEMENT & DIRECT DATA EDITOR
# ----------------------------------------------------
with tab5:
  st.header("⚙️ දත්ත පාලනය හා සෘජු සංස්කරණය (Data Editor)")
  st.info("පරණ ඇප් එකෙන් ඩවුන්ලෝඩ් කරගත් CSV ගොනුව පහතින් Upload කරන්න.")

  uploaded_csv = st.file_uploader(
      "📁 පරණ ඇප් එකේ CSV ෆයිල් එක මෙහි Upload කරන්න", type=["csv"]
  )
  if uploaded_csv is not None:
    try:
      raw_imported_df = pd.read_csv(uploaded_csv)
      imported_df = clean_imported_dataframe(raw_imported_df)
      st.session_state.student_data = imported_df
      save_marks_data(imported_df)
      st.success(
          "✅ CSV ෆයිල් එක ස්වයංක්‍රීයව පිරිසිදු කර, අලුත් ඇප් එකට ගැලපෙන ලෙස"
          " සාර්ථකව ඇතුළත් කර සුරක්ෂිත කරන ලදී!"
      )
      st.rerun()
    except Exception as e:
      st.error(f"දෝෂයක් සිදු විය: {str(e)}")

  st.divider()

  if (
      st.session_state.student_data is not None
      and not st.session_state.student_data.empty
  ):
    edited_df = st.data_editor(
        st.session_state.student_data,
        num_rows="dynamic",
        use_container_width=True,
        key="student_data_editor_grid",
    )
    if st.button(
        "💾 වෙනස්කම් සුරකින්න (Save Changes)",
        type="primary",
        use_container_width=True,
    ):
      st.session_state.student_data = edited_df
      save_marks_data(st.session_state.student_data)
      st.success("දත්ත සාර්ථකව යාවත්කාලීන කර සුරක්ෂිත කරන ලදී!")
      st.rerun()
  else:
    empty_df = pd.DataFrame(
        columns=[
            "Student ID",
            "Grade",
            "Year",
            "Term",
            "Subject",
            "Marks",
            "Status",
        ]
    )
    edited_df = st.data_editor(
        empty_df, num_rows="dynamic", use_container_width=True, key="empty_editor"
    )
    if st.button("💾 දත්ත සුරකින්න", type="primary"):
      st.session_state.student_data = edited_df
      save_marks_data(edited_df)
      st.success("සාර්ථකව සුරකින ලදී!")
      st.rerun()

  st.divider()
  if st.button("🗑️ සියලුම දත්ත ඉවත් කරන්න (Clear All Data)", type="secondary"):
    st.session_state.student_data = pd.DataFrame(
        columns=[
            "Student ID",
            "Grade",
            "Year",
            "Term",
            "Subject",
            "Marks",
            "Status",
        ]
    )
    save_marks_data(st.session_state.student_data)
    st.success("සියලු දත්ත ඉවත් කරන ලදී!")
    st.rerun()
