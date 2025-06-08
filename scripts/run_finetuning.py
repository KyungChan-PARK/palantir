"""Fine-tune base LLM using positive feedback stored in DB."""
import pandas as pd
from sqlalchemy import create_engine
from datasets import Dataset
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
from palantir.core.settings import settings

DB_URL = settings.database_url
BASE_MODEL = "gpt2"

engine = create_engine(DB_URL)

def load_feedback_df():
    query = "SELECT question, answer FROM llm_feedback WHERE feedback='like'"
    return pd.read_sql(query, engine)

def main():
    df = load_feedback_df()
    if df.empty:
        print("No positive feedback yet.")
        return
    ds = Dataset.from_pandas(df)
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)
    model = AutoModelForCausalLM.from_pretrained(BASE_MODEL)
    lora_config = LoraConfig(r=8, lora_alpha=16, target_modules=["c_attn"], lora_dropout=0.05)
    model = get_peft_model(model, lora_config)
    training_args = TrainingArguments(output_dir="./fine_tuned_adapter", per_device_train_batch_size=2, num_train_epochs=1)
    trainer = SFTTrainer(model=model, train_dataset=ds, dataset_text_field="answer", tokenizer=tokenizer, args=training_args)
    trainer.train()
    model.save_pretrained("./fine_tuned_adapter")

if __name__ == "__main__":
    main() 