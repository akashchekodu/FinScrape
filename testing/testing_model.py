from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

model_id = "TheBloke/Mistral-7B-Instruct-v0.2-GPTQ"  # 4-bit version

tokenizer = AutoTokenizer.from_pretrained(model_id, use_fast=True)
model = AutoModelForCausalLM.from_pretrained(
    model_id,
    device_map="auto",             # Automatically uses available GPU
    torch_dtype="auto",            # float16 or int4 based on model
    trust_remote_code=True         # Needed for some quantized models
)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)
print(pipe("Explain quantum computing in simple terms.", max_new_tokens=50))
