import os
import json
import re
import time
import logging
from typing import Any, Dict, List, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class NvidiaAIService:
    """
    Centralized NVIDIA AI NIM Integration Service.
    Supports Nemotron Ultra 550B primary reasoning, Nemotron Super 120B fallback,
    NemoGuard content safety moderation, and transparent diagnostics.
    """

    def __init__(self):
        self.api_key = os.environ.get("NVIDIA_API_KEY", "").strip().strip('"').strip("'")
        self.base_url = os.environ.get("NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1").strip()
        self.client: Optional[OpenAI] = None
        self.is_configured = bool(self.api_key and not self.api_key.startswith("nvapi-your"))

        # Configured model preferences
        self.configured_primary = os.environ.get("PRIMARY_REASONING_MODEL", "nvidia/nemotron-3-ultra-550b-a55b").strip()
        self.configured_secondary = os.environ.get("SECONDARY_REASONING_MODEL", "nvidia/nemotron-3-super-120b-a12b").strip()
        self.configured_fast = os.environ.get("FAST_MODEL", "nvidia/nemotron-3.5-lightning-30b-a3b").strip()
        self.configured_guardrail = os.environ.get("GUARDRAIL_MODEL", "nvidia/llama-3.1-nemoguard-8b-content-safety").strip()

        # Active models resolved against catalog
        self.active_primary_model = self.configured_primary
        self.active_secondary_model = self.configured_secondary
        self.active_guardrail_model = self.configured_guardrail
        self.fallback_active = False
        self.fallback_reason: Optional[str] = None
        self.discovered_catalog: List[str] = []
        self.last_discovery_time = 0.0
        self.last_latency_ms = 0.0
        self.last_error: Optional[str] = None

        if self.is_configured:
            try:
                self.client = OpenAI(
                    base_url=self.base_url,
                    api_key=self.api_key,
                    timeout=35.0,
                    max_retries=0,
                )
                self._discover_and_validate()
            except Exception as e:
                logger.error(f"[NvidiaAIService] Initialization error: {e}")
                self.last_error = str(e)

    def _discover_and_validate(self) -> None:
        """Discovers accessible models from the NVIDIA catalog for the supplied key."""
        if not self.client:
            return
        try:
            t0 = time.time()
            models_response = self.client.models.list()
            self.discovered_catalog = [m.id for m in models_response.data]
            self.last_discovery_time = time.time()

            # Verify Primary Reasoning Model
            if self.configured_primary in self.discovered_catalog:
                self.active_primary_model = self.configured_primary
            elif self.configured_secondary in self.discovered_catalog:
                self.active_primary_model = self.configured_secondary
                self.fallback_active = True
                self.fallback_reason = f"Primary model {self.configured_primary} not in catalog; switched to secondary {self.configured_secondary}"
            else:
                # Text-capable fallback
                fallbacks = ["meta/llama-3.2-11b-vision-instruct", "meta/llama-3.2-90b-vision-instruct"]
                matched = next((m for m in fallbacks if m in self.discovered_catalog), None)
                self.active_primary_model = matched or self.configured_primary
                self.fallback_active = True
                self.fallback_reason = f"Neither Ultra nor Super available; fell back to {self.active_primary_model}"

            # Verify Secondary Fallback
            if self.configured_secondary in self.discovered_catalog:
                self.active_secondary_model = self.configured_secondary
            else:
                self.active_secondary_model = "meta/llama-3.2-11b-vision-instruct"

            # Verify Guardrail Model
            if self.configured_guardrail in self.discovered_catalog:
                self.active_guardrail_model = self.configured_guardrail
            else:
                self.active_guardrail_model = "disabled"

            self.last_latency_ms = round((time.time() - t0) * 1000, 2)
            logger.info(
                f"[NvidiaAIService] Discovery Completed: Primary={self.active_primary_model}, "
                f"Secondary={self.active_secondary_model}, Guardrail={self.active_guardrail_model}, "
                f"CatalogCount={len(self.discovered_catalog)}"
            )
        except Exception as e:
            logger.warning(f"[NvidiaAIService] Catalog discovery failed, using configured defaults: {e}")
            self.last_error = str(e)

    def get_diagnostics(self) -> Dict[str, Any]:
        """Provides developer/admin diagnostics without leaking secrets."""
        masked_key = f"********{self.api_key[-4:]}" if len(self.api_key) >= 4 else "UNCONFIGURED"
        return {
            "provider": "NVIDIA",
            "endpoint": self.base_url,
            "api_configured": self.is_configured,
            "masked_key": masked_key,
            "primary_configured_model": self.configured_primary,
            "primary_active_model": self.active_primary_model,
            "secondary_active_model": self.active_secondary_model,
            "guardrail_model": self.active_guardrail_model,
            "fallback_active": self.fallback_active,
            "fallback_reason": self.fallback_reason,
            "catalog_count": len(self.discovered_catalog),
            "last_latency_ms": self.last_latency_ms,
            "last_error": self.last_error,
            "timestamp": time.time()
        }

    def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 1500,
        model: Optional[str] = None
    ) -> Optional[str]:
        """Executes chat completion with automated secondary fallback if primary fails."""
        if not self.client:
            raise RuntimeError("NVIDIA AI service is not configured with a valid API key.")

        target_model = model or self.active_primary_model
        t0 = time.time()

        try:
            completion = self.client.chat.completions.create(
                model=target_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self.last_latency_ms = round((time.time() - t0) * 1000, 2)
            content = completion.choices[0].message.content
            return content.strip() if content else None
        except Exception as primary_err:
            logger.warning(f"[NvidiaAIService] Primary model {target_model} failed: {primary_err}")
            self.last_error = str(primary_err)

            # Attempt secondary fallback if this was the primary model
            if target_model == self.active_primary_model and self.active_secondary_model != target_model:
                try:
                    logger.info(f"[NvidiaAIService] Attempting secondary fallback on {self.active_secondary_model}...")
                    fallback_comp = self.client.chat.completions.create(
                        model=self.active_secondary_model,
                        messages=messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                    )
                    self.fallback_active = True
                    self.fallback_reason = f"Primary model {target_model} failed with: {primary_err}"
                    content = fallback_comp.choices[0].message.content
                    return content.strip() if content else None
                except Exception as secondary_err:
                    logger.error(f"[NvidiaAIService] Secondary model {self.active_secondary_model} also failed: {secondary_err}")
                    raise secondary_err
            raise primary_err

    def extract_structured_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely parses structured JSON from AI output, stripping markdown blocks."""
        if not text:
            return None
        try:
            clean = text.replace("```json", "").replace("```", "").strip()
            match = re.search(r"\{.*\}", clean, re.DOTALL)
            if match:
                return json.loads(match.group(0))
            return json.loads(clean)
        except json.JSONDecodeError as e:
            logger.warning(f"[NvidiaAIService] JSON parse failed: {e}. Snippet: {text[:100]}...")
            return None

nvidia_service = NvidiaAIService()
