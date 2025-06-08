import logging
import os
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

logger = logging.getLogger(__name__)

BASE_MODEL = "gpt2"
ADAPTER_PATH = "./fine_tuned_adapter"

tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)

if os.path.exists(ADAPTER_PATH):
    try:
        model = PeftModel.from_pretrained(model, ADAPTER_PATH)
        logger.info("LoRA adapter loaded.")
    except Exception as exc:
        logger.error("Failed loading adapter: %s", exc)

__all__ = ["model", "tokenizer"]
