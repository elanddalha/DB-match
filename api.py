import os
import json
import pandas as pd
import requests
from io import StringIO
from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import asyncio  # ✅ 추가: 딜레이용

# ✅ GitHub에 올린 CSV 파일 RAW URL
CSV_URL = "https://raw.githubusercontent.com/elanddalha/DB-match/main/pension_data.csv"

# ✅ GitHub에서 CSV 불러오기
def load_csv():
    response = requests.get(CSV_URL)
    df = pd.read_csv(StringIO(response.text), dtype=str)
    return df

df = load_csv()

# ✅ FastAPI 앱 생성
app = FastAPI()

@app.get("/")
def home():
    """서버 정상 작동 확인"""
    return {"message": "퇴직연금 가입 여부 조회 API 실행 중!"}

@app.post("/webhook")
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

        user_name = match.group(1)
        user_id = match.group(2)

        # ✅ 딜레이 + 기본 응답 설정
        await asyncio.sleep(1.5)
        response_text = "조회 중입니다. 3초 안에 답변이 없을 경우 다시 한번 입력해주세요."

        # ✅ 실제 데이터 조회
        result = df[(df['name'] == user_name) & (df['id'] == user_id)]

        if not result.empty:
            pension_type = result.iloc[0]['pension_type']
            securities_firm = result.iloc[0]['securities_firm']
            response_text = (
                f"현재 퇴직연금에 가입되어 있으며, '{securities_firm}' 계좌를 이용 중입니다."
                if pension_type == "가입"
                else "현재 퇴직연금 미가입 상태입니다. 이랜드 퇴직연금은 매년 12월에 신규가입 가능합니다."
            )
        else:
            response_text = "현재 퇴직연금 가입 대상자가 아닙니다. 1년 미만 근로자가 아니라면, 입력 정보를 다시 확인해주세요."

        return JSONResponse(content={
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": response_text}}]
            }
        })

    except Exception as e:
        return JSONResponse(content={
            "version": "2.0",
            "template": {
                "outputs": [{"simpleText": {"text": f"서버 오류가 발생했습니다: {str(e)}"}}]
            }
        }, status_code=500)
