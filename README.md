
# 나만의 체중·식단 관리 (Streamlit)

갱년기·당뇨 전단계 맞춤 관리용 개인 대시보드입니다.  
- 음식 DB 기반 **칼로리 자동 계산**
- **체중 추세** 시각화
- **ACL 수술 이력 고려** 간단 운동 가이드
- CSV 업로드로 식단 대량 입력

## 파일 구성
- `app.py` : 스트림릿 앱
- `foods_korean.csv` : 음식 DB (서빙, kcal, 탄/단/지)
- `sample_meal_log.csv` : 업로드 예시

## 로컬 실행
```bash
pip install streamlit pandas
streamlit run app.py
```

## GitHub & Streamlit Community Cloud 배포
1. GitHub에 새 리포지토리 생성 후 `app.py`, `foods_korean.csv`, `sample_meal_log.csv` 업로드
2. [Streamlit Community Cloud](https://share.streamlit.io/) 접속 → **New app**
3. 방금 만든 GitHub 리포 선택, main branch, `app.py` 지정 → Deploy
4. 앱이 열리면 왼쪽 사이드바에서 음식 DB를 교체 업로드할 수 있습니다.

## 식단 CSV 포맷
`sample_meal_log.csv` 참고 (컬럼: `date, meal, food, servings`)  
- `date` : YYYY-MM-DD
- `meal` : 아침/점심/저녁/간식
- `food` : `foods_korean.csv`의 food 값과 일치해야 자동 kcal 계산
- `servings` : 배수(0.25 단위 등)

## 주의 및 면책
이 프로젝트는 교육/자기관리 목적입니다. 질병 치료를 대신하지 않습니다.  
개인 병력(당뇨 전단계, 무릎 수술 등)에 따라 **의사·물리치료사**와 상의하세요.
