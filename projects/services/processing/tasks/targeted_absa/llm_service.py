import logging
import torch
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline
# Cập nhật import cho LangChain bản mới
try:
    from langchain_core.prompts import PromptTemplate
except ImportError:
    # Fallback cho bản cũ nếu cần
    from langchain.prompts import PromptTemplate

from dto import AbsaResultDTO

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AbsaLocalService:
    def __init__(self, model_name='Qwen/Qwen2.5-1.5B-Instruct', device=-1):
        logger.info(f'AI: Loading model {model_name}...')
        try:
            self.tokenizer = AutoTokenizer.from_pretrained(model_name)
            self.model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float32,
                device_map='auto' if device >= 0 else 'cpu',
                trust_remote_code=True
            )
            pipe = pipeline(
                'text-generation',
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=128,
                do_sample=False,
                temperature=0.1,
                repetition_penalty=1.1
            )
            self.llm = HuggingFacePipeline(pipeline=pipe)
            
            # Prompt Qwen Chat Template
            template = \
'''<|im_start|>system
You are an expert AI for Tourism Sentiment Analysis. 
Task: Extract aspect-based sentiments. 
Aspects: Price, Food, Service, View, Location, Hygiene.
Sentiments: Positive, Negative, Neutral.
Format: Aspect:Sentiment | Aspect:Sentiment
<|im_end|>
<|im_start|>user
Review: {text}
<|im_end|>
<|im_start|>assistant
'''
            self.prompt = PromptTemplate.from_template(template)
            self.chain = self.prompt | self.llm
            logger.info('AI: Model loaded successfully!')
        except Exception as e:
            logger.error(f'AI Load Error: {e}')
            raise e

    def analyze_text(self, text, source_id):
        if not text: return []
        try:
            full_response = self.chain.invoke({'text': text})
            
            # Parsing response
            if '<|im_start|>assistant' in full_response:
                result_str = full_response.split('<|im_start|>assistant')[-1].strip()
            else:
                result_str = full_response.strip()
            
            logger.info(f'Review: {text[:30]}... -> AI: {result_str}')
            
            results = []
            pairs = result_str.split('|')
            valid_aspects = ['Price', 'Food', 'Service', 'View', 'Location', 'Hygiene', 'General']
            
            for pair in pairs:
                if ':' in pair:
                    parts = pair.split(':')
                    if len(parts) >= 2:
                        aspect = parts[0].strip()
                        sentiment = parts[1].strip()
                        # Simple cleanup
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
            logger.error(f'AI Processing Error: {e}')
            return []
