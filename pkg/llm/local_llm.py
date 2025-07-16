"""
Local LLM Integration for Enhanced Search
Provides ChatGPT-like search enhancement capabilities using local models
"""

import os
import sys
import logging
import requests
from requests.adapters import HTTPAdapter
import json
import time
import functools
import threading
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from pathlib import Path
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

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
    """Configuration for local LLM models with performance optimizations"""
    # LLM Configuration
    llm_model: str = "phi3"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.7
    llm_top_p: float = 0.9
    llm_context_window: int = 4096
    
    # Performance Optimizations
    use_gpu: bool = True
    batch_size: int = 4
    cache_responses: bool = True
    cache_size: int = 1000
    max_concurrent_requests: int = 8
    request_timeout: int = 60
    enable_streaming: bool = False
    
    # Embedding Configuration
    embedding_model: str = "bge-small-en"
    embedding_dimension: int = 384  # bge-small-en dimension
    
    # General Configuration
    chunk_overlap: int = 200
    max_chunk_size: int = 1000

class ResponseCache:
    """LRU cache for LLM responses to improve performance"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        self.lock = threading.Lock()
    
    def _generate_key(self, prompt: str, model: str, max_tokens: int, temperature: float) -> str:
        """Generate cache key from request parameters"""
        key_data = f"{prompt}:{model}:{max_tokens}:{temperature}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, model: str, max_tokens: int, temperature: float) -> Optional[str]:
        """Get cached response if available"""
        key = self._generate_key(prompt, model, max_tokens, temperature)
        with self.lock:
            if key in self.cache:
                # Move to end of access order (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
        return None
    
    def put(self, prompt: str, model: str, max_tokens: int, temperature: float, response: str):
        """Cache a response"""
        key = self._generate_key(prompt, model, max_tokens, temperature)
        with self.lock:
            # Remove oldest entry if cache is full
            if len(self.cache) >= self.max_size and self.access_order:
                oldest_key = self.access_order.pop(0)
                del self.cache[oldest_key]
            
            self.cache[key] = response
            if key in self.access_order:
                self.access_order.remove(key)
            self.access_order.append(key)
    
    def clear(self):
        """Clear the cache"""
        with self.lock:
            self.cache.clear()
            self.access_order.clear()
    
    def size(self) -> int:
        """Get current cache size"""
        with self.lock:
            return len(self.cache)

class LocalLLMProvider:
    """Base class for local LLM providers with performance optimizations"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.model = None
        self.is_loaded = False
        self.cache = ResponseCache(config.cache_size) if config.cache_responses else None
        self.executor = ThreadPoolExecutor(max_workers=config.max_concurrent_requests)
        self.request_lock = threading.Lock()
    
    def load_model(self) -> bool:
        """Load the LLM model"""
        raise NotImplementedError
    
    def generate_response(self, prompt: str, context: str = "") -> str:
        """Generate response from the model"""
        raise NotImplementedError
    
    def generate_responses_batch(self, prompts: List[str]) -> List[str]:
        """Generate responses for multiple prompts in batch"""
        raise NotImplementedError
    
    def is_available(self) -> bool:
        """Check if the LLM provider is available"""
        raise NotImplementedError
    
    def cleanup(self):
        """Cleanup resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

class OllamaProvider(LocalLLMProvider):
    """Ollama provider for local models with performance optimizations"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        self.base_url = "http://localhost:11434"
        self.api_url = f"{self.base_url}/api"
        self.model_name = None
        self.session = requests.Session()
        # Configure session for better performance
        self.session.headers.update({'Content-Type': 'application/json'})
        adapter = HTTPAdapter(
            pool_connections=config.max_concurrent_requests,
            pool_maxsize=config.max_concurrent_requests
        )
        self.session.mount('http://', adapter)
        self.session.mount('https://', adapter)
    
    def is_available(self) -> bool:
        """Check if Ollama is available"""
        try:
            response = self.session.get(f"{self.api_url}/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False
    
    def load_model(self, model_name: str) -> bool:
        """Load Ollama model with performance optimizations"""
        try:
            # Check if model is available
            response = self.session.get(f"{self.api_url}/tags", timeout=10)
            if response.status_code != 200:
                return False
            
            available_models = response.json().get("models", [])
            model_ids = [model.get("name", "") for model in available_models]
            
            # Try to find the preferred model or a fallback
            preferred_models = [model_name, "phi3", "mistral", "llama2"]
            available_model = None
            
            for preferred in preferred_models:
                # Check exact match first
                if preferred in model_ids:
                    available_model = preferred
                    break
                # Check with :latest suffix
                elif f"{preferred}:latest" in model_ids:
                    available_model = f"{preferred}:latest"
                    break
                # Check without :latest suffix
                elif preferred.replace(":latest", "") in model_ids:
                    available_model = preferred.replace(":latest", "")
                    break
            
            if available_model:
                self.model_name = available_model
                logger.info(f"Ollama model {available_model} is available")
                
                # Configure model for optimal performance
                self._configure_model_performance()
                return True
            else:
                logger.warning(f"Preferred Ollama models not found. Available: {model_ids}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error("Failed to connect to Ollama server")
            return False
        except Exception as e:
            logger.error(f"Error loading Ollama model: {e}")
            return False
    
    def _configure_model_performance(self):
        """Configure Ollama model for optimal performance"""
        try:
            # Set model parameters for better performance
            config_payload = {
                "model": self.model_name,
                "options": {
                    "num_gpu": 1 if self.config.use_gpu else 0,
                    "num_thread": min(8, os.cpu_count() or 4),
                    "numa": True,  # Enable NUMA optimization
                    "f16_kv": True,  # Use half-precision for key/value cache
                    "rope_freq_base": 10000,
                    "rope_freq_scale": 0.5
                }
            }
            
            response = self.session.post(
                f"{self.api_url}/create",
                json=config_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                logger.info(f"Configured {self.model_name} for optimal performance")
            else:
                logger.warning(f"Could not configure model performance: {response.status_code}")
                
        except Exception as e:
            logger.warning(f"Error configuring model performance: {e}")
    
    def generate_response(self, prompt: str, context: str = "", max_tokens: Optional[int] = None) -> str:
        """Generate response using Ollama with caching and optimizations"""
        if not self.model_name:
            return "Error: No model loaded"
        
        # Check cache first
        if self.cache:
            cached_response = self.cache.get(
                prompt, 
                self.model_name, 
                max_tokens or self.config.llm_max_tokens,
                self.config.llm_temperature
            )
            if cached_response:
                logger.debug("Returning cached response")
                return cached_response
        
        try:
            # Combine prompt with context if provided
            full_prompt = prompt
            if context:
                full_prompt = f"Context: {context}\n\nQuestion: {prompt}"
            
            # Prepare the request with performance optimizations
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": self.config.enable_streaming,
                "options": {
                    "num_predict": max_tokens or self.config.llm_max_tokens,
                    "temperature": self.config.llm_temperature,
                    "top_p": self.config.llm_top_p,
                    "num_gpu": 1 if self.config.use_gpu else 0,
                    "num_thread": min(8, os.cpu_count() or 4)
                }
            }
            
            # Make the request with timeout
            start_time = time.time()
            response = self.session.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=self.config.request_timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                response_text = result.get("response", "")
                
                # Cache the response
                if self.cache:
                    self.cache.put(
                        prompt,
                        self.model_name,
                        max_tokens or self.config.llm_max_tokens,
                        self.config.llm_temperature,
                        response_text
                    )
                
                elapsed_time = time.time() - start_time
                logger.debug(f"Generated response in {elapsed_time:.2f}s")
                return response_text
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return f"Error: API returned status {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Error generating response with Ollama: {e}")
            return f"Error: {str(e)}"
        except Exception as e:
            logger.error(f"Unexpected error with Ollama: {e}")
            return f"Error: {str(e)}"
    
    def generate_responses_batch(self, prompts: List[str]) -> List[str]:
        """Generate responses for multiple prompts in parallel"""
        if not self.model_name:
            return ["Error: No model loaded"] * len(prompts)
        
        # Use ThreadPoolExecutor for parallel processing
        futures = []
        with self.executor as executor:
            for prompt in prompts:
                future = executor.submit(self.generate_response, prompt)
                futures.append(future)
            
            # Collect results
            responses = []
            for future in as_completed(futures):
                try:
                    response = future.result()
                    responses.append(response)
                except Exception as e:
                    logger.error(f"Error in batch generation: {e}")
                    responses.append(f"Error: {str(e)}")
        
        return responses

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
    """Manager for local LLM integration with enhanced model support and performance optimizations"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.providers = {}
        self.active_provider = None
        self.embedding_manager = EmbeddingManager(self.config)
        self.search_context = {}
        self.performance_stats = {
            "total_requests": 0,
            "cache_hits": 0,
            "average_response_time": 0.0,
            "total_response_time": 0.0
        }
        self.stats_lock = threading.Lock()
    
    def register_provider(self, name: str, provider: LocalLLMProvider):
        """Register an LLM provider"""
        self.providers[name] = provider
        logger.info(f"Registered LLM provider: {name}")
    
    def detect_providers(self) -> List[str]:
        """Detect available LLM providers"""
        available = []
        
        # Check Ollama with enhanced model support
        # Use llama2:latest as default since it's commonly available
        ollama_config = LLMConfig(
            llm_model="llama2:latest",
            embedding_model="bge-small-en",
            llm_max_tokens=2048,
            llm_temperature=0.7
        )
        ollama_provider = OllamaProvider(ollama_config)
        if ollama_provider.is_available():
            self.register_provider("ollama", ollama_provider)
            available.append("ollama")
        
        return available
    
    def set_active_provider(self, provider_name: str) -> bool:
        """Set the active LLM provider"""
        if provider_name in self.providers:
            self.active_provider = self.providers[provider_name]
            
            # Load the model for the active provider
            if hasattr(self.active_provider, 'load_model'):
                model_loaded = self.active_provider.load_model(self.config.llm_model)
                if model_loaded:
                    logger.info(f"Set active LLM provider: {provider_name} with model: {self.config.llm_model}")
                else:
                    logger.warning(f"Provider {provider_name} set but model loading failed")
            
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
    
    def update_performance_stats(self, response_time: float, cache_hit: bool = False):
        """Update performance statistics"""
        with self.stats_lock:
            self.performance_stats["total_requests"] += 1
            if cache_hit:
                self.performance_stats["cache_hits"] += 1
            self.performance_stats["total_response_time"] += response_time
            self.performance_stats["average_response_time"] = (
                self.performance_stats["total_response_time"] / 
                self.performance_stats["total_requests"]
            )
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get current performance statistics"""
        with self.stats_lock:
            stats = self.performance_stats.copy()
            if stats["total_requests"] > 0:
                stats["cache_hit_rate"] = stats["cache_hits"] / stats["total_requests"]
            else:
                stats["cache_hit_rate"] = 0.0
            return stats
    
    def clear_performance_stats(self):
        """Clear performance statistics"""
        with self.stats_lock:
            self.performance_stats = {
                "total_requests": 0,
                "cache_hits": 0,
                "average_response_time": 0.0,
                "total_response_time": 0.0
            }
    
    def enhance_search_results(self, query: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Enhance search results with LLM-generated insights with performance monitoring"""
        start_time = time.time()
        
        if not self.active_provider:
            available = self.detect_providers()
            if available:
                self.set_active_provider(available[0])
            else:
                response_time = time.time() - start_time
                self.update_performance_stats(response_time)
                return {
                    "enhanced": False,
                    "message": "No local LLM providers available",
                    "results": search_results,
                    "performance": {"response_time": response_time}
                }
        
        if not self.active_provider:
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
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
            
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            
            return {
                "enhanced": True,
                "query": query,
                "llm_response": enhanced_response,
                "results": search_results,
                "provider": type(self.active_provider).__name__,
                "llm_model": self.active_provider.config.llm_model,
                "embedding_model": self.config.embedding_model,
                "performance": {"response_time": response_time}
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            logger.error(f"Error enhancing search results: {e}")
            return {
                "enhanced": False,
                "message": f"Error enhancing results: {str(e)}",
                "results": search_results,
                "performance": {"response_time": response_time}
            }
    
    def answer_question(self, question: str, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Answer a specific question based on search results with performance monitoring"""
        start_time = time.time()
        
        if not self.active_provider:
            available = self.detect_providers()
            if available:
                self.set_active_provider(available[0])
            else:
                response_time = time.time() - start_time
                self.update_performance_stats(response_time)
                return {
                    "answered": False,
                    "message": "No local LLM providers available",
                    "answer": "I cannot answer this question as no local LLM is available.",
                    "performance": {"response_time": response_time}
                }
        
        if not self.active_provider:
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            return {
                "answered": False,
                "message": "No local LLM providers available",
                "answer": "I cannot answer this question as no local LLM is available.",
                "performance": {"response_time": response_time}
            }
        
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Generate answer
            answer = self.active_provider.generate_response(
                prompt=question,
                context=context
            )
            
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            
            return {
                "answered": True,
                "question": question,
                "answer": answer,
                "provider": type(self.active_provider).__name__,
                "llm_model": self.active_provider.config.llm_model,
                "embedding_model": self.config.embedding_model,
                "sources": [result.get('filepath', 'Unknown') for result in search_results],
                "performance": {"response_time": response_time}
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            logger.error(f"Error answering question: {e}")
            return {
                "answered": False,
                "message": f"Error answering question: {str(e)}",
                "answer": "I encountered an error while trying to answer your question.",
                "performance": {"response_time": response_time}
            }
    
    def generate_summary(self, search_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate a summary of search results with performance monitoring"""
        start_time = time.time()
        
        if not self.active_provider:
            available = self.detect_providers()
            if available:
                self.set_active_provider(available[0])
            else:
                response_time = time.time() - start_time
                self.update_performance_stats(response_time)
                return {
                    "summarized": False,
                    "message": "No local LLM providers available",
                    "summary": "Cannot generate summary as no local LLM is available.",
                    "performance": {"response_time": response_time}
                }
        
        if not self.active_provider:
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            return {
                "summarized": False,
                "message": "No local LLM providers available",
                "summary": "Cannot generate summary as no local LLM is available.",
                "performance": {"response_time": response_time}
            }
        
        try:
            # Prepare context from search results
            context = self._prepare_context(search_results)
            
            # Generate summary
            summary = self.active_provider.generate_response(
                prompt="Provide a concise summary of the key information found in these search results. Highlight the most important points and any patterns or insights.",
                context=context
            )
            
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            
            return {
                "summarized": True,
                "summary": summary,
                "provider": type(self.active_provider).__name__,
                "llm_model": self.active_provider.config.llm_model,
                "embedding_model": self.config.embedding_model,
                "result_count": len(search_results),
                "performance": {"response_time": response_time}
            }
            
        except Exception as e:
            response_time = time.time() - start_time
            self.update_performance_stats(response_time)
            logger.error(f"Error generating summary: {e}")
            return {
                "summarized": False,
                "message": f"Error generating summary: {str(e)}",
                "summary": "I encountered an error while trying to generate a summary.",
                "performance": {"response_time": response_time}
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
        """Get status of all LLM providers and models with performance statistics"""
        status = {
            "active_provider": type(self.active_provider).__name__ if self.active_provider else None,
            "available_providers": [],
            "detected_providers": self.detect_providers(),
            "embedding_model": self.get_embedding_model_info(),
            "llm_model": self.active_provider.config.llm_model if self.active_provider else None,
            "performance_stats": self.get_performance_stats(),
            "cache_info": {
                "enabled": self.config.cache_responses,
                "size": self.active_provider.cache.size() if self.active_provider and self.active_provider.cache else 0,
                "max_size": self.config.cache_size
            } if self.active_provider else None
        }
        
        for name, provider in self.providers.items():
            status["available_providers"].append({
                "name": name,
                "type": type(provider).__name__,
                "available": provider.is_available(),
                "loaded": provider.is_loaded,
                "llm_model": provider.config.llm_model,
                "config": {
                    "use_gpu": provider.config.use_gpu,
                    "max_concurrent_requests": provider.config.max_concurrent_requests,
                    "request_timeout": provider.config.request_timeout,
                    "cache_responses": provider.config.cache_responses
                }
            })
        
        return status

# Global LLM manager instance
llm_manager = LocalLLMManager()

def get_llm_manager() -> LocalLLMManager:
    """Get the global LLM manager instance"""
    return llm_manager 