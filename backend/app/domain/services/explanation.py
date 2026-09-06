from __future__ import annotations

import json
import logging
import os
from uuid import UUID

from app.domain.models.explanation import (
    ExplanationEvidence,
    ExplanationResponse,
    StructuredExplanation,
)

logger = logging.getLogger(__name__)


class GroundingError(ValueError):
    """Raised when generated explanation fails grounding validation."""


class ExplanationGenerator:
    @staticmethod
    def generate(evidence: ExplanationEvidence) -> ExplanationResponse:
        use_llm = os.getenv("ENABLE_LLM_EXPLANATION", "false").lower() == "true"

        if use_llm:
            try:
                structured = ExplanationGenerator._generate_gemini(evidence)
                ExplanationGenerator._validate_structured(evidence, structured)
                explanation_text = ExplanationGenerator._render_structured(structured)
                return ExplanationResponse(
                    explanation=explanation_text,
                    generated_by="gemini",
                    run_id=evidence.run_id,
                )
            except GroundingError as e:
                logger.warning(
                    "Gemini grounding validation failed: %s. Using deterministic fallback.", e
                )
                return ExplanationGenerator._generate_deterministic(evidence)
            except Exception as e:  # noqa: BLE001
                logger.warning(
                    "Gemini explanation failed: %s. Using deterministic fallback.", e
                )
                return ExplanationGenerator._generate_deterministic(evidence)
        else:
            return ExplanationGenerator._generate_deterministic(evidence)

    # ------------------------------------------------------------------
    # Grounding validation (applied to structured Gemini output)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_structured(
        evidence: ExplanationEvidence, structured: StructuredExplanation
    ) -> None:
        """Validate structured Gemini output against verified evidence."""
        infeasible_route_names = {r.route_name for r in evidence.routes if not r.is_feasible}

        # CASE A: Recommended route name must match optimizer decision.
        if evidence.has_feasible_routes and evidence.recommended_route_id:
            expected = next(
                (r.route_name for r in evidence.routes if r.is_recommended), None
            )
            if expected and structured.recommended_route_name != expected:
                raise GroundingError(
                    f"Gemini recommended '{structured.recommended_route_name}' "
                    f"but optimizer selected '{expected}'."
                )

        # CASE C: No feasible routes — must not name any route as recommended.
        if not evidence.has_feasible_routes and structured.recommended_route_name and structured.recommended_route_name.strip():
            raise GroundingError(
                "Gemini named a recommended route but no feasible route exists."
            )

        # CASE B: Infeasible route must not be referred to as feasible in reasons/tradeoffs.
        all_free_text = " ".join(structured.reasons + structured.tradeoffs + structured.constraint_notes)
        for infeasible_name in infeasible_route_names:
            if infeasible_name in all_free_text:
                # Check for feasibility-contradicting phrases
                contradictions = [
                    f"{infeasible_name} is feasible",
                    f"{infeasible_name} can be selected",
                    f"{infeasible_name} is recommended",
                ]
                for phrase in contradictions:
                    if phrase.lower() in all_free_text.lower():
                        raise GroundingError(
                            f"Gemini claimed infeasible route '{infeasible_name}' is feasible/recommended."
                        )

    # ------------------------------------------------------------------
    # Gemini LLM generation with structured output
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_gemini(evidence: ExplanationEvidence) -> StructuredExplanation:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not configured.")

        from google import genai  # noqa: PLC0415
        from google.genai import types  # noqa: PLC0415

        model_name = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

        # Build a safe, minimal evidence summary for the prompt
        evidence_summary = ExplanationGenerator._build_evidence_summary(evidence)

        prompt = (
            "You are an explanation generator for a logistics route optimization system.\n"
            "You are NOT an optimization engine. The deterministic optimizer has already decided.\n"
            "\nCRITICAL RULES:\n"
            "1. THE OPTIMIZATION ENGINE DECIDES. YOU ONLY EXPLAIN.\n"
            "2. Use ONLY the supplied evidence below. Do not invent facts.\n"
            "3. Do not change the recommended route.\n"
            "4. Do not introduce route names not present in the evidence.\n"
            "5. Do not invent cost, time, reliability, or risk numbers.\n"
            "6. Preserve feasibility distinctions exactly as given.\n"
            "7. If no feasible route exists, leave recommended_route_name empty.\n"
            "8. Use phrases like 'The optimization selected...' not 'I recommend...'.\n"
            "\nEVIDENCE:\n"
            f"{evidence_summary}\n"
            "\nReturn a JSON object with these exact fields:\n"
            '{"recommended_route_name": "<name or empty string>", "reasons": ["..."], "tradeoffs": ["..."], "constraint_notes": ["..."]}'
        )

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema={
                    "type": "object",
                    "properties": {
                        "recommended_route_name": {"type": "string"},
                        "reasons": {"type": "array", "items": {"type": "string"}},
                        "tradeoffs": {"type": "array", "items": {"type": "string"}},
                        "constraint_notes": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["recommended_route_name", "reasons", "tradeoffs", "constraint_notes"],
                },
            ),
        )

        raw_json = response.text
        data = json.loads(raw_json)
        return StructuredExplanation(
            recommended_route_name=data.get("recommended_route_name", ""),
            reasons=data.get("reasons", []),
            tradeoffs=data.get("tradeoffs", []),
            constraint_notes=data.get("constraint_notes", []),
        )

    @staticmethod
    def _build_evidence_summary(evidence: ExplanationEvidence) -> str:
        """Build a compact, safe evidence summary for the LLM prompt."""
        lines = []
        if evidence.has_feasible_routes and evidence.recommended_route_id:
            rec = next((r for r in evidence.routes if r.is_recommended), None)
            if rec:
                lines.append(f"Recommended route: {rec.route_name}")
                lines.append(f"Total weighted score: {rec.total_score:.4f}" if rec.total_score else "")
                top_drivers = rec.score_drivers[:3]
                for d in top_drivers:
                    lines.append(f"  Score contribution — {d.objective}: {d.contribution*100:.1f}%")
        else:
            lines.append("No feasible route: all candidates violated hard constraints.")

        lines.append("\nAll routes:")
        for r in evidence.routes:
            status = "FEASIBLE" if r.is_feasible else "INFEASIBLE"
            pareto = " [Pareto-efficient]" if r.is_pareto_efficient else ""
            rec_marker = " [RECOMMENDED]" if r.is_recommended else ""
            lines.append(f"  {r.route_name}: {status}{pareto}{rec_marker}")
            if not r.is_feasible and r.constraint_violations:
                for v in r.constraint_violations:
                    lines.append(f"    Violation: {v}")

        lines.append(f"\nObjective weights: cost={evidence.weights.get('cost', 0):.0%}, "
                     f"time={evidence.weights.get('time', 0):.0%}, "
                     f"reliability={evidence.weights.get('reliability', 0):.0%}, "
                     f"risk={evidence.weights.get('risk', 0):.0%}")
        return "\n".join(l for l in lines if l)

    @staticmethod
    def _render_structured(structured: StructuredExplanation) -> str:
        """Convert validated StructuredExplanation into readable prose."""
        parts = []
        if structured.recommended_route_name:
            parts.append(
                f"The optimization selected {structured.recommended_route_name}."
            )
        parts.extend(structured.reasons)
        parts.extend(structured.tradeoffs)
        parts.extend(structured.constraint_notes)
        return " ".join(parts) if parts else "No explanation available."

    # ------------------------------------------------------------------
    # Deterministic fallback
    # ------------------------------------------------------------------

    @staticmethod
    def _generate_deterministic(evidence: ExplanationEvidence) -> ExplanationResponse:
        if not evidence.has_feasible_routes or not evidence.recommended_route_id:
            return ExplanationResponse(
                explanation=(
                    "No feasible route exists for this shipment. "
                    "The optimization engine could not find any candidate "
                    "that satisfies all hard constraints."
                ),
                generated_by="deterministic",
                run_id=evidence.run_id,
            )

        recommended = next((r for r in evidence.routes if r.is_recommended), None)
        if not recommended:
            return ExplanationResponse(
                explanation="Error: Recommended route not found in evidence.",
                generated_by="deterministic",
                run_id=evidence.run_id,
            )

        top_drivers = recommended.score_drivers[:2]
        drivers_text = " and ".join(
            [f"{d.objective} ({d.contribution * 100:.1f}%)" for d in top_drivers]
        )

        lines = [
            f"The optimization engine selected {recommended.route_name} "
            f"because its weighted score was highest among feasible routes."
        ]

        if drivers_text:
            lines.append(
                f"Its strongest contributions to the final score came from {drivers_text}."
            )

        pareto_routes = [
            r
            for r in evidence.routes
            if r.is_pareto_efficient and r.route_id != recommended.route_id
        ]
        if pareto_routes:
            alt_names = [r.route_name for r in pareto_routes]
            lines.append(
                f"While {recommended.route_name} won the weighted recommendation, "
                f"other Pareto-efficient alternatives exist "
                f"({', '.join(alt_names)}) that might be attractive "
                f"under different priorities."
            )

        infeasible_routes = [r for r in evidence.routes if not r.is_feasible]
        if infeasible_routes:
            lines.append(
                f"Additionally, {len(infeasible_routes)} route(s) were "
                f"rejected due to hard constraint violations."
            )

        return ExplanationResponse(
            explanation=" ".join(lines),
            generated_by="deterministic",
            run_id=evidence.run_id,
        )

    # ------------------------------------------------------------------
    # Public: expose for testing
    # ------------------------------------------------------------------

    @classmethod
    def validate_structured(cls, evidence: ExplanationEvidence, structured: StructuredExplanation) -> None:
        cls._validate_structured(evidence, structured)
