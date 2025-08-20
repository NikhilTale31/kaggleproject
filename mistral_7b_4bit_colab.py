"""
Mistral-7B 4-bit Quantization Script for Google Colab (A100 GPU)
This script properly loads and uses the Mistral-7B-Instruct model with 4-bit quantization.
"""

import torch
from transformers import (
    AutoModelForCausalLM, 
    AutoTokenizer, 
    BitsAndBytesConfig,
    pipeline
)
import warnings

# Suppress non-critical warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

def load_mistral_7b_4bit():
    """
    Load Mistral-7B-Instruct model with proper 4-bit quantization configuration.
    """
    print("🚀 Starting Mistral-7B 4-bit model loading...")
    
    # Model identifier
    model_id = "mistralai/Mistral-7B-Instruct-v0.1"
    
    # Configure 4-bit quantization properly
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_use_double_quant=True,  # Use nested quantization for better memory efficiency
        bnb_4bit_quant_type="nf4",       # Use NormalFloat4 quantization
        bnb_4bit_compute_dtype=torch.float16  # Compute in float16 for better performance
    )
    
    print("📥 Loading tokenizer...")
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(model_id)
    
    # Set padding token if not already set
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    
    print("📥 Loading model with 4-bit quantization...")
    # Load model with quantization config
    # Important: Do NOT call .to('cuda') on quantized models - they're already on the correct device
    model = AutoModelForCausalLM.from_pretrained(
        model_id,
        quantization_config=bnb_config,
        device_map="auto",  # Automatically handle device placement
        trust_remote_code=True,
        torch_dtype=torch.float16  # Specify dtype explicitly
    )
    
    print("✅ Model loaded successfully!")
    print(f"   - Model device map: {model.hf_device_map}")
    print(f"   - Model memory footprint: ~{model.get_memory_footprint() / 1e9:.2f} GB")
    
    return model, tokenizer

def test_model(model, tokenizer):
    """
    Test the loaded model with a simple generation task.
    """
    print("\n🧪 Testing model generation...")
    
    # Test prompt
    prompt = "What are the key benefits of using 4-bit quantization for large language models?"
    
    # Tokenize input
    inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True)
    
    # Move inputs to the same device as the model
    # For quantized models, we need to check where the model is
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}
    
    # Generate response
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=150,
            temperature=0.7,
            do_sample=True,
            top_p=0.95,
            pad_token_id=tokenizer.pad_token_id,
            eos_token_id=tokenizer.eos_token_id
        )
    
    # Decode and print response
    response = tokenizer.decode(outputs[0], skip_special_tokens=True)
    print(f"\n💬 Model Response:\n{response}")

def create_chat_pipeline(model, tokenizer):
    """
    Create a convenient chat pipeline for interactive use.
    """
    print("\n🔧 Creating chat pipeline...")
    
    # Create text generation pipeline
    chat_pipeline = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        device_map="auto",
        max_new_tokens=512,
        do_sample=True,
        temperature=0.7,
        top_p=0.95
    )
    
    print("✅ Chat pipeline ready!")
    return chat_pipeline

def chat_with_model(pipeline, message):
    """
    Simple chat interface for the model.
    """
    # Format message in Mistral instruction format
    formatted_message = f"[INST] {message} [/INST]"
    
    # Generate response
    response = pipeline(formatted_message, return_full_text=False)
    
    return response[0]['generated_text']

def main():
    """
    Main execution function.
    """
    try:
        # Check CUDA availability
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available. This script requires a GPU.")
        
        print(f"🖥️  GPU: {torch.cuda.get_device_name(0)}")
        print(f"📊 GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1e9:.2f} GB")
        
        # Load model
        model, tokenizer = load_mistral_7b_4bit()
        
        # Test model
        test_model(model, tokenizer)
        
        # Create chat pipeline
        chat_pipeline = create_chat_pipeline(model, tokenizer)
        
        # Example chat
        print("\n💬 Example Chat:")
        response = chat_with_model(chat_pipeline, "Explain quantum computing in simple terms.")
        print(f"Response: {response}")
        
        print("\n✅ All operations completed successfully!")
        
        # Return model and tokenizer for further use
        return model, tokenizer, chat_pipeline
        
    except Exception as e:
        print(f"\n❌ Error occurred: {str(e)}")
        raise

if __name__ == "__main__":
    model, tokenizer, chat_pipeline = main()
