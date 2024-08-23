from typing import Optional
from pydantic import BaseSettings
import os

class LLMProviderSettings(BaseSettings):
    temperature: float = 0.0
    max_tokens: Optional[int] = None
    max_retries: int = 3

class OpenAISettings(LLMProviderSettings):
    api_key: str
    default_model: str = "gpt-4o"

    class Config:
        env_prefix = 'OPENAI_'

class AnthropicSettings(LLMProviderSettings):
    api_key: str
    default_model: str = "claude-3-5-sonnet-20240620"
    max_tokens: int = 1024

    class Config:
        env_prefix = 'ANTHROPIC_'

class LlamaSettings(LLMProviderSettings):
    api_key: str = "key"  # required, but not used
    default_model: str = "llama3"
    base_url: str = "http://localhost:11434/v1"

    class Config:
        env_prefix = 'LLAMA_'

class Settings(BaseSettings):
    app_name: str = "GenAI Project Template"
    openai: OpenAISettings = OpenAISettings()
    anthropic: AnthropicSettings = AnthropicSettings()
    llama: LlamaSettings = LlamaSettings()

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'

def get_settings() -> Settings:
    return Settings()
