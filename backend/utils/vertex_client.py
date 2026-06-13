"""
GCP Vertex AI client wrapper.
Set USE_MOCK_GCP=true in .env to use mock responses (no credentials needed).
All model names are read from environment variables — change them in .env without touching code.
"""
import os
import json
import random
from typing import Optional

USE_MOCK = os.getenv("USE_MOCK_GCP", "true").lower() == "true"

# ── Model config — all overridable via .env ───────────────────────────────────
FLASH_MODEL = os.getenv("GEMINI_FLASH_MODEL", "gemini-2.5-flash")
PRO_MODEL   = os.getenv("GEMINI_PRO_MODEL",   "gemini-2.5-pro")
STT_MODEL   = os.getenv("STT_MODEL",           "chirp_2")
STT_LANG    = os.getenv("STT_LANGUAGE",        "hi-IN")
TTS_VOICE   = os.getenv("TTS_VOICE",           "hi-IN-Neural2-A")
TTS_LANG    = os.getenv("TTS_LANGUAGE",        "hi-IN")


class VertexClient:
    def __init__(self):
        self.mock = USE_MOCK
        if not self.mock:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            project  = os.getenv("GOOGLE_CLOUD_PROJECT")
            location = os.getenv("GOOGLE_CLOUD_LOCATION", "us-central1")
            vertexai.init(project=project, location=location)
            self.flash_model = GenerativeModel(FLASH_MODEL)
            self.pro_model   = GenerativeModel(PRO_MODEL)
            print(f"[Vertex AI] Flash: {FLASH_MODEL} | Pro: {PRO_MODEL}")
            print(f"[Vertex AI] STT: {STT_MODEL} ({STT_LANG}) | TTS voice: {TTS_VOICE}")

    async def generate_text(self, prompt: str, use_pro: bool = False, json_mode: bool = False) -> str:
        if self.mock:
            return await self._mock_generate(prompt, json_mode)
        model = self.pro_model if use_pro else self.flash_model
        response = model.generate_content(prompt)
        return response.text

    async def _mock_generate(self, prompt: str, json_mode: bool) -> str:
        prompt_lower = prompt.lower()
        if json_mode or "json" in prompt_lower:
            if "order" in prompt_lower or "parse" in prompt_lower:
                return json.dumps({
                    "buyer": "Ramesh Traders",
                    "items": [
                        {"name": "Steel Rods", "qty": 50, "unit": "kg", "rate": 85.0, "hsn": "7214"},
                        {"name": "Iron Sheets", "qty": 20, "unit": "pcs", "rate": 450.0, "hsn": "7209"}
                    ],
                    "delivery_date": "2024-02-15",
                    "confidence": 0.92
                })
            # Check notice/compliance BEFORE generic gst to avoid false match
            if "notice" in prompt_lower or "demand" in prompt_lower or "penalty" in prompt_lower or "translate" in prompt_lower:
                return json.dumps({
                    "hindi_translation": "आपको GST रिटर्न दाखिल करने में देरी के कारण ₹57,600 की मांग की गई है। 30 दिनों के अंदर भुगतान करें।",
                    "notice_type": "DRC-01 — Tax Demand Notice",
                    "action_items": [
                        "30 दिनों में ₹57,600 का भुगतान करें",
                        "GSTIN पोर्टल पर लॉगिन करें और Challan जनरेट करें",
                        "CA से legal reply की सलाह लें"
                    ],
                    "deadline": "2024-03-01",
                    "severity": "high",
                    "penalty_amount": 4500,
                    "escalation_required": False
                })
            if "gstr" in prompt_lower or "validate" in prompt_lower or "return" in prompt_lower:
                return json.dumps({
                    "overall_status": "valid",
                    "issues": [],
                    "suggestions": ["Invoice sequence is correct", "HSN codes present on all items", "Arithmetic verified", "Ready for GSTR-1 filing"],
                    "filing_ready": True
                })
            return json.dumps({"status": "ok", "message": "Mock response"})

        if "hindi" in prompt_lower or "hinglish" in prompt_lower:
            responses = [
                "बिल्कुल सर! आपका ऑर्डर दर्ज हो गया है। Ramesh Traders को 50 kg Steel Rods के लिए invoice तैयार किया जा रहा है।",
                "जी हाँ! पिछले महीने में Suresh Enterprises ने सबसे ज़्यादा payment delay किया — 45 दिन। उनका बकाया ₹1,20,000 है।",
                "आपका cash flow अच्छा है। अगले 3 महीनों में ₹8.5 लाख की income expected है। MUDRA loan के लिए आप eligible हैं।"
            ]
            return random.choice(responses)

        if "forecast" in prompt_lower or "cash flow" in prompt_lower:
            return "Based on your last 6 months of transactions, projected revenue for the next 3 months is ₹8.5L, ₹9.2L, and ₹7.8L respectively. Current AR aging shows ₹2.1L overdue beyond 60 days."

        if "scheme" in prompt_lower or "mudra" in prompt_lower:
            return "Your business qualifies for: (1) MUDRA Kishore Loan up to ₹5L at 8.5% PA, (2) CGTMSE Credit Guarantee up to ₹25L, (3) PM Vishwakarma Scheme — ₹3L collateral-free credit."

        return "I understand your query. Based on your VyapaarOS data, here is a summary of the relevant information from your ledger and agent analysis."

    async def speech_to_text(self, audio_bytes: bytes, language: str = None) -> str:
        lang = language or STT_LANG
        if self.mock:
            mock_transcripts = [
                "Ramesh ko bol do 50 kilo steel rod chahiye hai kal tak",
                "Suresh ka invoice approved kar do",
                "Mera cash flow dikhao pichhle teen mahine ka",
                "GST notice explain karo simple Hindi mein"
            ]
            return random.choice(mock_transcripts)

        from google.cloud import speech
        client = speech.SpeechClient()
        audio  = speech.RecognitionAudio(content=audio_bytes)
        config = speech.RecognitionConfig(
            model=STT_MODEL,
            language_code=lang,
            alternative_language_codes=["en-IN"],
            enable_automatic_punctuation=True,
        )
        response = client.recognize(config=config, audio=audio)
        if response.results:
            return response.results[0].alternatives[0].transcript
        return ""

    async def text_to_speech(self, text: str, language: str = None) -> bytes:
        lang = language or TTS_LANG
        if self.mock:
            return b"\xff\xfb\x90\x00" * 100

        from google.cloud import texttospeech
        client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text)

        # Determine SSML gender from voice name suffix (A/C = FEMALE, B/D = MALE)
        voice_suffix = TTS_VOICE.split("-")[-1] if TTS_VOICE else "A"
        gender = (texttospeech.SsmlVoiceGender.MALE
                  if voice_suffix in ("B", "D")
                  else texttospeech.SsmlVoiceGender.FEMALE)

        voice = texttospeech.VoiceSelectionParams(
            language_code=lang,
            name=TTS_VOICE,
            ssml_gender=gender,
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,
            pitch=0.0,
        )
        response = client.synthesize_speech(
            input=synthesis_input, voice=voice, audio_config=audio_config
        )
        return response.audio_content


vertex_client = VertexClient()
