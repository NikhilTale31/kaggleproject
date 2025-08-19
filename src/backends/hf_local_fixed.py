import torch
import gc
import os
from typing import Optional, Dict, Any
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

logger = logging.getLogger(__name__)

class HFLocalFixed:
    """Fixed version of HF Local backend with better memory management"""
    
    def __init__(self, model_name: str, **kwargs):
        self.model_name = model_name
        self._model = None
        self._tokenizer = None
        self.device = None
        
    def start(self):
        """Initialize model with proper memory management"""
        try:
            # Clear any existing CUDA cache
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
                torch.cuda.synchronize()
                gc.collect()
            
            # Set memory allocation config
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
            
            # Load tokenizer first (lightweight)
            logger.info(f"Loading tokenizer: {self.model_name}")
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=True
            )
            
            # Try different loading strategies
            loading_strategies = [
                {
                    "device_map": "auto",
                    "torch_dtype": torch.float16,  # Use fp16 instead of auto
                    "low_cpu_mem_usage": True,
                    "offload_folder": "offload",
                    "offload_state_dict": True,
                },
                {
                    "device_map": {
                        "": "cuda:0"  # Force single GPU
                    },
                    "torch_dtype": torch.float16,
                    "low_cpu_mem_usage": True,
                    "max_memory": {0: "38GiB", "cpu": "70GiB"},
                },
                {
                    "device_map": "balanced",
                    "torch_dtype": torch.float16,
                    "low_cpu_mem_usage": True,
                    "offload_folder": "offload",
                }
            ]
            
            for i, strategy in enumerate(loading_strategies):
                try:
                    logger.info(f"Attempting loading strategy {i+1}/{len(loading_strategies)}")
                    self._model = AutoModelForCausalLM.from_pretrained(
                        self.model_name,
                        trust_remote_code=True,
                        **strategy
                    )
                    logger.info(f"Successfully loaded model with strategy {i+1}")
                    break
                except torch.cuda.OutOfMemoryError as e:
                    logger.warning(f"Strategy {i+1} failed: {str(e)}")
                    # Clean up
                    if self._model is not None:
                        del self._model
                        self._model = None
                    torch.cuda.empty_cache()
                    gc.collect()
                    continue
            
            if self._model is None:
                raise RuntimeError("All loading strategies failed")
                
            # Set device
            if hasattr(self._model, 'device'):
                self.device = self._model.device
            else:
                self.device = next(self._model.parameters()).device
                
        except Exception as e:
            logger.error(f"Failed to load model: {str(e)}")
            raise
            
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate response with memory-efficient settings"""
        if self._model is None:
            raise RuntimeError("Model not loaded")
            
        # Prepare inputs
        inputs = self._tokenizer(prompt, return_tensors="pt", truncation=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Memory-efficient generation settings
        gen_kwargs = {
            "max_new_tokens": kwargs.get("max_new_tokens", 512),
            "temperature": kwargs.get("temperature", 0.7),
            "do_sample": kwargs.get("do_sample", True),
            "top_p": kwargs.get("top_p", 0.9),
            "pad_token_id": self._tokenizer.pad_token_id,
            "eos_token_id": self._tokenizer.eos_token_id,
            "use_cache": True,  # Enable KV cache
        }
        
        # Generate with gradient checkpointing disabled
        with torch.no_grad():
            outputs = self._model.generate(**inputs, **gen_kwargs)
            
        # Decode
        response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Clean up intermediate tensors
        del inputs, outputs
        torch.cuda.empty_cache()
        
        return response
        
    def stop(self):
        """Properly clean up resources"""
        if self._model is not None:
            del self._model
            self._model = None
        if self._tokenizer is not None:
            del self._tokenizer
            self._tokenizer = None
        
        # Force garbage collection and clear CUDA cache
        gc.collect()
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
