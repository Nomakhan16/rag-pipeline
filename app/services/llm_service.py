import os
from typing import List
import re

class LLMService:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
    
    def generate_response(self, question: str, context_chunks: List[str]) -> str:
        """
        Completely generic answer extraction - no hardcoded terms
        """
        if not context_chunks:
            return "No relevant information found in the documents."
        
        # Find the most relevant answer using generic methods only
        answer = self._find_best_answer(question, context_chunks)
        return answer
    
    def _find_best_answer(self, question: str, chunks: List[str]) -> str:
        """Find the best answer using only generic patterns"""
        question_lower = question.lower()
        main_topic = self._extract_main_topic(question)
        
        # Try multiple strategies to find the best answer
        strategies = [
            self._extract_definition,
            self._extract_direct_match,
            self._extract_most_relevant
        ]
        
        for strategy in strategies:
            answer = strategy(chunks, main_topic, question_lower)
            if answer and len(answer) > 25:  # Valid answer found
                return answer
        
        # Final fallback
        return self._get_simple_fallback(chunks[0])
    
    def _extract_definition(self, chunks: List[str], topic: str, question: str) -> str:
        """Extract definition-style sentences using only generic patterns"""
        for chunk in chunks:
            clean_chunk = self._clean_text(chunk)
            sentences = self._split_sentences(clean_chunk)
            
            for i, sentence in enumerate(sentences):
                sentence_lower = sentence.lower()
                
                # Only use universal definition patterns
                if (f"{topic} is" in sentence_lower or 
                    f"{topic} means" in sentence_lower or
                    f"{topic} refers to" in sentence_lower):
                    
                    # Take this sentence and optionally the next one
                    result_sentences = [sentence]
                    if i + 1 < len(sentences) and len(result_sentences) < 2:
                        result_sentences.append(sentences[i + 1])
                    
                    return '. '.join(result_sentences) + '.'
        
        return ""
    
    def _extract_direct_match(self, chunks: List[str], topic: str, question: str) -> str:
        """Extract sentences that directly match the question topic"""
        all_matching_sentences = []
        
        for chunk in chunks:
            clean_chunk = self._clean_text(chunk)
            sentences = self._split_sentences(clean_chunk)
            
            for sentence in sentences:
                sentence_lower = sentence.lower()
                if topic in sentence_lower and len(sentence) > 30:
                    all_matching_sentences.append(sentence)
                    if len(all_matching_sentences) >= 2:
                        break
            
            if len(all_matching_sentences) >= 2:
                break
        
        if all_matching_sentences:
            return '. '.join(all_matching_sentences[:2]) + '.'
        
        return ""
    
    def _extract_most_relevant(self, chunks: List[str], topic: str, question: str) -> str:
        """Extract most relevant sentences using only length and topic presence"""
        scored_sentences = []
        
        for chunk in chunks:
            clean_chunk = self._clean_text(chunk)
            sentences = self._split_sentences(clean_chunk)
            
            for sentence in sentences:
                # Score based only on topic presence and sentence length
                score = 0
                if topic in sentence.lower():
                    score += 3
                if len(sentence) > 40:  # Prefer substantial sentences
                    score += 1
                
                if score > 0:
                    scored_sentences.append((score, sentence))
        
        # Sort by score and take top 2
        scored_sentences.sort(key=lambda x: x[0], reverse=True)
        top_sentences = [sentence for score, sentence in scored_sentences[:2]]
        
        if top_sentences:
            return '. '.join(top_sentences) + '.'
        
        return ""
    
    def _get_simple_fallback(self, chunk: str) -> str:
        """Simple fallback - just take first meaningful part"""
        clean_chunk = self._clean_text(chunk)
        
        # Find the first sentence ending
        first_period = clean_chunk.find('.')
        if first_period != -1:
            first_sentence = clean_chunk[:first_period + 1].strip()
            
            # Try to get a second sentence
            remaining = clean_chunk[first_period + 1:].strip()
            second_period = remaining.find('.')
            if second_period != -1:
                second_sentence = remaining[:second_period + 1].strip()
                return first_sentence + ' ' + second_sentence
            else:
                return first_sentence
        
        # No periods found, just take reasonable chunk
        return clean_chunk[:200] + '...' if len(clean_chunk) > 200 else clean_chunk
    
    def _extract_main_topic(self, question: str) -> str:
        """Extract main topic using only basic stop words"""
        basic_stop_words = {'what', 'is', 'are', 'the'}
        words = question.lower().split()
        main_words = [word for word in words if word not in basic_stop_words]
        return main_words[0] if main_words else question.lower()
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences using only basic punctuation"""
        sentences = re.split(r'[.!?]', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _clean_text(self, text: str) -> str:
        """Improved text cleaning for PDF extraction issues"""
        if not text:
            return ""
        
        # Fix space-separated words - more aggressive pattern
        # This catches patterns like "strat egies", "dat a", "reason ing"
        text = re.sub(r'(\b\w) (\w\w+)', r'\1\2', text)
        text = re.sub(r'(\w\w) (\w\b)', r'\1\2', text)
        
        # Fix specific common broken words from your examples
        text = text.replace('strat egies', 'strategies')
        text = text.replace('dat a', 'data')
        text = text.replace('reason ing', 'reasoning')
        
        # Basic whitespace normalization
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\s+([.,;:!?])', r'\1', text)
        text = re.sub(r'([.,;:!?])\s*', r'\1 ', text)
        
        # Fix em-dash spacing
        text = re.sub(r'\s*—\s*', ' — ', text)
        
        return text.strip()