from __future__ import annotations

import asyncio
from typing import Any, Dict, Optional

import logging

try:
    import torch  # noqa: F401
except Exception:  # pragma: no cover
    torch = None  # type: ignore

try:
    from transformers import AutoModelForCausalLM, AutoTokenizer
except Exception as e:  # pragma: no cover
    raise RuntimeError("transformers must be installed to use hf_local backend") from e

from ..config import Config
from ..utils.logger import get_logger, log_exception


class HFLocalClient:
    """
    Local Hugging Face backend that mirrors APIClient's async context and generate() contract.

    Load order (to honor the user's requested snippet while remaining robust on low-VRAM GPUs):
      1) Try user's exact preferred load:
           model = AutoModelForCausalLM.from_pretrained(model_id, torch_dtype="auto", device_map="cuda")
         This can OOM on small GPUs (e.g., 4 GB). If it fails, we fallback automatically:
      2) device_map="auto" (Accelerate dispatch / CPU+offload as available)
      3) CPU-only load as last resort.

    Returns a dict shaped like APIClient.generate():
      {
        "output_text": str,
        "raw": dict,
        "meta": { "cached": bool, "cache_key": str }
      }

    Notes:
      - Caching is not implemented here (disk cache lives in APIClient). meta.cached=False always.
      - Tools are ignored (no tool execution in local backend).
    """

    def __init__(self, config: Config, logger_name: str = "hf-local") -> None:
        self.config = config
        self.logger: logging.Logger = get_logger(logger_name)
        self._tokenizer = None
        self._model = None
        self._started = False

    async def __aenter__(self) -> "HFLocalClient":
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.close()

    async def start(self) -> None:
        if self._started:
            return
        configured = (self.config.model or "openai/gpt-oss-20b").strip()
        model_id = configured if "/" in configured else f"openai/{configured}"

        # Optional HF auth token (for gated/private repos)
        import os
        token = getattr(self.config, "hf_token", None) or os.getenv("HUGGINGFACE_HUB_TOKEN") or os.getenv("HF_TOKEN")

        # Load tokenizer
        self.logger.info(f"[hf_local] Loading tokenizer: {model_id}")
        self._tokenizer = AutoTokenizer.from_pretrained(model_id, token=token)

        # Some tokenizers/models don't define pad token; align to eos if missing
        if getattr(self._tokenizer, "pad_token_id", None) is None and getattr(self._tokenizer, "eos_token_id", None) is not None:
            try:
                self._tokenizer.pad_token = self._tokenizer.eos_token  # type: ignore[attr-defined]
            except Exception:
                pass

        # Optional: 4-bit quantized load if configured (preferred on Kaggle T4×2)
        if bool(getattr(self.config, "hf_load_in_4bit", False)):
            try:
                from transformers import BitsAndBytesConfig  # type: ignore
                compute_str = str(getattr(self.config, "hf_bnb_4bit_compute_dtype", "float16")).lower()
                compute_dtype = None
                if "bfloat" in compute_str or compute_str in ("bf16", "bfloat16"):
                    compute_dtype = getattr(torch, "bfloat16", None) if torch is not None else None
                else:
                    compute_dtype = getattr(torch, "float16", None) if torch is not None else None

                bnb_config = BitsAndBytesConfig(
                    load_in_4bit=True,
                    bnb_4bit_quant_type=str(getattr(self.config, "hf_bnb_4bit_quant_type", "nf4")),
                    bnb_4bit_use_double_quant=bool(getattr(self.config, "hf_bnb_4bit_use_double_quant", True)),
                    bnb_4bit_compute_dtype=compute_dtype,
                )
                kwargs: Dict[str, Any] = {
                    "quantization_config": bnb_config,
                    "device_map": "auto",
                    "token": token,
                    "torch_dtype": torch.float16 if torch is not None else None,  # Specify dtype explicitly
                    "low_cpu_mem_usage": True,
                }
                max_memory = getattr(self.config, "hf_max_memory", None)
                if max_memory:
                    kwargs["max_memory"] = max_memory
                self._model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
                self.logger.info("[hf_local] Loaded 4-bit with device_map='auto'")
                self._started = True
                self.logger.info("[hf_local] Ready")
                return
            except Exception as e_q:
                log_exception(self.logger, "[hf_local] 4-bit load failed; falling back to non-quantized path", e_q)

        # Attempt user-requested load first (as provided in the task)
        # NOTE: This often OOMs on 4 GB GPUs; we catch and fallback automatically.
        self.logger.info("[hf_local] Attempting preferred load: device_map='cuda', torch_dtype='auto'")
        try:
            self._model = AutoModelForCausalLM.from_pretrained(
                model_id,
                torch_dtype="auto",
                device_map="cuda",
                token=token,
            )
            self.logger.info("[hf_local] Loaded with device_map='cuda'")
        except Exception as e1:
            log_exception(self.logger, "[hf_local] Preferred load failed, trying device_map='auto'", e1)
            try:
                kwargs: Dict[str, Any] = {
                    "torch_dtype": "auto",
                    "device_map": "auto",
                    "token": token,
                }
                max_memory = getattr(self.config, "hf_max_memory", None)
                if max_memory:
                    kwargs["max_memory"] = max_memory
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    **kwargs,
                )
                self.logger.info("[hf_local] Loaded with device_map='auto' (may use CPU/offload)")
            except Exception as e2:
                log_exception(self.logger, "[hf_local] device_map='auto' failed, falling back to CPU", e2)
                # Last resort: CPU-only load
                self._model = AutoModelForCausalLM.from_pretrained(
                    model_id,
                    torch_dtype="auto",
                    token=token,
                )
                self.logger.warning("[hf_local] Loaded on CPU. Generation will be slow.")

        self._started = True
        self.logger.info("[hf_local] Ready")

    async def close(self) -> None:
        # Nothing special to close for HF models; allow GC to reclaim
        self._started = False
        self.logger.info("[hf_local] Closed")

    def _build_text(self, prompt: str, system: Optional[str]) -> str:
        """
        Build a plain text prompt. The rest of the pipeline already collapses multi-turn.
        """
        if system:
            return f"System:\n{system}\n\nUser:\n{prompt}\n\nAssistant:"
        return prompt

    async def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        tools: Optional[list] = None,  # ignored
        metadata: Optional[dict] = None,  # passthrough ignored
        temperature: float = 0.2,
        max_tokens: Optional[int] = None,
    ) -> Dict[str, Any]:
        if not self._started:
            await self.start()
        assert self._tokenizer is not None and self._model is not None

        text = self._build_text(prompt, system)
        max_new_tokens = int(max_tokens) if max_tokens is not None else int(getattr(self.config, "hf_max_new_tokens", 256))

        do_sample = bool(getattr(self.config, "hf_do_sample", True))
        top_p = float(getattr(self.config, "hf_top_p", 0.95))
        temp = float(getattr(self.config, "hf_temperature", temperature if temperature is not None else 0.7))

        # Tokenize (remain on CPU; Transformers/Accelerate will dispatch as needed)
        inputs = self._tokenizer(text, return_tensors="pt")
        # Ensure pad/eos tokens are set
        eos_id = getattr(self._tokenizer, "eos_token_id", None)
        pad_id = getattr(self._tokenizer, "pad_token_id", None) or eos_id

        gen_kwargs: Dict[str, Any] = dict(
            max_new_tokens=max_new_tokens,
            do_sample=do_sample,
            top_p=top_p,
            temperature=max(0.0, temp),
            eos_token_id=eos_id,
            pad_token_id=pad_id,
        )

        try:
            # Run generation in a thread to avoid blocking the event loop
            outputs = await asyncio.to_thread(self._model.generate, **inputs, **gen_kwargs)
        except Exception as e:
            log_exception(self.logger, "[hf_local] Generation failed", e)
            raise

        try:
            decoded = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
            # Heuristic: return everything after the original text if present
            if decoded.startswith(text):
                output_text = decoded[len(text):].lstrip()
            else:
                output_text = decoded
        except Exception:
            output_text = ""

        raw = {
            "model": self.config.model,
            "backend": "hf_local",
            "generated_text": output_text,
            "tokens": getattr(outputs, "shape", None),
        }
        return {"output_text": output_text, "raw": raw, "meta": {"cached": False, "cache_key": ""}}


__all__ = ["HFLocalClient"]
