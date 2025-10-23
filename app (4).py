
import streamlit as st
import pandas as pd
from datetime import date
from pathlib import Path

st.set_page_config(page_title="나만의 체중·식단 관리", page_icon="🍚", layout="wide")

@st.cache_data
def load_foods(path: str):
    df = pd.read_csv(path)
    needed = {"food","serving","kcal","carbs_g","protein_g","fat_g"}
    if not needed.issubset(df.columns):
        raise ValueError("foods CSV must have columns: " + ", ".join(needed))
    return df

def kcal_from_food(df_foods, name, servings=1.0):
    row = df_foods[df_foods['food'] == name]
    if row.empty: 
        return 0.0
    return float(row.iloc[0]['kcal']) * float(servings)

def kcal_from_walk(activity: str, minutes: float, weight_kg: float):
    # MET values: 느림~보통~빠름
    met_map = {"걷기(느림)": 2.8, "걷기(보통)": 3.5, "걷기(빠름)": 4.5}
    MET = met_map.get(activity, 3.5)
    # kcal/min = MET * 3.5 * kg / 200
    return MET * 3.5 * weight_kg / 200.0 * minutes

# Sidebar
st.sidebar.header("설정")
foods_file = st.sidebar.file_uploader("음식 DB(foods_korean.csv) 교체 업로드", type=["csv"], accept_multiple_files=False)
default_foods = "foods_korean.csv"
if foods_file is not None:
    foods_df = pd.read_csv(foods_file)
else:
    if Path(default_foods).exists():
        foods_df = load_foods(default_foods)
    else:
        st.sidebar.error("foods_korean.csv 파일이 앱과 같은 폴더에 있어야 합니다.")
        st.stop()

st.sidebar.write(f"등록된 음식 개수: **{len(foods_df)}**")

# Session states
if "weight_log" not in st.session_state:
    st.session_state.weight_log = pd.DataFrame(columns=["date","weight_kg","note"])
if "meal_log" not in st.session_state:
    st.session_state.meal_log = pd.DataFrame(columns=["date","meal","food","servings","kcal"])
if "exercise_log" not in st.session_state:
    st.session_state.exercise_log = pd.DataFrame(columns=["date","activity","minutes","weight_kg","kcal_burned"])

st.title("🍚 나만의 체중·식단·걷기 관리 대시보드")
st.caption("갱년기·당뇨 전단계 맞춤 관리 (의료 조언이 아닌 생활 가이드입니다. 개인 상황은 전문가와 상의하세요.)")

tabs = st.tabs(["대시보드", "식단 기록", "운동(걷기) 기록", "운동 가이드", "체중 기록", "음식 DB"])

# Dashboard
with tabs[0]:
    st.subheader("오늘 요약")
    today = date.today().isoformat()
    today_meals = st.session_state.meal_log[st.session_state.meal_log["date"] == today]
    today_kcal_in = today_meals["kcal"].sum() if not today_meals.empty else 0
    today_ex = st.session_state.exercise_log[st.session_state.exercise_log["date"] == today]
    today_kcal_out = today_ex["kcal_burned"].sum() if not today_ex.empty else 0
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("오늘 섭취 열량(kcal)", f"{today_kcal_in:.0f}")
    with col2:
        st.metric("오늘 소모 열량(kcal)", f"{today_kcal_out:.0f}")
    with col3:
        st.metric("에너지 밸런스", f"{today_kcal_in - today_kcal_out:.0f} kcal")
    with col4:
        if not st.session_state.weight_log.empty:
            latest_w = st.session_state.weight_log.sort_values("date").iloc[-1]["weight_kg"]
            st.metric("현재 체중(kg)", f"{latest_w}")
        else:
            st.metric("현재 체중(kg)", "—")

    st.divider()
    st.subheader("최근 체중 추세")
    if not st.session_state.weight_log.empty:
        w = st.session_state.weight_log.sort_values("date").copy()
        w["date"] = pd.to_datetime(w["date"])
        st.line_chart(w.set_index("date")["weight_kg"])
    else:
        st.info("체중을 한 번 이상 기록하면 선그래프가 표시됩니다.")

# Meal logging
with tabs[1]:
    st.subheader("식단 기록 추가")
    log_col1, log_col2 = st.columns([2,1])
    with log_col1:
        sel_date = st.date_input("날짜", value=date.today())
        meal_type = st.selectbox("끼니", ["아침","점심","저녁","간식"])
        food = st.selectbox("음식", foods_df["food"].tolist(), index=foods_df["food"].tolist().index("플레인요거트") if "플레인요거트" in foods_df["food"].tolist() else 0)
        servings = st.number_input("서빙 수(기본=1)", min_value=0.25, max_value=5.0, step=0.25, value=1.0)
        kcal = kcal_from_food(foods_df, food, servings)
        st.write(f"계산된 열량: **{kcal:.0f} kcal**")
        if st.button("기록 추가"):
            new_row = {"date": sel_date.isoformat(),"meal": meal_type,"food": food,"servings": servings,"kcal": kcal}
            st.session_state.meal_log = pd.concat([st.session_state.meal_log, pd.DataFrame([new_row])], ignore_index=True)
            st.success("기록되었습니다!")

    with log_col2:
        st.markdown("**CSV 업로드(선택)**")
        up = st.file_uploader("sample_meal_log.csv 형식", type=["csv"])
        if up is not None:
            up_df = pd.read_csv(up)
            if "kcal" not in up_df.columns:
                rows = []
                for _, r in up_df.iterrows():
                    k = kcal_from_food(foods_df, r["food"], r.get("servings", 1))
                    rows.append(k)
                up_df["kcal"] = rows
            st.session_state.meal_log = pd.concat([st.session_state.meal_log, up_df], ignore_index=True)
            st.success(f"{len(up_df)}건 업로드됨")

    st.divider()
    st.subheader("기록된 식단")
    if st.session_state.meal_log.empty:
        st.info("아직 기록이 없습니다.")
    else:
        st.dataframe(st.session_state.meal_log.sort_values(["date","meal"]))
        day = st.date_input("일자별 합계 보기", value=date.today(), key="sum_date")
        ddf = st.session_state.meal_log[st.session_state.meal_log["date"] == day.isoformat()]
        st.write(f"**{day.isoformat()} 섭취 열량 합계: {ddf['kcal'].sum():.0f} kcal**")

# Exercise (Walking) logging
with tabs[2]:
    st.subheader("걷기 기록 추가 (칼로리 자동 계산)")
    e_col1, e_col2 = st.columns([2,1])
    with e_col1:
        e_date = st.date_input("날짜", value=date.today(), key="e_date")
        activity = st.selectbox("활동", ["걷기(느림)","걷기(보통)","걷기(빠름)"])
        minutes = st.number_input("시간(분)", min_value=5, max_value=240, value=30, step=5)
        # Prefer latest logged body weight if available
        if not st.session_state.weight_log.empty:
            latest_w = float(st.session_state.weight_log.sort_values("date").iloc[-1]["weight_kg"])
        else:
            latest_w = 60.0
        weight_kg = st.number_input("체중(kg) (칼로리 계산용)", min_value=30.0, max_value=200.0, value=latest_w, step=0.5)
        kcal_burned = kcal_from_walk(activity, minutes, weight_kg)
        st.write(f"예상 소모 열량: **{kcal_burned:.0f} kcal**")
        if st.button("운동 기록 추가"):
            new_e = {"date": e_date.isoformat(), "activity": activity, "minutes": minutes, "weight_kg": weight_kg, "kcal_burned": kcal_burned}
            st.session_state.exercise_log = pd.concat([st.session_state.exercise_log, pd.DataFrame([new_e])], ignore_index=True)
            st.success("운동이 기록되었습니다.")

    with e_col2:
        st.markdown("**CSV 업로드(선택)**")
        eup = st.file_uploader("sample_exercise_log.csv 형식", type=["csv"])
        if eup is not None:
            eup_df = pd.read_csv(eup)
            # Recompute kcal if missing or zero
            if "kcal_burned" not in eup_df.columns or (eup_df["kcal_burned"].fillna(0)==0).any():
                kcals = []
                for _, r in eup_df.iterrows():
                    kcals.append(kcal_from_walk(str(r.get("activity","걷기(보통)")), float(r.get("minutes",30)), float(r.get("weight_kg",60))))
                eup_df["kcal_burned"] = kcals
            st.session_state.exercise_log = pd.concat([st.session_state.exercise_log, eup_df], ignore_index=True)
            st.success(f"{len(eup_df)}건 업로드됨")

    st.divider()
    st.subheader("기록된 걷기/운동")
    if st.session_state.exercise_log.empty:
        st.info("아직 운동 기록이 없습니다.")
    else:
        st.dataframe(st.session_state.exercise_log.sort_values(["date","activity"]))
        day_e = st.date_input("일자별 운동 합계 보기", value=date.today(), key="sum_e_date")
        edf = st.session_state.exercise_log[st.session_state.exercise_log["date"] == day_e.isoformat()]
        st.write(f"**{day_e.isoformat()} 소모 열량 합계: {edf['kcal_burned'].sum():.0f} kcal**")

# Exercise guidance
with tabs[3]:
    st.subheader("전방십자인대(ACL) 수술 이력 고려 간단 운동")
    st.write("""
    **주의:** 통증, 부기, 불안정감이 있으면 중단하고 전문의/물리치료사와 상담하세요.  
    - **유산소(저충격)**: 실내 자전거(좌식 권장) 15–30분, 빠른 걷기 20–40분, 수영/아쿠아 워킹 15–30분.  
    - **근력(주 2–3회, 무릎 친화적)**  
      - 미니 스쿼트(의자 앞, 0–45° 범위) 8–12회 × 2–3세트  
      - 브릿지 10–12회 × 2–3세트  
      - 클램셸(밴드 선택) 10–12회 × 2–3세트  
      - 레그프레스(가벼운 중량, 0–60°) 8–10회 × 2–3세트  
      - 햄스트링 컬(밴드/기구) 10–12회 × 2–3세트  
    - **유연성/균형(매일)**: 종아리·햄스트링 스트레칭 20–30초 × 2–3세트, 단측 스탠스 20–30초 × 2–3세트  
    - **RPE**(자각운동강도) 4–6 수준 유지, 통증 3/10 이상 지속 시 강도 감소
    """)
    st.caption("개인 상황에 따라 조절하세요.")

# Weight logging
with tabs[4]:
    st.subheader("체중 기록")
    w_date = st.date_input("날짜", value=date.today(), key="w_date")
    weight = st.number_input("체중(kg)", min_value=30.0, max_value=200.0, step=0.1, value=60.0)
    note = st.text_input("메모", value="")
    if st.button("체중 기록 추가"):
        new_w = {"date": w_date.isoformat(), "weight_kg": weight, "note": note}
        st.session_state.weight_log = pd.concat([st.session_state.weight_log, pd.DataFrame([new_w])], ignore_index=True)
        st.success("체중이 기록되었습니다.")
    st.divider()
    if not st.session_state.weight_log.empty:
        ww = st.session_state.weight_log.sort_values("date").copy()
        ww["date"] = pd.to_datetime(ww["date"])
        st.line_chart(ww.set_index("date")["weight_kg"])
        st.dataframe(ww)

# Foods DB
with tabs[5]:
    st.subheader("음식 DB 미리보기")
    st.dataframe(foods_df)
    st.download_button("현재 음식 DB 다운로드", data=foods_df.to_csv(index=False), file_name="foods_korean.csv", mime="text/csv")
    st.markdown("""
    **칼로리 자동 계산 원리**  
    - 각 음식의 기본 서빙 당 칼로리를 DB에서 찾고, 입력한 서빙 수를 곱합니다.  
    - 음식명이 DB에 없으면 0 kcal로 계산되니, 필요 시 DB를 수정/추가하여 업로드하세요.
    """)

st.sidebar.markdown("""
### 사용 팁
- 아침·저녁은 **요거트, 과일(토마토/사과), 통밀빵, 달걀, 고구마** 등으로 간단히 구성하면 혈당 급등을 줄이는 데 도움이 됩니다.
- 점심 구내식당은 **현미/잡곡밥 소량 + 단백질 반찬 + 채소 나물** 위주로 선택하세요.
- 식후 10–15분 가벼운 걷기를 권장합니다.
""")
