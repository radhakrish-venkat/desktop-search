"""
Local LLM Integration for Enhanced Search
Provides ChatGPT-like search enhancement capabilities using local models
"""

import os
import sys
import logging
import json
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmbeddingModel(str, Enum):
    """Embedding model options"""
    BGE_SMALL_EN = "bge-small-en"
    NOMIC_EMBED_TEXT = "nomic-embed-text"
    ALL_MINI_LM_L6_V2 = "all-MiniLM-L6-v2"  # Default fallback

class LLMModel(str, Enum):
    """LLM model options"""
    PHI3 = "phi3"
    MISTRAL = "mistral"
    LLAMA2 = "llama2"  # Fallback
    CODELLAMA = "codellama"  # Code-focused

@dataclass
class LLMConfig:
    """Configuration for local LLM models"""
    # LLM Configuration
    llm_model: str = "phi3"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_top_p: float = 0.9
    llm_context_window: int = 4096
    
    # Embedding Configuration
    embedding_model: str = "bge-small-en"
    embedding_dimension: int = 384  # bge-small-en dimension
    
    # General Configuration
    chunk_overlap: int = 200
    max_chunk_size: int = 1000

class LocalLLMProvider:
    """Base class for local LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = None
        self.is_loaded = False
    
    def load_model(self) -> bool:
        """Load the LLM model"""
        raise NotImplementedError
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response from the model"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        raise NotImplementedError

class OllamaProvider(LocalLLMProvider):
    """Ollama LLM provider for local models"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.ollama_client = None
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            import requests
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def load_model(self) -> bool:
        """Load Ollama model"""
        try:
            import requests
            
            # Check if model is available
            response = requests.get("http://localhost:11434/api/tags")
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model["name"] for model in models]
                
                # Try preferred model first, then fallbacks
                preferred_models = [self.config.llm_model, "phi3", "mistral", "llama2"]
                available_model = None
                
                for model in preferred_models:
                    if model in model_names:
                        available_model = model
                        break
                
                if available_model:
                    logger.info(f"Ollama model {available_model} is available")
                    self.config.llm_model = available_model
                    self.is_loaded = True
                    return True
                else:
                    logger.warning(f"Preferred Ollama models not found. Available: {model_names}")
                    return False
            else:
                logger.error("Failed to connect to Ollama server")
                return False
                
        except Exception as e:
            logger.error(f"Error loading Ollama model: {e}")
            return False
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using Ollama"""
        if not self.is_loaded:
            if not self.load_model():
                return "Error: Model not loaded"
        
        try:
            import requests
            
            # Prepare the full prompt with context
            full_prompt = f"""Context: {context}

Question: {prompt}

Please provide a helpful answer based on the context above. If the context doesn't contain relevant information, say so."""
            
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.config.llm_model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": self.config.llm_temperature,
                        "top_p": self.config.llm_top_p,
                        "num_predict": self.config.llm_max_tokens
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "No response generated")
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return "Error: Failed to generate response"
                
        except Exception as e:
            logger.error(f"Error generating response with Ollama: {e}")
            return f"Error: {str(e)}"

class LocalAIProvider(LocalLLMProvider):
    """LocalAI provider for local models"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
    
    def is_available(self) -> bool:
        """Check if LocalAI is available"""
        try:
            import requests
            response = requests.get("http://localhost:8080/v1/models", timeout=5)
            return response.status_code == 200
        except:
            return False
    
    def load_model(self) -> bool:
        """Load LocalAI model"""
        try:
            import requests
            
            # Check if model is available
            response = requests.get("http://localhost:8080/v1/models")
            if response.status_code == 200:
                models = response.json().get("data", [])
                model_ids = [model["id"] for model in models]
                
                # Try preferred model first, then fallbacks
                preferred_models = [self.config.llm_model, "phi3", "mistral", "gpt4all"]
                available_model = None
                
                for model in preferred_models:
                    if model in model_ids:
                        available_model = model
                        break
                
                if available_model:
                    logger.info(f"LocalAI model {available_model} is available")
                    self.config.llm_model = available_model
                    self.is_loaded = True
                    return True
                else:
                    logger.warning(f"Preferred LocalAI models not found. Available: {model_ids}")
                    return False
            else:
                logger.error("Failed to connect to LocalAI server")
                return False
                
        except Exception as e:
            logger.error(f"Error loading LocalAI model: {e}")
            return False
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response using LocalAI"""
        if not self.is_loaded:
            if not self.load_model():
                return "Error: Model not loaded"
        
        try:
            import requests
            
            # Prepare the full prompt with context
            full_prompt = f"""Context: {context}

Question: {prompt}

Please provide a helpful answer based on the context above. If the context doesn't contain relevant information, say so."""
            
            response = requests.post(
                f"http://localhost:8080/v1/completions",
                json={
                    "model": self.config.llm_model,
                    "prompt": full_prompt,
                    "max_tokens": self.config.llm_max_tokens,
                    "temperature": self.config.llm_temperature,
                    "top_p": self.config.llm_top_p,
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                choices = result.get("choices", [])
                if choices:
                    return choices[0].get("text", "No response generated")
                else:
                    return "No response generated"
            else:
                logger.error(f"LocalAI API error: {response.status_code}")
                return "Error: Failed to generate response"
                
        except Exception as e:
            logger.error(f"Error generating response with LocalAI: {e}")
            return f"Error: {str(e)}"

class EmbeddingManager:
    """Manager for embedding models"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.embedding_model = None
        self.is_loaded = False
    
    def load_embedding_model(self) -> bool:
        """Load the embedding model"""
        try:
            from sentence_transformers import SentenceTransformer
            
            # Try preferred model first, then fallbacks
            preferred_models = [
                self.config.embedding_model,
                "bge-small-en",
                "nomic-embed-text",
                "all-MiniLM-L6-v2"
            ]
            
            for model_name in preferred_models:
                try:
                    logger.info(f"Loading embedding model: {model_name}")
                    self.embedding_model = SentenceTransformer(model_name)
                    self.config.embedding_model = model_name
                    self.is_loaded = True
                    logger.info(f"Successfully loaded embedding model: {model_name}")
                    return True
                except Exception as e:
                    logger.warning(f"Failed to load {model_name}: {e}")
                    continue
            
            logger.error("Failed to load any embedding model")
            return False
            
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            return False
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts"""
        if not self.is_loaded:
            if not self.load_embedding_model():
                return []
        
        try:
            if self.embedding_model is not None:
                embeddings = self.embedding_model.encode(texts)
                return embeddings.tolist()
            else:
                logger.error("Embedding model not loaded")
                return []
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of the embedding model"""
        if self.embedding_model is not None:
            dimension = self.embedding_model.get_sentence_embedding_dimension()
            return dimension if dimension is not None else self.config.embedding_dimension
        return self.config.embedding_dimension

class LocalLLMManager:
    """Manager for local LLM integration with enhanced model support"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.providers = {}
        self.active_provider = None
        self.embedding_manager = EmbeddingManager(self.config)
        self.search_context = {}
    
    def register_provider(self, name: str, provider: LocalLLMProvider):
        """Register an LLM provider"""
        self.providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")
    
    def detect_providers(self) -> List[str]:
        """Detect available LLM providers"""
        available = []
        
        # Check Ollama with enhanced model support
        ollama_config = LLMConfig(
            llm_model="phi3",
            embedding_model="bge-small-en",
            llm_max_tokens=2048,
            llm_temperature=0.7
        )
        ollama_provider = OllamaProvider(ollama_config)
        if ollama_provider.is_available():
            self.register_provider("ollama", ollama_provider)
            available.append("ollama")
        
        # Check LocalAI
        localai_config = LLMConfig(
            llm_model="phi3",
            embedding_model="bge-small-en",
            llm_max_tokens=2048,
            llm_temperature=0.7
        )
        localai_provider = LocalAIProvider(localai_config)
        if localai_provider.is_available():
            self.register_provider("localai", localai_provider)
            available.append("localai")
        
        return available
    
    def set_active_provider(self, provider_name: str) -> bool:
        """Set the active LLM provider"""
        if provider_name in self.providers:
            self.active_provider = self.providers[provider_name]
            logger.info(f"Set active LLM provider: {provider_name}")
            return True
        else:
            logger.error(f"Provider {provider_name} not found")
            return False
    
    def get_embedding_model_info(self) -> Dict[str, Any]:
        """Get information about the embedding model"""
        if not self.embedding_manager.is_loaded:
            self.embedding_manager.load_embedding_model()
        
        return {
            "model_name": self.config.embedding_model,
            "dimension": self.embedding_manager.get_embedding_dimension(),
            "loaded": self.embedding_manager.is_loaded
        }
    
    def enhance_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance search results with LLM-generated insights"""
        if not self.active_provider:
            available = self.detect_providers()
            if available:
                self.set_active_provider(available[0])
            else:
                return {
                    "enhanced": False,
                    "message": "No local LLM providers available",
                    "results": search_results
                }
        
        if not self.active_provider:
            return {
                "enhanced": False,
                "message": "No local LLM providers available",
                "results": search_results
            }
        
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Generate enhanced response
            enhanced_response = self.active_provider.generate_response(
                prompt=f"Based on the search results for '{query}', provide a comprehensive summary and insights. Include key findings, patterns, and recommendations.",
                context=context
            )
            
            return {
                "enhanced": True,
                "query": query,
                "llm_response": enhanced_response,
                "results": search_results,
                "provider": type(self.active_provider).__name__,
                "llm_model": self.active_provider.config.llm_model,
                "embedding_model": self.config.embedding_model
            }
            
        except Exception as e:
            logger.error(f"Error enhancing search results: {e}")
            return {
                "enhanced": False,
                "message": f"Error enhancing results: {str(e)}",
                "results": search_results
            }
    
    def answer_question(self, question: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer a specific question based on search results"""
        if not self.active_provider:
            available = self.detect_providers()
            if available:
                self.set_active_provider(available[0])
            else:
                return {
                    "answered": False,
                    "message": "No local LLM providers available",
                    "answer": "I cannot answer this question as no local LLM is available."
                }
        
        if not self.active_provider:
            return {
                "answered": False,
                "message": "No local LLM providers available",
                "answer": "I cannot answer this question as no local LLM is available."
            }
        
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Generate answer
            answer = self.active_provider.generate_response(
                prompt=question,
                context=context
            )
            
            return {
                "answered": True,
                "question": question,
                "answer": answer,
                "provider": type(self.active_provider).__name__,
                "llm_model": self.active_provider.config.llm_model,
                "embedding_model": self.config.embedding_model,
                "sources": [result.get('filepath', 'Unknown') for result in search_results]
            }
            
        except Exception as e:
            logger.error(f"Error answering question: {e}")
            return {
                "answered": False,
                "message": f"Error answering question: {str(e)}",
                "answer": "I encountered an error while trying to answer your question."
            }
    
    def generate_summary(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of search results"""
        if not self.active_provider:
            available = self.detect_providers()
            if available:
                self.set_active_provider(available[0])
            else:
                return {
                    "summarized": False,
                    "message": "No local LLM providers available",
                    "summary": "Cannot generate summary as no local LLM is available."
                }
        
        if not self.active_provider:
            return {
                "summarized": False,
                "message": "No local LLM providers available",
                "summary": "Cannot generate summary as no local LLM is available."
            }
        
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Generate summary
            summary = self.active_provider.generate_response(
                prompt="Provide a concise summary of the key information found in these search results. Highlight the most important points and any patterns or insights.",
                context=context
            )
            
            return {
                "summarized": True,
                "summary": summary,
                "provider": type(self.active_provider).__name__,
                "llm_model": self.active_provider.config.llm_model,
                "embedding_model": self.config.embedding_model,
                "result_count": len(search_results)
            }
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return {
                "summarized": False,
                "message": f"Error generating summary: {str(e)}",
                "summary": "I encountered an error while trying to generate a summary."
            }
    
    def _prepare_context(self, search_results: List[Dict[str, Any]]) -> str:
        """Prepare context from search results for LLM"""
        if not search_results:
            return "No search results available."
        
        context_parts = []
        for i, result in enumerate(search_results[:10], 1):  # Limit to top 10 results
            filepath = result.get('filepath', 'Unknown file')
            filename = result.get('filename', os.path.basename(filepath))
            snippet = result.get('snippet', 'No content available')
            score = result.get('score', result.get('similarity', 0))
            
            context_parts.append(f"""
Document {i}: {filename}
Relevance Score: {score:.3f}
Content: {snippet}
---""")
        
        return "\n".join(context_parts)
    
    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all LLM providers and models"""
        status = {
            "active_provider": type(self.active_provider).__name__ if self.active_provider else None,
            "available_providers": [],
            "detected_providers": self.detect_providers(),
            "embedding_model": self.get_embedding_model_info(),
            "llm_model": self.active_provider.config.llm_model if self.active_provider else None
        }
        
        for name, provider in self.providers.items():
            status["available_providers"].append({
                "name": name,
                "type": type(provider).__name__,
                "available": provider.is_available(),
                "loaded": provider.is_loaded,
                "llm_model": provider.config.llm_model
            })
        
        return status

# Global LLM manager instance
llm_manager = LocalLLMManager()

def get_llm_manager() -> LocalLLMManager:
    """Get the global LLM manager instance"""
    return llm_manager 