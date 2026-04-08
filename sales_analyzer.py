import os
import re
import tempfile
from pathlib import Path

import streamlit as st

# ─────────────────────────────────────────────────
# 페이지 설정
# ─────────────────────────────────────────────────
st.set_page_config(
    page_title="영업 상담 분석기",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────
# 커스텀 CSS
# ─────────────────────────────────────────────────
st.markdown("""
<style>
  .app-header {
    background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 50%, #a78bfa 100%);
    color: white;
    padding: 2.5rem 2rem 2.2rem;
    border-radius: 16px;
    margin-bottom: 1.5rem;
    text-align: center;
    box-shadow: 0 10px 40px rgba(99,102,241,0.25);
  }
  .app-header h1 { margin: 0; font-size: 2.2rem; letter-spacing: -0.5px; }
  .app-header p  { margin: 0.5rem 0 0; opacity: 0.88; font-size: 1.05rem; }

  .steps-row {
    display: flex; align-items: center; justify-content: center;
    gap: 0.4rem; margin: 1.4rem 0 0.8rem;
  }
  .step-pill {
    padding: 0.4rem 1.3rem; border-radius: 20px;
    font-weight: 700; font-size: 0.88rem; display: inline-block;
  }
  .step-active  { background: #6366f1; color: white; box-shadow: 0 2px 12px rgba(99,102,241,0.4); }
  .step-done    { background: #10b981; color: white; }
  .step-waiting { background: #f1f5f9; color: #94a3b8; }
  .step-arrow   { color: #cbd5e1; font-size: 1.2rem; font-weight: 700; }

  .result-card {
    background: white; border: 1px solid #e2e8f0;
    border-radius: 12px; padding: 1.5rem 1.8rem;
    margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }

  .stTabs [data-baseweb="tab"] {
    font-size: 0.98rem; font-weight: 600; gap: 0.3rem;
  }
  .stTabs [data-baseweb="tab-list"] { gap: 0.5rem; }

  div[data-testid="stMetricValue"] { font-size: 1.6rem; color: #6366f1; }

  .stream-box {
    background: #f8fafc; border: 1px solid #e2e8f0;
    border-radius: 10px; padding: 1.2rem 1.5rem;
    font-size: 0.93rem; line-height: 1.75;
    min-height: 120px;
  }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# 헬퍼 함수
# ─────────────────────────────────────────────────

def transcribe_audio(file_bytes: bytes, filename: str, openai_api_key: str) -> str:
    """OpenAI Whisper API로 음성 → 텍스트 변환"""
    from openai import OpenAI

    max_bytes = 25 * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise ValueError(
            f"파일 크기({len(file_bytes)/1024/1024:.1f}MB)가 25MB 제한을 초과합니다."
        )

    client = OpenAI(api_key=openai_api_key)
    suffix = Path(filename).suffix or ".mp3"

    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file_bytes)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "rb") as f:
            result = client.audio.transcriptions.create(
                model="whisper-1",
                file=f,
                language="ko",
                response_format="text",
            )
        return str(result)
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def stream_analysis(transcript: str, consultation_type: str, api_key: str):
    """Claude Opus 4.6로 상담 내용 스트리밍 분석 (generator)"""
    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    system_prompt = f"""당신은 {consultation_type} 분야의 최고 영업 전략 전문가이자 고객 심리 분석가입니다.
영업사원이 고객과 나눈 상담 내용을 분석하여 실무에 즉시 적용 가능한 인사이트를 제공합니다.

분석 원칙:
- 고객의 말 속에 숨겨진 진짜 니즈와 우려사항을 파악합니다
- 심리학적 패턴(DISC 모델)을 활용하여 성향을 분석합니다
- 구체적이고 실행 가능한 영업 전략을 제시합니다
- 한국 비즈니스 문화를 반영한 현실적 조언을 제공합니다
- 분석은 텍스트에서 관찰된 객관적 근거를 바탕으로 합니다"""

    user_prompt = f"""다음은 {consultation_type} 상담 녹취록입니다:

---
{transcript}
---

아래 세 개의 섹션으로 상세히 분석해주세요.
각 섹션은 반드시 지정된 마크다운 헤더로 시작해야 합니다.

## 📝 상담 내용 요약

### 핵심 논의 사항
(상담에서 다룬 주요 주제, 제품/서비스, 가격 조건 등)

### 고객의 주요 관심사와 질문
(고객이 특별히 집중한 부분과 구체적 질문들)

### 고객의 우려사항 및 반론
(고객이 표현한 걱정, 부정적 반응, 장벽)

### 상담 결과 및 합의 사항
(합의된 사항, 약속된 팔로업, 남은 과제)

---

## 👤 고객 성향 분석

### 커뮤니케이션 스타일
(직접적 vs 우회적, 감성적 vs 논리적, 말이 많은 vs 경청형)

### DISC 성향 분석
다음 4가지를 각각 평가하고, 주요 성향 유형을 판단해주세요:
- **D형(주도형)**: 직접적·결과지향·도전적 특성 관련 행동 관찰 내용
- **I형(사교형)**: 열정적·낙관적·사람 중심적 특성 관련 행동 관찰 내용
- **S형(안정형)**: 안정 추구·협조적·변화를 싫어하는 특성 관련 행동 관찰 내용
- **C형(신중형)**: 분석적·정확성 추구·규칙 준수 특성 관련 행동 관찰 내용
- **종합 판단**: 이 고객의 주요 성향 유형과 근거

### 의사결정 패턴
(충동적 vs 신중한, 독자적 vs 타인 의존적, 가격 민감도)

### 리스크 허용도
(보수적/안정 추구형 vs 도전적/수익 추구형)

### 핵심 구매 동기
(이 고객이 계약을 결심하게 할 핵심 이유)

### 계약 방해 요인
(계약을 막을 가능성이 높은 내적·외적 요인)

### 맞춤 설득 키워드
(이 고객에게 특히 효과적인 표현과 단어)

---

## 💡 계약 성사 전략

### 즉시 실행 액션 (24시간 내)
(지금 바로 영업사원이 해야 할 구체적 행동 목록)

### 팔로업 전략
- **연락 타이밍**: 언제 연락하면 가장 효과적인가
- **연락 채널**: 전화·카카오톡·이메일·방문 중 최적 방법
- **메시지 톤**: 어떤 말투와 내용으로 소통해야 하는가

### 예상 반론 & 대응 스크립트
주요 반론 3가지와 각각의 구체적 대응 스크립트를 제시해주세요

### 맞춤형 가치 제안
(이 고객의 성향에 맞게 강조해야 할 핵심 포인트)

### 클로징 전략
(계약으로 이끄는 최적의 클로징 방법과 타이밍)

### 장기 관계 구축 방안
(장기 고객·소개 고객으로 발전시키는 전략)"""

    with client.messages.stream(
        model="claude-opus-4-6",
        max_tokens=8000,
        thinking={"type": "adaptive"},
        system=system_prompt,
        messages=[{"role": "user", "content": user_prompt}],
    ) as stream:
        for chunk in stream.text_stream:
            yield chunk


def parse_sections(full_text: str) -> dict:
    """분석 결과를 3개 섹션으로 파싱"""
    summary_m = re.search(
        r"(## 📝 상담 내용 요약.*?)(?=## 👤|## 💡|$)", full_text, re.DOTALL
    )
    person_m = re.search(
        r"(## 👤 고객 성향 분석.*?)(?=## 💡|$)", full_text, re.DOTALL
    )
    strat_m = re.search(
        r"(## 💡 계약 성사 전략.*?)$", full_text, re.DOTALL
    )

    return {
        "summary":     summary_m.group(1).strip() if summary_m else "",
        "personality": person_m.group(1).strip()  if person_m else "",
        "strategy":    strat_m.group(1).strip()   if strat_m  else "",
    }


# ─────────────────────────────────────────────────
# 세션 상태 초기화
# ─────────────────────────────────────────────────
_defaults = {"step": 1, "transcript": "", "analysis": ""}
for _k, _v in _defaults.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ─────────────────────────────────────────────────
# 사이드바
# ─────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ 설정")
    st.divider()

    anthropic_key = st.text_input(
        "🔑 Anthropic API Key",
        type="password",
        placeholder="sk-ant-...",
        help="Claude AI 분석에 사용됩니다. console.anthropic.com에서 발급받으세요.",
    )

    openai_key = st.text_input(
        "🔑 OpenAI API Key (음성 변환용)",
        type="password",
        placeholder="sk-...",
        help="음성 파일 → 텍스트 변환(Whisper)에 필요합니다.\n"
             "텍스트를 직접 입력하는 경우 입력하지 않아도 됩니다.",
    )

    st.divider()
    st.markdown("### 📋 상담 유형")
    consultation_type = st.selectbox(
        "유형",
        [
            "창업/프랜차이즈 상담",
            "부동산 투자 상담",
            "금융/보험 상담",
            "IT 솔루션/소프트웨어 영업",
            "B2B 기업 영업",
            "기타 영업 상담",
        ],
        label_visibility="collapsed",
    )

    st.divider()
    with st.expander("📌 사용 방법"):
        st.markdown("""
**STEP 1 — 파일 업로드**
- 녹음 파일(MP3/WAV/M4A 등) 업로드
- 또는 상담 텍스트 직접 붙여넣기

**STEP 2 — 텍스트 확인**
- 변환된 텍스트 검토 및 수정

**STEP 3 — AI 분석 결과**
- 상담 내용 요약
- 고객 성향 분석 (DISC)
- 계약 성사 전략
""")

    st.divider()
    st.caption("🤖 Powered by Claude Opus 4.6 & Whisper")


# ─────────────────────────────────────────────────
# 헤더
# ─────────────────────────────────────────────────
st.markdown("""
<div class="app-header">
  <h1>🎙️ 영업 상담 분석기</h1>
  <p>창업 상담 녹음을 AI로 분석하여 고객 인사이트와 맞춤 영업 전략을 도출합니다</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────
# 단계 표시기
# ─────────────────────────────────────────────────
step = st.session_state.step


def _cls(i: int) -> str:
    if step > i:  return "step-done"
    if step == i: return "step-active"
    return "step-waiting"


labels = ["1️⃣ 입력", "2️⃣ 텍스트 확인", "3️⃣ AI 분석"]
st.markdown(
    f"""
    <div class="steps-row">
      <span class="step-pill {_cls(1)}">{labels[0]}</span>
      <span class="step-arrow">→</span>
      <span class="step-pill {_cls(2)}">{labels[1]}</span>
      <span class="step-arrow">→</span>
      <span class="step-pill {_cls(3)}">{labels[2]}</span>
    </div>
    """,
    unsafe_allow_html=True,
)
st.divider()


# ─────────────────────────────────────────────────
# STEP 1: 입력
# ─────────────────────────────────────────────────
if step == 1:
    st.markdown("### 📁 상담 내용 입력")
    tab_file, tab_text = st.tabs(["🎙️ 녹음 파일 업로드", "📝 텍스트 직접 입력"])

    # ── 파일 업로드 탭 ──────────────────────────────
    with tab_file:
        col_l, col_r = st.columns([1, 2], gap="large")

        with col_l:
            st.markdown("""
**지원 형식**
`MP3` `MP4` `WAV` `M4A` `OGG` `WEBM` `FLAC`

**제한 사항**
- 최대 파일 크기: **25 MB**
- 언어: 한국어 자동 인식

**필요한 API Key**
- OpenAI API Key (Whisper)
""")

        with col_r:
            uploaded = st.file_uploader(
                "파일을 여기로 드래그하거나 클릭하여 업로드",
                type=["mp3", "mp4", "wav", "m4a", "ogg", "webm", "flac"],
                label_visibility="collapsed",
            )

            if uploaded:
                size_mb = len(uploaded.getvalue()) / 1024 / 1024
                if size_mb > 25:
                    st.error(
                        f"파일 크기({size_mb:.1f}MB)가 25MB를 초과합니다. "
                        "파일을 분할하거나 텍스트 탭을 이용해주세요."
                    )
                else:
                    st.success(f"✅ **{uploaded.name}** ({size_mb:.1f} MB)")

                    if not openai_key:
                        st.warning("사이드바에 **OpenAI API Key**를 입력해주세요.")
                    else:
                        if st.button(
                            "🔄 텍스트로 변환하기",
                            type="primary",
                            use_container_width=True,
                        ):
                            with st.spinner(
                                f"🎧 음성 변환 중... ({size_mb:.1f}MB, 수 분 소요될 수 있습니다)"
                            ):
                                try:
                                    text = transcribe_audio(
                                        uploaded.getvalue(),
                                        uploaded.name,
                                        openai_key,
                                    )
                                    st.session_state.transcript = text
                                    st.session_state.step = 2
                                    st.rerun()
                                except Exception as exc:
                                    st.error(f"변환 실패: {exc}")

    # ── 텍스트 직접 입력 탭 ──────────────────────────
    with tab_text:
        st.caption("상담 녹취록을 직접 붙여넣거나 입력해주세요.")
        text_in = st.text_area(
            "상담 텍스트",
            height=320,
            placeholder=(
                "영업사원: 안녕하세요! 오늘 상담에 오신 것을 환영합니다.\n"
                "고객: 네 안녕하세요. 요즘 퇴직을 준비하면서 창업을 알아보고 있는데요...\n"
                "영업사원: 어떤 업종에 관심이 있으신가요?\n"
                "고객: 카페 창업을 생각하고 있어요. 투자 비용이 얼마나 될까요?"
            ),
            label_visibility="collapsed",
        )

        if text_in.strip():
            if st.button("다음 단계로 →", type="primary", use_container_width=True):
                st.session_state.transcript = text_in
                st.session_state.step = 2
                st.rerun()
        else:
            st.info("텍스트를 입력하면 분석을 시작할 수 있습니다.")


# ─────────────────────────────────────────────────
# STEP 2: 텍스트 확인
# ─────────────────────────────────────────────────
elif step == 2:
    st.markdown("### 📝 텍스트 검토 및 수정")
    st.caption(
        "변환된 텍스트를 확인하고 오타나 누락된 부분을 수정해주세요. "
        "수정 후 AI 분석을 시작합니다."
    )

    edited = st.text_area(
        "상담 텍스트",
        value=st.session_state.transcript,
        height=400,
        label_visibility="collapsed",
    )
    st.session_state.transcript = edited

    # 텍스트 통계
    if edited.strip():
        c1, c2, c3 = st.columns(3)
        c1.metric("단어 수",  f"{len(edited.split()):,}")
        c2.metric("글자 수",  f"{len(edited):,}")
        c3.metric("줄 수",   f"{edited.count(chr(10)) + 1:,}")

    st.divider()

    col_back, col_next = st.columns([1, 3])
    with col_back:
        if st.button("← 다시 입력", use_container_width=True):
            st.session_state.step = 1
            st.session_state.transcript = ""
            st.session_state.analysis = ""
            st.rerun()
    with col_next:
        if not anthropic_key:
            st.warning("⚠️ 사이드바에 **Anthropic API Key**를 입력해야 분석할 수 있습니다.")
        else:
            btn_disabled = not edited.strip()
            if st.button(
                "🔍 AI 분석 시작",
                type="primary",
                use_container_width=True,
                disabled=btn_disabled,
            ):
                st.session_state.analysis = ""
                st.session_state.step = 3
                st.rerun()


# ─────────────────────────────────────────────────
# STEP 3: AI 분석
# ─────────────────────────────────────────────────
elif step == 3:
    analysis = st.session_state.analysis

    # ── 아직 분석 전 → 스트리밍 실행 ──────────────────
    if not analysis:
        if not anthropic_key:
            st.error("Anthropic API Key가 없습니다. 사이드바에서 입력해주세요.")
            if st.button("← 돌아가기"):
                st.session_state.step = 2
                st.rerun()
        else:
            st.info("🤖 **Claude Opus 4.6**이 상담 내용을 분석하고 있습니다. 잠시만 기다려주세요...")

            # 실시간 스트리밍 표시
            with st.container(border=True):
                stream_holder = st.empty()

            full_text = ""
            try:
                for chunk in stream_analysis(
                    st.session_state.transcript,
                    consultation_type,
                    anthropic_key,
                ):
                    full_text += chunk
                    stream_holder.markdown(full_text + "\n\n▌")

                # 커서 제거 후 저장
                stream_holder.markdown(full_text)
                st.session_state.analysis = full_text
                st.rerun()

            except Exception as exc:
                err = str(exc)
                if "authentication" in err.lower() or "api_key" in err.lower():
                    st.error("❌ API Key가 유효하지 않습니다. 올바른 Anthropic API Key를 입력해주세요.")
                elif "rate_limit" in err.lower():
                    st.error("⏳ API 요청 한도를 초과했습니다. 잠시 후 다시 시도해주세요.")
                else:
                    st.error(f"분석 중 오류 발생: {err}")

                if st.button("← 텍스트 수정으로 돌아가기"):
                    st.session_state.step = 2
                    st.rerun()

    # ── 분석 완료 → 결과 표시 ────────────────────────
    else:
        st.success("✅ 분석이 완료되었습니다!")
        st.markdown("<br>", unsafe_allow_html=True)

        sections = parse_sections(analysis)

        tab_sum, tab_per, tab_str = st.tabs(
            ["📝 상담 내용 요약", "👤 고객 성향 분석", "💡 계약 성사 전략"]
        )

        with tab_sum:
            if sections["summary"]:
                st.markdown(sections["summary"])
            else:
                st.markdown(analysis.split("## 👤")[0] if "## 👤" in analysis else analysis)

        with tab_per:
            if sections["personality"]:
                st.markdown(sections["personality"])
            else:
                st.info("성향 분석 섹션이 분리되지 않았습니다. '전체 결과' 탭을 확인해주세요.")

        with tab_str:
            if sections["strategy"]:
                st.markdown(sections["strategy"])
            else:
                st.info("계약 전략 섹션이 분리되지 않았습니다. '전체 결과' 탭을 확인해주세요.")

        st.divider()

        # 액션 버튼 행
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("← 텍스트 수정", use_container_width=True):
                st.session_state.step = 2
                st.session_state.analysis = ""
                st.rerun()
        with c2:
            if st.button(
                "🔄 재분석 (다른 유형으로)",
                use_container_width=True,
            ):
                st.session_state.analysis = ""
                st.session_state.step = 3
                st.rerun()
        with c3:
            st.download_button(
                label="📥 결과 다운로드 (.txt)",
                data=analysis,
                file_name="상담_분석_결과.txt",
                mime="text/plain",
                use_container_width=True,
            )

        # 새 상담 시작
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button(
            "🆕 새 상담 분석 시작",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.transcript = ""
            st.session_state.analysis = ""
            st.session_state.step = 1
            st.rerun()

        # 원문 숨김 표시
        with st.expander("🔍 전체 분석 원문 보기"):
            st.markdown(analysis)
