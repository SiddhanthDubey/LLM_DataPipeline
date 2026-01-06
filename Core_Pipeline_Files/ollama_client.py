"""
Ollama Client - Clean interface for Ollama API with session management
"""
import requests
import json
from datetime import datetime


class OllamaClient:
    """Simple, clean client for Ollama API with conversation memory"""
    
    def __init__(self, base_url="http://localhost:11434"):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama API base URL
        """
        self.base_url = base_url
        self.conversation_history = []
        self.model_name = None
        self.system_prompt = None
        self.temperature = 0.7
        self.max_tokens = 4000
        self.top_p = 0.9
    
    def set_model(self, model_config):
        """
        Configure the model for this session.
        
        Args:
            model_config: Dictionary with model configuration
        """
        self.model_name = model_config['name']
        self.system_prompt = model_config.get('system_prompt', '')
        self.temperature = model_config.get('temperature', 0.7)
        self.max_tokens = model_config.get('max_tokens', 4000)
        self.top_p = model_config.get('top_p', 0.9)
        
        # Initialize conversation with system prompt
        if self.system_prompt:
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
        else:
            self.conversation_history = []
    
    def chat(self, user_message):
        """
        Send a message and get response, maintaining conversation history.
        
        Args:
            user_message: User's message/prompt
        
        Returns:
            str: Model's response
        """
        if not self.model_name:
            raise ValueError("Model not set. Call set_model() first.")
        
        # Add user message to history
        self.conversation_history.append({
            "role": "user",
            "content": user_message
        })
        
        # Prepare request
        payload = {
            "model": self.model_name,
            "messages": self.conversation_history,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "num_predict": self.max_tokens,
                "top_p": self.top_p
            }
        }
        
        try:
            # Make API call
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=300  # 5 minute timeout
            )
            response.raise_for_status()
            
            # Parse response
            result = response.json()
            assistant_message = result['message']['content']
            
            # Add assistant response to history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return assistant_message
            
        except requests.exceptions.ConnectionError:
            raise ConnectionError(
                "Cannot connect to Ollama. Make sure Ollama is running:\n"
                "Run: ollama serve"
            )
        except requests.exceptions.Timeout:
            raise TimeoutError(
                "Ollama request timed out. The model might be too slow or stuck."
            )
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise ValueError(
                    f"Model '{self.model_name}' not found.\n"
                    f"Run: ollama pull {self.model_name}"
                )
            else:
                raise RuntimeError(f"Ollama API error: {e}")
    
    def get_conversation_history(self):
        """Get the full conversation history"""
        return self.conversation_history.copy()
    
    def get_conversation_summary(self):
        """Get a summary of the conversation for logging"""
        return {
            'model': self.model_name,
            'temperature': self.temperature,
            'message_count': len(self.conversation_history),
            'messages': [
                {
                    'role': msg['role'],
                    'content_preview': msg['content'][:100] + '...' if len(msg['content']) > 100 else msg['content'],
                    'content_length': len(msg['content'])
                }
                for msg in self.conversation_history
            ]
        }
    
    def clear_history(self):
        """Clear conversation history (keeps system prompt if present)"""
        if self.system_prompt:
            self.conversation_history = [
                {"role": "system", "content": self.system_prompt}
            ]
        else:
            self.conversation_history = []
    
    def reset(self):
        """Completely reset the client"""
        self.conversation_history = []
        self.model_name = None
        self.system_prompt = None
        self.temperature = 0.7
        self.max_tokens = 4000
        self.top_p = 0.9
    
    def test_connection(self):
        """
        Test if Ollama is running and accessible.
        
        Returns:
            bool: True if Ollama is accessible
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            return True
        except:
            return False
    
    def list_available_models(self):
        """
        Get list of available models in Ollama.
        
        Returns:
            list: List of model names
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            response.raise_for_status()
            models = response.json().get('models', [])
            return [model['name'] for model in models]
        except:
            return []
    
    def get_status(self):
        """Get current client status"""
        return {
            'connected': self.test_connection(),
            'model': self.model_name,
            'conversation_length': len(self.conversation_history),
            'temperature': self.temperature,
            'available_models': self.list_available_models()
        }


if __name__ == "__main__":
    # Test the Ollama client
    print("Testing OllamaClient...")
    
    client = OllamaClient()
    
    # Test connection
    print("\n1. Testing connection...")
    if client.test_connection():
        print("   ✓ Connected to Ollama")
    else:
        print("   ✗ Cannot connect to Ollama")
        print("   Make sure Ollama is running: ollama serve")
        exit(1)
    
    # List available models
    print("\n2. Available models:")
    models = client.list_available_models()
    if models:
        for model in models:
            print(f"   - {model}")
    else:
        print("   No models found")
    
    # Test a simple chat
    print("\n3. Testing chat...")
    try:
        # Configure with a simple model config
        test_config = {
            'name': 'llama3.2:3b',
            'system_prompt': 'You are a helpful assistant.',
            'temperature': 0.7,
            'max_tokens': 100
        }
        
        client.set_model(test_config)
        response = client.chat("Say 'Hello' in one word")
        print(f"   Response: {response}")
        print("   ✓ Chat test successful")
    except Exception as e:
        print(f"   ✗ Chat test failed: {e}")
    
    print("\n✓ OllamaClient test complete!")