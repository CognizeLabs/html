# LLM Factory

The `LLM Factory` project is designed to simplify the creation of language model clients and facilitate generating completions from various providers, including OpenAI, Anthropic, and Llama. It uses `pydantic` for settings management and `instructor` for interacting with the APIs.

## Features

- **Supports Multiple LLM Providers**: Easily switch between OpenAI, Anthropic, and Llama.
- **Dynamic Configuration**: Configurations are loaded from environment variables using `pydantic`.
- **Completion Generation**: Generate responses and reasoning from a language model.

## Installation

1. **Clone the repository**:

    ```bash
    git clone https://github.com/yourusername/llm-factory.git
    cd llm-factory
    ```

2. **Install dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3. **Create a `.env` file** in the root directory with the following content:

    ```dotenv
    # OpenAI settings
    OPENAI_API_KEY=your_openai_api_key

    # Anthropic settings
    ANTHROPIC_API_KEY=your_anthropic_api_key

    # Llama settings (if needed)
    LLAMA_API_KEY=your_llama_api_key

    # General application settings
    APP_NAME=GenAI Project Template
    ```

    Replace `your_openai_api_key`, `your_anthropic_api_key`, and `your_llama_api_key` with your actual API keys.

## Usage

1. **Define your completion model**:

    Create a model class that extends `BaseModel` from `pydantic`. For example:

    ```python
    from pydantic import BaseModel, Field

    class CompletionModel(BaseModel):
        response: str = Field(description="Your response to the user.")
        reasoning: str = Field(description="Explain your reasoning for the response.")
    ```

2. **Generate completions**:

    Use the `LLMFactory` to interact with the language model:

    ```python
    from llm_factory import LLMFactory
    from your_model import CompletionModel

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "If it takes 2 hours to dry 1 shirt out in the sun, how long will it take to dry 5 shirts?"}
    ]

    llm = LLMFactory("openai")
    completion = llm.create_completion(
        response_model=CompletionModel,
        messages=messages,
    )

    print(f"Reasoning: {completion.reasoning}\n")
    print(f"Response: {completion.response}")
    ```

## Directory Structure

