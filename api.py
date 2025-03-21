from fastapi import FastAPI, Request
from starlette.responses import JSONResponse
import re

app = FastAPI()

# ✅ 직원 정보 (SQLite 대신 직접 저장)
employees = {
    "홍길동10999999": {"가입유형": "가입", "퇴직연금사업장": "신한투자증권"},
    "김철수10888888": {"가입유형": "미가입"},
}

@app.get("/")
def hello():
    """서버 정상 작동 확인"""
    return {"message": "Vercel 퇴직연금 조회 API 실행 중!"}

@app.post("/check-pension")
async def check_pension(request: Request):
    try:
        data = await request.json()
        print("\n🔹 [STEP 1] Received JSON 데이터:\n", data)

        # ✅ JSON 데이터가 유효한지 확인
        if not data:
            print("❌ 오류: JSON 데이터 없음")
            return JSONResponse(content={
                "version": "2.0",
                "template": {"outputs": [{"simpleText": {"text": "Invalid request: No JSON received"}}]}
            }, status_code=400)

        # ✅ 사용자 입력값 가져오기 (카카오 챗봇에서 전달한 "이름+사번")
        action_params = data.get('action', {}).get('params', {})
        user_input = str(action_params.get('user_input', '')).strip()

        # ✅ 만약 user_input이 비어 있다면, utterance 값에서 가져오기
        if not user_input:
            user_input = data.get('utterance', '').strip()

        print(f"🔹 [STEP 2] 입력값(이름+사번): {user_input}")

        # ✅ 정규식으로 이름과 사번 분리
        pattern = r"^([가-힣]+)(\d+)$"
        match = re.match(pattern, user_input)

        if not match:
            print("❌ [STEP 3] 이름+사번 형식 오류")
            return JSONResponse(content={
                "version": "2.0",
                "template": {
                    "outputs": [{"simpleText": {"text": "입력 형식이 올바르지 않습니다. 띄어쓰기 없이 입력해주세요. 예) 홍길동10999999"}}]
                }
            }, status_code=400)

        user_name = match.group(1)  # 이름
        user_id = match.group(2)    # 사번
        print(f"🔹 [STEP 3] 이름: {user_name}, 사번: {user_id}")

        # ✅ 가입 여부 확인 (직접 저장된 데이터에서 조회)
        if user_input in employees:
            emp_data = employees[user_input]
            if emp_data["가입유형"] == "가입":
                response_text = f"현재 퇴직연금에 가입되어 있으며, '{emp_data['퇴직연금사업장']}' 계좌를 이용 중입니다."
            else:
                response_text = "현재 퇴직연금 미가입 상태입니다. 이랜드 퇴직연금은 매년 12월에 신규가입 가능합니다."
        else:
            response_text = "현재 퇴직연금 가입 대상자가 아닙니다. 1년 미만 근로자가 아니라면, 입력 정보를 다시 확인해주세요."

        print("🔹 [STEP 6] 최종 응답:", response_text)

        # ✅ 최종 응답 (카카오 챗봇 JSON 형식)
        return JSONResponse(content={
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": response_text}}]}
        })

    except Exception as e:
        print("🚨 [ERROR] 서버 오류 발생:", str(e))
        return JSONResponse(content={
            "version": "2.0",
            "template": {"outputs": [{"simpleText": {"text": f"서버 오류가 발생했습니다: {str(e)}"}}]}
        }, status_code=500)
