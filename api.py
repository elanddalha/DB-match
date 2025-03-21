import os
import json
import pandas as pd
import requests
from io import StringIO
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse

# ✅ GitHub에 올린 CSV 파일 RAW URL (본인의 GitHub 저장소로 변경 필요)
CSV_URL = "https://raw.githubusercontent.com/elanddalha/DB-match/main/pension_data.csv"

# ✅ GitHub에서 CSV 불러오기
def load_csv():
    try:
        response = requests.get(CSV_URL)
        response.raise_for_status()  # HTTP 에러 발생 시 예외 처리
        df = pd.read_csv(StringIO(response.text), dtype=str)  # 문자열 데이터를 데이터프레임으로 변환
        return df
    except Exception as e:
        print(f"🚨 CSV 파일 로드 실패: {str(e)}")
        return None

# ✅ 데이터 로드
df = load_csv()
if df is None:
    raise RuntimeError("🚨 CSV 파일을 불러올 수 없습니다. GitHub URL을 확인하세요.")

# ✅ FastAPI 앱 생성
app = FastAPI()

@app.get("/")
def home():
    """서버 정상 작동 확인"""
    return {"message": "퇴직연금 가입 여부 조회 API 실행 중!"}

@app.post("/check-pension")
async def check_pension(request: Request):
    try:
        data = await request.json()
        action_params = data.get('action', {}).get('params', {})
        user_input = str(action_params.get('user_input', '')).strip()

        if not user_input:
            user_input = data.get('utterance', '').strip()

        # ✅ 정규식으로 이름과 사번 분리
        import re
        pattern = r"^([가-힣]+)(\d+)$"
        match = re.match(pattern, user_input)

        if not match:
            return JSONResponse(content={
                "version": "2.0",
                "template": {
                    "outputs": [{"simpleText": {"text": "입력 형식이 올바르지 않습니다. 띄어쓰기 없이 입력해주세요. 예) 홍길동10999999"}}]
                }
            }, status_code=400)

        user_name = match.group(1)  # 이름
        user_id = match.group(2)    # 사번

        # ✅ 데이터프레임에서 조회
        if df is None:
            return JSONResponse(content={
                "version": "2.0",
                "template": {
                    "outputs": [{"simpleText": {"text": "🚨 CSV 데이터가 로드되지 않았습니다. 관리자에게 문의하세요."}}]
                }
            }, status_code=500)

        result = df[(df['name'] == user_name) & (df['id'] == user_id)]

        if not result.empty:
            pension_type = result.iloc[0]['pension_type']
            securities_firm = result.iloc[0]['securities_firm']
            response_text = f"현재 퇴직연금에 가입되어 있으며, '{securities_firm}' 계좌를 이용 중입니다." if pension_type == "가입" else "현재 퇴직연금 미가입 상태입니다. 이랜드 퇴직연금은 매년 12월에 신규가입 가능합니다."
        else:
            response_text = "현재 퇴직연금 가입 대상자가 아닙니다. 1년 미만 근로자가 아니라면, 입력 정보를 다시 확인해주세요."

        return JSONResponse(content={
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": response_text}}]
            }
        })

    except Exception as e:
        print(f"🚨 서버 오류 발생: {str(e)}")
        return JSONResponse(content={
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": f"서버 오류가 발생했습니다: {str(e)}"}}]
            }
        }, status_code=500)
