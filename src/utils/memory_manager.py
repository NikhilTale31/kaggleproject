
"""Memory management utilities for handling GPU memory efficiently."""

import gc
import os
import torch
import psutil
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages GPU and system memory for model loading and inference."""
    
    @staticmethod
    def setup_memory_optimization():
        """Set up environment variables for memory optimization."""
        # Enable memory fragmentation fix
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'expandable_segments:True'
        
        # Additional memory optimizations
        os.environ['CUDA_LAUNCH_BLOCKING'] = '1'  # Helps with memory debugging
        os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:512,expandable_segments:True'
        
        logger.info("Memory optimization environment variables set")
    
    @staticmethod
    def clear_memory():
        """Aggressively clear GPU and CPU memory."""
        # Clear Python garbage
        gc.collect()
        
        # Clear GPU cache if CUDA is available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()
            
            # Force garbage collection multiple times
            for _ in range(3):
                gc.collect()
                torch.cuda.empty_cache()
        
        logger.info("Memory cleared")
    
    @staticmethod
    def get_memory_status() -> Dict[str, float]:
        """Get current memory usage statistics."""
        status = {}
        
        # GPU memory
        if torch.cuda.is_available():
            gpu_memory = torch.cuda.get_device_properties(0).total_memory
            gpu_reserved = torch.cuda.memory_reserved(0)
            gpu_allocated = torch.cuda.memory_allocated(0)
            gpu_free = gpu_memory - gpu_allocated
            
            status['gpu_total_gb'] = gpu_memory / 1024**3
            status['gpu_reserved_gb'] = gpu_reserved / 1024**3
            status['gpu_allocated_gb'] = gpu_allocated / 1024**3
            status['gpu_free_gb'] = gpu_free / 1024**3
            status['gpu_usage_percent'] = (gpu_allocated / gpu_memory) * 100
        
        # System memory
        vm = psutil.virtual_memory()
        status['ram_total_gb'] = vm.total / 1024**3
        status['ram_available_gb'] = vm.available / 1024**3
        status['ram_usage_percent'] = vm.percent
        
        return status
    
    @staticmethod
    def log_memory_status(prefix: str = ""):
        """Log current memory status."""
        status = MemoryManager.get_memory_status()
        
        logger.info(f"{prefix} Memory Status:")
        logger.info(f"  GPU: {status.get('gpu_allocated_gb', 0):.2f}/{status.get('gpu_total_gb', 0):.2f} GB "
                   f"({status.get('gpu_usage_percent', 0):.1f}% used)")
        logger.info(f"  RAM: {(status['ram_total_gb'] - status['ram_available_gb']):.2f}/{status['ram_total_gb']:.2f} GB "
                   f"({status['ram_usage_percent']:.1f}% used)")
    
    @staticmethod
    def check_memory_availability(required_gb: float) -> Tuple[bool, str]:
        """Check if enough memory is available for model loading."""
        status = MemoryManager.get_memory_status()
        
        gpu_free = status.get('gpu_free_gb', 0)
        ram_available = status.get('ram_available_gb', 0)
        
        if gpu_free >= required_gb:
            return True, f"GPU has {gpu_free:.2f} GB free (need {required_gb:.2f} GB)"
        elif ram_available >= required_gb * 2:  # Need more RAM for CPU loading
            return True, f"Can use CPU with {ram_available:.2f} GB RAM available"
        else:
            return False, f"Insufficient memory: GPU has {gpu_free:.2f} GB free, RAM has {ram_available:.2f} GB available (need {required_gb:.2f} GB)"
    
    @staticmethod
    def kill_zombie_processes():
        """Kill any zombie CUDA processes that might be holding memory."""
        try:
            import subprocess
            # Find and kill zombie python processes using GPU
            result = subprocess.run(['nvidia-smi', '--query-compute-apps=pid', '--format=csv,noheader'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                pids = [int(pid.strip()) for pid in result.stdout.strip().split('\n') if pid.strip()]
                current_pid = os.getpid()
                
                for pid in pids:
                    if pid != current_pid:
                        try:
                            os.kill(pid, 9)
                            logger.info(f"Killed zombie process {pid}")
                        except:
                            pass
        except Exception as e:
            logger.warning(f"Could not check for zombie processes: {e}")


def prepare_for_model_loading(model_size_gb: float = 20.0):
    """Prepare system for loading a large model."""
    logger.info(f"Preparing to load model (~{model_size_gb} GB)")
    
    # Setup optimization
    MemoryManager.setup_memory_optimization()
    
    # Clear memory
    MemoryManager.clear_memory()
    
    # Kill zombies
    MemoryManager.kill_zombie_processes()
    
    # Log status
    MemoryManager.log_memory_status("Before loading")
    
    # Check availability
    can_load, message = MemoryManager.check_memory_availability(model_size_gb)
    logger.info(f"Memory check: {message}")
    
    return can_load, message
