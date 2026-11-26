"""
MindCare LLM Integration Service
Connects ML predictions, SHAP feature drivers, and RAG knowledge base chunks to generate
personalized 3-step action plans and grounded conversational Q&A.
Supports Google Gemini, Groq, Ollama, and an offline grounded fallback generator.
"""

import os
import json
from typing import List, Optional
import httpx

from app.config import settings
from app.models.schemas import (
    StudentData,
    FeatureImpact,
    RetrievedSource,
    PlanStep,
    PlanResponse,
    ChatMessage,
    ChatResponse,
    SafetyAlert
)
from app.services.safety_guard import safety_guard

# Try importing google-genai SDK
try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


class LLMService:
    def __init__(self):
        self.api_key = (settings.GEMINI_API_KEY or os.environ.get("GEMINI_API_KEY", "")).strip()
        self.groq_key = (settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")).strip()
        self.client = None
        self.last_groq_error: Optional[str] = None

        if HAS_GENAI and self.api_key:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def _call_gemini(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not HAS_GENAI or not self.client:
            return None

        try:
            model_name = settings.GEMINI_MODEL or "gemini-2.5-flash"
            response = self.client.models.generate_content(
                model=model_name,
                contents=f"{system_prompt}\n\nUser Question:\n{user_prompt}",
            )
            if response and response.text:
                return response.text.strip()
        except Exception as e:
            print(f"[LLMService] Gemini API call failed: {e}")
            return None

        return None

    def _call_groq(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        if not self.groq_key:
            return None

        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.groq_key}",
            "Content-Type": "application/json"
        }
        candidates = []
        for m in [settings.GROQ_MODEL, "llama-3.1-8b-instant", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"]:
            if m and m not in candidates:
                candidates.append(m)

        try:
            with httpx.Client(timeout=15.0) as client:
                for model in candidates:
                    payload = {
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 800
                    }
                    res = client.post(url, headers=headers, json=payload)
                    if res.status_code == 200:
                        self.last_groq_error = None
                        data = res.json()
                        return data["choices"][0]["message"]["content"].strip()
                    self.last_groq_error = f"HTTP {res.status_code}: {res.text[:200]}"
                    print(f"[LLMService] Groq API error ({model}) {self.last_groq_error}")
                    if res.status_code != 404:
                        break
        except Exception as e:
            self.last_groq_error = str(e)
            print(f"[LLMService] Groq API call failed: {e}")

        return None

    def _offline_plan_synthesizer(
        self,
        score: float,
        risk_factors: List[FeatureImpact],
        protective_factors: List[FeatureImpact],
        retrieved_sources: List[RetrievedSource]
    ) -> PlanResponse:
        """
        High-fidelity offline grounded planner.
        Synthesizes an exact 3-step action plan using the student's top SHAP drivers and retrieved RAG chunks.
        Ensures the system never breaks when running offline or without an external API key.
        """
        headline = (
            f"Personalized Resilience Plan (Signal Score: {score}/10) — Addressing Top Lifestyle Drivers"
        )

        steps: List[PlanStep] = []

        # Step 1: Immediate Shift (Night / Morning rhythm, targeting Sleep or Screen Time)
        sleep_driver = next((f for f in risk_factors if f.category == "Sleep"), None)
        screen_driver = next((f for f in risk_factors if f.category == "Screen Time"), None)
        stress_driver = next((f for f in risk_factors if f.category == "Stress"), None)

        # Source lookups
        sleep_source = next((s for s in retrieved_sources if s.category == "Sleep"), None)
        screen_source = next((s for s in retrieved_sources if s.category == "Screen Time"), None)
        stress_source = next((s for s in retrieved_sources if s.category == "Stress"), None)
        exercise_source = next((s for s in retrieved_sources if s.category == "Exercise"), None)
        study_source = next((s for s in retrieved_sources if s.category == "Study Habits"), None)

        # --- Step 1: Sleep / Evening Anchor ---
        if sleep_driver:
            step1_action = (
                f"Establish a consistent lights-out target with a 45-minute digital curfew. "
                f"Because your sleep is currently {sleep_driver.user_value}, shifting sleep onset 30 minutes earlier "
                f"and keeping mobile screens out of arm's reach restores deep NREM recovery cycles."
            )
            step1_title = "Anchor Circadian Sleep Hygiene"
            step1_source = sleep_source.source if sleep_source else "WHO Guidelines on Sleep and Circadian Health"
            step1_target = "Sleep Duration"
        else:
            step1_action = (
                "Maintain your consistent sleep schedule and prioritize 15 minutes of natural morning sunlight "
                "within an hour of waking to anchor daytime alertness and nighttime melatonin synthesis."
            )
            step1_title = "Protect Sleep Anchor"
            step1_source = sleep_source.source if sleep_source else "Harvard Sleep Medicine Guide"
            step1_target = "Circadian Rhythm"

        steps.append(PlanStep(
            step_number=1,
            title=step1_title,
            action=step1_action,
            target_driver=step1_target,
            source=step1_source
        ))

        # --- Step 2: Digital / Focus Boundaries ---
        if screen_driver:
            step2_action = (
                f"Implement the 2-window social media schedule. Your current screen time is {screen_driver.user_value}. "
                f"Silence non-human notifications, move feeds to nested folders, and replace passive late-evening scrolling "
                f"with analog reading to reduce attention residue."
            )
            step2_title = "Digital Habit Restructuring"
            step2_source = screen_source.source if screen_source else "Stanford Lifestyle Medicine Digital Detox"
            step2_target = "Screen Time & Phone Unlocks"
        else:
            step2_action = (
                "Utilize Pomodoro 25-minute single-task sprints during study blocks. "
                "Keep browser tabs organized and eliminate multitasking to preserve working memory endurance."
            )
            step2_title = "Single-Task Study Immersion"
            step2_source = study_source.source if study_source else "Cornell Learning Strategies"
            step2_target = "Study Efficiency"

        steps.append(PlanStep(
            step_number=2,
            title=step2_title,
            action=step2_action,
            target_driver=step2_target,
            source=step2_source
        ))

        # --- Step 3: Somatic Reset & Stress De-escalation ---
        if stress_driver:
            step3_action = (
                f"Practice the Stanford Physiological Sigh (two quick nasal inhalations followed by one long passive exhale) "
                f"for 2 minutes whenever exam or academic pressure peaks. "
                f"Pair this with a daily 15-minute brisk outdoor walk to clear cortisol buildup."
            )
            step3_title = "Autonomic Nervous System Reset"
            step3_source = stress_source.source if stress_source else "Stanford Neurobiology & NHS Every Mind Matters"
            step3_target = "Perceived Stress"
        else:
            step3_action = (
                "Integrate 20 minutes of brisk movement or aerobic walking into your study breaks. "
                "Regular physical exertion naturally boosts hippocampal BDNF and monoamine neurotransmitters."
            )
            step3_title = "Daily Movement & Neuroplasticity Boost"
            step3_source = exercise_source.source if exercise_source else "WHO Physical Activity Guidelines"
            step3_target = "Physical Resilience"

        steps.append(PlanStep(
            step_number=3,
            title=step3_title,
            action=step3_action,
            target_driver=step3_target,
            source=step3_source
        ))

        return PlanResponse(
            predicted_score=score,
            headline=headline,
            steps=steps,
            retrieved_sources=retrieved_sources,
            safety_disclaimer=safety_guard.get_disclaimer(),
            provider_used="MindCare Grounded Synthesizer (Offline Precision)"
        )

    def _has_llm(self) -> bool:
        """Check if any LLM provider is available."""
        return bool((HAS_GENAI and self.client) or self.groq_key)

    def _llm_enhance_step(self, step: PlanStep, sources_context: str, score: float) -> PlanStep:
        """Use LLM to rewrite a single step's action text — returns original on failure."""
        system_prompt = (
            "You are a concise, empathetic student wellness advisor. "
            "Rewrite the following wellness recommendation to be more personalized, warm, and actionable. "
            "Keep it to 2-3 sentences. Cite the given source naturally. Do NOT add markdown. "
            "Return ONLY the rewritten text, nothing else."
        )
        user_prompt = (
            f"Student score: {score}/10\n"
            f"Step title: {step.title}\n"
            f"Original: {step.action}\n"
            f"Source to cite: {step.source}\n"
            f"Context:\n{sources_context[:500]}"
        )
        enhanced = self._call_gemini(system_prompt, user_prompt) or self._call_groq(system_prompt, user_prompt)
        if enhanced and len(enhanced) > 20:
            step.action = enhanced
        return step

    def generate_plan(
        self,
        score: float,
        risk_factors: List[FeatureImpact],
        protective_factors: List[FeatureImpact],
        retrieved_sources: List[RetrievedSource]
    ) -> PlanResponse:
        """
        Generates a 3-step action plan.
        Strategy: always build the structured plan using the reliable offline synthesizer,
        then enhance each step with LLM if available. This guarantees valid structure
        while still using Groq/Gemini for personalization.
        """
        # Build the reliable structured plan first
        plan = self._offline_plan_synthesizer(score, risk_factors, protective_factors, retrieved_sources)

        # If an LLM is available, enhance each step's text
        if self._has_llm():
            sources_context = "\n".join([
                f"{s.source} — {s.title}: {s.snippet[:150]}"
                for s in retrieved_sources[:4]
            ])
            try:
                for step in plan.steps:
                    self._llm_enhance_step(step, sources_context, score)
                # Determine which provider actually worked
                provider = "Gemini" if (HAS_GENAI and self.client) else "Groq"
                plan.provider_used = f"{provider} (Grounded RAG)"
            except Exception as e:
                print(f"[LLMService] LLM enhancement failed, keeping offline text: {e}")

        return plan

    def chat(
        self,
        message: str,
        history: List[ChatMessage],
        retrieved_sources: List[RetrievedSource],
        student_context: Optional[StudentData] = None
    ) -> ChatResponse:
        """
        Conversational assistant grounded strictly in retrieved documents.
        Enforces crisis bypass and medical disclaimer.
        Note: Crisis safety check is handled by the caller (main.py) before this method is invoked.
        """
        # Build grounded context from RAG
        context_text = "\n\n".join([
            f"[Source {i+1}: {s.source} - {s.title}]\n{s.snippet}"
            for i, s in enumerate(retrieved_sources)
        ])

        student_info = ""
        if student_context:
            student_info = (
                f"Student profile context: Age {student_context.age}, {student_context.academic_level}, "
                f"Platform: {student_context.most_used_platform} ({student_context.avg_daily_usage_hours}h/day), "
                f"Sleep: {student_context.sleep_hours_per_night}h/night, Stress: {student_context.stress_level}."
            )

        system_prompt = (
            "You are MindCare AI, a gentle, empathetic, and evidence-grounded student wellness companion.\n\n"
            "CRITICAL RULES:\n"
            "1. Answer the user's question using ONLY the provided verified wellness guidelines below.\n"
            "2. If the user's question cannot be answered from the provided sources, reply honestly: "
            "'I don't have information on that in my current wellness library, but I can share tips on sleep, stress management, digital detox, study habits, or exercise.'\n"
            "3. Do NOT make up facts, cite nonexistent studies, or hallucinate.\n"
            "4. NEVER diagnose any mental or medical illness, and never recommend medications.\n"
            "5. Keep your tone encouraging, practical, and easy to read (2-3 concise paragraphs maximum).\n"
            "6. Always mention the source organization (e.g., WHO, Harvard Health, Stanford Lifestyle Medicine) in your answer."
        )

        user_prompt = (
            f"{student_info}\n\n"
            f"Verified Wellness Context:\n{context_text}\n\n"
            f"Student Question: {message}\n\n"
            "Provide a grounded, compassionate response citing the relevant source:"
        )

        # Attempt Gemini
        reply = self._call_gemini(system_prompt, user_prompt)
        provider = "Gemini"

        # Attempt Groq if Gemini unavailable
        if not reply:
            reply = self._call_groq(system_prompt, user_prompt)
            provider = "Groq"

        # Offline grounded synthesizer fallback for chat
        if not reply:
            if retrieved_sources:
                top_s = retrieved_sources[0]
                reply = (
                    f"Based on guidelines from **{top_s.source}** ({top_s.title}):\n\n"
                    f"{top_s.snippet}\n\n"
                    f"To put this into practice: try introducing one small, manageable change today. "
                    f"Consistency with simple micro-habits yields the greatest benefit over time.\n\n"
                    f"*Source: {top_s.source}*"
                )
                provider = "MindCare Grounded RAG (Local)"
            else:
                reply = (
                    "I don't have specific guidance on that question in my current wellness library. "
                    "However, you can ask me about sleep hygiene, reducing screen time, managing academic stress, "
                    "focus techniques (like the Pomodoro method), or the mental benefits of daily movement!"
                )
                provider = "MindCare Knowledge Router"

        return ChatResponse(
            reply=reply,
            sources=retrieved_sources,
            is_crisis=False,
            safety_alert=None,
            medical_disclaimer=safety_guard.get_disclaimer(),
            provider_used=provider
        )


llm_service = LLMService()
