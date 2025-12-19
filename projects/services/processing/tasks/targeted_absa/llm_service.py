import logging
import torch
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
from langchain.prompts import PromptTemplate
from .dto import AbsaResultDTO

# Cấu hình log để theo dõi AI chạy
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbsaLocalService:
    def __init__(self, model_name="Qwen/Qwen2.5-1.5B-Instruct", device=-1):
        """
        Khởi tạo Qwen2.5 (Offline).
        """
        logger.info(f"AI: Đang tải model {model_name} (Sẽ mất vài phút lần đầu)...")
        
        # 1. Tải Tokenizer & Model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float32, # CPU dùng float32
            device_map="auto" if device >= 0 else "cpu",
            trust_remote_code=True
        )

        # 2. Tạo Pipeline (Nhiệm vụ: sinh văn bản)
        pipe = pipeline(
            "text-generation",
            model=self.model,
            tokenizer=self.tokenizer,
            max_new_tokens=128, # Giới hạn độ dài trả lời để chạy nhanh
            do_sample=False,    # Tắt ngẫu nhiên để kết quả ổn định
            temperature=0.1,
            repetition_penalty=1.1
        )

        self.llm = HuggingFacePipeline(pipeline=pipe)

        # 3. Prompt Engineering (Kỹ thuật ra lệnh cho AI)
        # Qwen dùng template ChatML (<|im_start|>)
        template = """<|im_start|>system
You are an expert AI assistant for Tourism Sentiment Analysis. 
Your task is to extract aspect-based sentiments from user reviews.
Target Aspects: Price, Food, Service, View, Location, Hygiene.
Sentiments: Positive, Negative, Neutral.

Output format: Aspect:Sentiment | Aspect:Sentiment
Example: Food:Positive | Price:Negative
<|im_end|>
<|im_start|>user
Review: "{text}"
Extract the aspects and sentiments. If none, return General:Neutral.
<|im_end|>
<|im_start|>assistant
"""
        self.prompt = PromptTemplate.from_template(template)
        self.chain = self.prompt | self.llm
        logger.info("AI: Model đã sẵn sàng!")

    def analyze_text(self, text, source_id):
        if not text: return []
        try:
            # Chạy model
            full_response = self.chain.invoke({"text": text})
            
            # Cắt lấy phần trả lời của AI (sau thẻ assistant)
            if "<|im_start|>assistant" in full_response:
                result_str = full_response.split("<|im_start|>assistant")[-1].strip()
            else:
                result_str = full_response.strip()
                
            logger.info(f"Review: {text[:30]}... -> AI: {result_str}")
            
            # Phân tích chuỗi kết quả (Parsing)
            results = []
            pairs = result_str.split('|')
            valid_aspects = ["Price", "Food", "Service", "View", "Location", "Hygiene", "General"]
            
            for pair in pairs:
                if ':' in pair:
                    parts = pair.split(':')
                    if len(parts) >= 2:
                        aspect = parts[0].strip()
                        sentiment = parts[1].strip()
                        
                        # Lọc rác (chỉ lấy đúng Aspect mình cần)
                        if aspect in valid_aspects:
                            results.append(AbsaResultDTO(
                                source_id=source_id,
                                source_text=text,
                                aspect=aspect,
                                sentiment=sentiment,
                                confidence=0.85 
                            ))
            return results
        except Exception as e:
            logger.error(f"AI Error: {e}")
            return []