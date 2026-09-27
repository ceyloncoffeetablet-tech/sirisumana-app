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
        df = pd.DataFrame(data)
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
    "⚙️ දත්ත පාලනය",
])

# Grade List
GRADES = [
    "4 ශ්‍රේණිය",
    "1 ශ්‍රේණිය",
    "2 ශ්‍රේණිය",
    "3 ශ්‍රේණිය",
    "5 ශ්‍රේණිය",
    "English Medium 1",
    "English Medium 2",
    "English Medium 3",
    "English Medium 4",
    "English Medium 5",
]

# Years List
YEARS = ["2025", "2026", "2027", "2028", "2029", "2030"]

# List of all 10 subjects
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


# Helper Function for Grading (Supports AB and numbers)
def get_grade(marks):
  if str(marks).strip().upper() == "AB":
    return "AB"
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
  except:
    return "AB"


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
# TAB 1: DATA ENTRY (MANUAL / PHOTO / PDF with Edit Preview)
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
      if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        st.error("කරුණාකර API Key එක සකසන්න.")
      else:
        try:
          with st.spinner("AI මඟින් Photo එක පරීක්ෂා කරමින් පවතී..."):
            client = genai.Client(api_key=GEMINI_API_KEY)
            prompt_text = (
                "මෙම ඡායාරූපයෙහි ඇති ශිෂ්‍ය ලකුණු ලේඛනයෙන් සෑම ශිෂ්‍යයෙකුගේම"
                " විභාග අංකය (Student ID) සහ ලකුණු පහත JSON ආකෘතියෙන් ලබාදෙන්න.\n"
                "අවශ්‍ය විෂයන්: ත්‍රිපිටක ධර්මය (Tripitaka), සිංහල (Sinhala),"
                " පාලි (Pali), සංස්කෘත (Sanskrit), ගණිතය (Maths), ඉංග්‍රීසි"
                " (English), ඉතිහාසය (History), සමාජ විද්‍යාව (Social Sci.),"
                " සෞඛ්‍ය විද්‍යාව (Health Sci.), භූගෝල විද්‍යාව (Geog. Phy.)\n"
                "සිසුවෙකු නොපැමිණ ඇත්නම් (Absent) ලකුණු වෙනුවට 'AB' ලෙස"
                " යොදන්න. ලකුණු නැතිනම් 0 යොදන්න.\n"
                "JSON Format:\n"
                '[{"Student ID": "3017", "Marks": {"ත්‍රිපිටක ධර්මය'
                ' (Tripitaka)": 48, "සිංහල (Sinhala)": "AB", "පාලි (Pali)": 60,'
                ' "සංස්කෘත (Sanskrit)": 55, "ගණිතය (Maths)": 59, "ඉංග්‍රීසි'
                ' (English)": 31, "ඉතිහාසය (History)": 0, "සමාජ විද්‍යාව (Social'
                ' Sci.)": 0, "සෞඛ්‍ය විද්‍යාව (Health Sci.)": 0, "භූගෝල විද්‍යාව'
                ' (Geog. Phy.)": 0}}]\n'
                "වෙනත් කිසිදු අමතර සටහනක් නොලියා pure JSON පමණක් ලබාදෙන්න."
            )
            response = client.models.generate_content(
                model="gemini-3.8-flash", contents=[img, prompt_text]
            )
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
                  new_rows.append({
                      "Student ID": s_id,
                      "Grade": scan_grade,
                      "Year": scan_year,
                      "Term": scan_term,
                      "Subject": sub,
                      "Marks": str(mark),
                      "Status": "Locked",
                  })
            if new_rows:
              st.session_state["temp_scanned_df"] = pd.DataFrame(new_rows)
              st.success(
                  "✅ AI ස්කෑන් කිරීම සාර්ථකයි! පහտින් ඇති වගුව පරීක්ෂා කර අවශ්‍ය"
                  " වෙනස්කම් කර Save කරන්න."
              )
        except Exception as e:
          st.error(f"දෝෂයක් සිදු විය: {str(e)}")

    if "temp_scanned_df" in st.session_state:
      st.subheader("✏️ ස්කෑන් කළ දත්ත පරීක්ෂා කර Edit කිරීම")
      edited_scanned_df = st.data_editor(
          st.session_state["temp_scanned_df"],
          key="scanned_data_editor",
          use_container_width=True,
      )
      if st.button("💾 මෙම දත්ත පද්ධතියට අන්තර්ගත කරන්න (Save)", type="primary"):
        st.session_state.student_data = pd.concat(
            [st.session_state.student_data, edited_scanned_df],
            ignore_index=True,
        )
        save_marks_data(st.session_state.student_data)
        del st.session_state["temp_scanned_df"]
        st.success("දත්ත සාර්ථකව සුරකින ලදී!")
        st.rerun()

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
      if not GEMINI_API_KEY or GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        st.error("කරුණාකර API Key එක සකසන්න.")
      else:
        try:
          with st.spinner("AI මඟින් PDF එක පරීක්ෂා කරමින් පවතී..."):
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
                "සිසුවෙකු නොපැමිණ ඇත්නම් (Absent) ලකුණු වෙනුවට 'AB' ලෙස"
                " යොදන්න.\n"
                "JSON Format:\n"
                '[{"Student ID": "3017", "Marks": {"ත්‍රිපිටක ධර්මය'
                ' (Tripitaka)": 48, "සිංහල (Sinhala)": "AB", "පාලි (Pali)": 60,'
                ' "සංස්කෘත (Sanskrit)": 55, "ගණිතය (Maths)": 59, "ඉංග්‍රීසි'
                ' (English)": 31, "ඉතිහාසය (History)": 0, "සමාජ විද්‍යාව (Social'
                ' Sci.)": 0, "සෞඛ්‍ය විද්‍යාව (Health Sci.)": 0, "භූගෝල විද්‍යාව'
                ' (Geog. Phy.)": 0}}]\n'
                "වෙනත් කිසිදු අමතර සටහනක් නොලියා pure JSON පමණක් ලබාදෙන්න."
            )
            response = client.models.generate_content(
                model="gemini-3.8-flash", contents=[pdf_part, prompt_text]
            )
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
                  new_rows.append({
                      "Student ID": s_id,
                      "Grade": pdf_grade,
                      "Year": pdf_year,
                      "Term": pdf_term,
                      "Subject": sub,
                      "Marks": str(mark),
                      "Status": "Locked",
                  })
            if new_rows:
              st.session_state["temp_pdf_df"] = pd.DataFrame(new_rows)
              st.success("✅ PDF ස්කෑන් කිරීම සාර්ථකයි! පහතින් පරීක්ෂා කර Save කරන්න.")
        except Exception as e:
          st.error(f"දෝෂයක් සිදු විය: {str(e)}")

    if "temp_pdf_df" in st.session_state:
      st.subheader("✏️ PDF ස්කෑන් කළ දත්ත පරීක්ෂා කර Edit කිරීම")
      edited_pdf_df = st.data_editor(
          st.session_state["temp_pdf_df"],
          key="pdf_data_editor",
          use_container_width=True,
      )
      if st.button("💾 PDF දත්ත පද්ධතියට අන්තර්ගත කරන්න (Save)", type="primary"):
        st.session_state.student_data = pd.concat(
            [st.session_state.student_data, edited_pdf_df], ignore_index=True
        )
        save_marks_data(st.session_state.student_data)
        del st.session_state["temp_pdf_df"]
        st.success("දත්ත සාර්ථකව සුරකින ලදී!")
        st.rerun()

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
            "ලියාපදිංචි සිසුන්ගෙන් තෝරන්න:",
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
      st.subheader("විෂයයන් 10 සහ ලකුණු (නොපැමිණි නම් AB ලියන්න)")
      marks_dict = {}
      for sub in SUBJECTS:
        marks_dict[sub] = st.text_input(
            f"{sub} ලකුණු (ලකුණු හෝ AB):", value="0", key=f"mark_{sub}"
        )

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
          "⛔ මෙම ශිෂ්‍යයාගේ ලකුණු දැනටමත් Lock කර ඇත. වෙනස් කිරීමට Admin"
          " අමතන්න."
      )
    else:
      btn_col1, btn_col2 = st.columns(2)
      with btn_col1:
        if st.button("💾 තාවකාලිකව සුරකින්න (Save Draft)", use_container_width=True):
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
              new_rows.append({
                  "Student ID": student_id,
                  "Grade": grade,
                  "Year": year,
                  "Term": term,
                  "Subject": sub,
                  "Marks": str(mark),
                  "Status": "Draft",
              })
            st.session_state.student_data = pd.concat(
                [st.session_state.student_data, pd.DataFrame(new_rows)],
                ignore_index=True,
            )
            save_marks_data(st.session_state.student_data)
            st.success("ලකුණු තාවකාලිකව සුරකින ලදී!")
          else:
            st.warning("ਕරුණාකර ශිෂ්‍ය අංකය ඇතුළත් කරන්න.")

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
              new_rows.append({
                  "Student ID": student_id,
                  "Grade": grade,
                  "Year": year,
                  "Term": term,
                  "Subject": sub,
                  "Marks": str(mark),
                  "Status": "Locked",
              })
            st.session_state.student_data = pd.concat(
                [st.session_state.student_data, pd.DataFrame(new_rows)],
                ignore_index=True,
            )
            save_marks_data(st.session_state.student_data)
            st.success("ලකුණු සාර්ථකව Lock කරන ලදී!")
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
    st.info("මෙම තේරීම සඳහා දත්ත ඇතුළත් කර නොමැත.")
  else:
    sub_df["සාමාර්ථය"] = sub_df["Marks"].apply(get_grade)
    sub_df["සාධන මට්ටම"] = sub_df["Marks"].apply(
        lambda x: "AB" if str(x).upper() == "AB" else f"{x}%"
    )
    sub_df["ප්‍රගති මැනීම"] = sub_df["Marks"].apply(
        lambda x: (
            "නොපැමිණ ඇත (AB)"
            if str(x).upper() == "AB"
            else (
                "යහපත්"
                if float(x if str(x).replace(".", "").isdigit() else 0) >= 65
                else (
                    "මධ්‍යම"
                    if float(x if str(x).replace(".", "").isdigit() else 0) >= 35
                    else "දුර්වල"
                )
            )
        )
    )
    sub_df["විශ්ලේෂණයන්"] = sub_df["Marks"].apply(
        lambda x: (
            "විභාගයට පෙනී නොසිට ඇත"
            if str(x).upper() == "AB"
            else (
                "ලකුණු මට්ටම උසස් කරගත යුතුය"
                if float(x if str(x).replace(".", "").isdigit() else 0) < 50
                else "සාධනීය මට්ටමක පවතී"
            )
        )
    )

    display_sub_df = sub_df.reset_index(drop=True)
    display_sub_df.index += 1
    display_sub_df = display_sub_df.reset_index().rename(
        columns={"index": "අනු අංකය", "Student ID": "විභාග අංකය"}
    )
    show_table = display_sub_df[[
        "අනු අංකය",
        "විභාග අංකය",
        "Marks",
        "සාධන මට්ටම",
        "සාමාර්ථය",
        "ප්‍රගති මැනීම",
        "විශ්ලේෂණයන්",
    ]]

    st.dataframe(show_table, use_container_width=True)

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
            </style>
        </head>
        <body>
            <div class="header-box">
                <h2>මහ/දෙනු/ සිරිසුමන ද්විභාෂා පිරිවෙණ</h2>
                <p>වාර පරීක්ෂණ ප්‍රතිඵල විශ්ලේෂණ වාර්තාව ({sel_term}) - {sel_year}</p>
                <p>ශ්‍රේණිය :- {sel_grade} | විෂය :- {sel_subject}</p>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>අනු අංකය</th><th>විභාග අංකය</th><th>සාධන මට්ටම</th><th>සාමාර්ථය</th><th>ප්‍රගති මැනීම</th><th>විශ්ලේෂණයන්</th>
                    </tr>
                </thead>
                <tbody>{rows_html}</tbody>
            </table>
        </body>
        </html>
        """

    st.download_button(
        label="📥 නිල වාර්තාව Download කරගන්න",
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
    st.info("දත්ත නොමැත.")
  else:
    st_year = st.selectbox("වර්ෂය තෝරන්න:", YEARS, index=1, key="st_year")
    filtered_by_year = st.session_state.student_data[
        st.session_state.student_data["Year"] == st_year
    ]
    if not filtered_by_year.empty:
      student_list = filtered_by_year["Student ID"].unique()
      selected_student = st.selectbox("ශිෂ්‍ය අංකය තෝරන්න:", student_list)
      student_df = filtered_by_year[
          filtered_by_year["Student ID"] == selected_student
      ].copy()
      student_df["NumericMarks"] = pd.to_numeric(
          student_df["Marks"], errors="coerce"
      ).fillna(0)
      fig = px.bar(
          student_df,
          x="Subject",
          y="NumericMarks",
          color="Term",
          barmode="group",
          title="වාර 3 හි විෂයයන් ලකුණු සංසන්දනය (AB සඳහා 0 ලෙස දැක්වේ)",
      )
      st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------------------
# TAB 4: CLASS OVERALL ANALYSIS
# ----------------------------------------------------
with tab4:
  st.header("🏫 සමස්ත පන්ති සාධන විශ්ලේෂණය")
  if not st.session_state.student_data.empty:
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
          class_df, x="Subject", y="NumericMarks", title="විෂයයන් අනුව ලකුණු ව්‍යාප්තිය"
      )
      st.plotly_chart(fig_class, use_container_width=True)

# ----------------------------------------------------
# TAB 5: DATA MANAGEMENT, LIVE EDITING & DOWNLOAD
# ----------------------------------------------------
with tab5:
  st.header("⚙️ දත්ත පාලන සහ සෘජු සංස්කරණ මධ්‍යස්ථානය (Data Editor)")
  st.info(
      "💡 ඔබට පහත වගුව තුළ ඇති ඕනෑම අගයක් (ලකුණු, විභාග අංක, AB ආදී වශයෙන්)"
      " සෘජුවම ක්ලික් කර වෙනස් කරගත හැක! වෙනස් කළ පසු පහත ඇති Save බොත්තම"
      " ක්ලික් කරන්න."
  )

  # Live Editable DataFrame Table
  edited_master_df = st.data_editor(
      st.session_state.student_data,
      key="master_data_editor",
      use_container_width=True,
      num_rows="dynamic",
  )

  col_sv1, col_sv2 = st.columns(2)
  with col_sv1:
    if st.button(
        "💾 වගුවේ කළ වෙනස්කම් Save කරගන්න",
        type="primary",
        use_container_width=True,
    ):
      st.session_state.student_data = edited_master_df
      save_marks_data(st.session_state.student_data)
      st.success("සියලු වෙනස්කම් සාර්ථකව සුරකින ලදී!")
      st.rerun()

  st.divider()
  st.subheader("📥 දත්ත උපස්ථ කරගැනීම (Backup Data)")

  if not st.session_state.student_data.empty:
    json_data = st.session_state.student_data.to_json(
        orient="records", force_ascii=False
    )
    st.download_button(
        label="📥 දත්ත සියල්ල JSON ලෙස Download කරගන්න",
        data=json_data,
        file_name="student_marks_backup.json",
        mime="application/json",
        use_container_width=True,
    )

    csv_data = st.session_state.student_data.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 දත්ත සියල්ල CSV ලෙස Download කරගන්න",
        data=csv_data,
        file_name="student_marks_backup.csv",
        mime="text/csv",
        use_container_width=True,
    )
  else:
    st.info("ඩවුන්ලෝඩ් කිරීමට දත්ත කිසිවක් නොමැත.")

  st.divider()
  st.subheader("🧹 දත්ත ඉවත් කිරීම (Reset Data)")
  col_del1, col_del2 = st.columns(2)
  with col_del1:
    if st.button("🗑️ සියලු දත්ත ඉවත් කරන්න", use_container_width=True):
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
      st.success("දත්ත ඉවත් කරන ලදී!")
      st.rerun()

  with col_del2:
    if admin_access:
      if st.button("🔓 සියලුම Locked Data Unlock කරන්න", use_container_width=True):
        st.session_state.student_data["Status"] = "Draft"
        save_marks_data(st.session_state.student_data)
        st.success("දත්ත Unlock කරන ලදී!")
        st.rerun()
