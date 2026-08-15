"""LLM 实例工厂：DeepSeek / OpenAI / Ollama（均为 OpenAI 兼容协议，经 ChatOpenAI 接入）。"""
from langchain_openai import ChatOpenAI

from . import config


def create_llm(provider=None, temperature=0):
    provider = (provider or config.LLM_PROVIDER).strip().lower()

    if provider == "deepseek":
        if not config.DEEPSEEK_API_KEY:
            raise ValueError("未配置 DEEPSEEK_API_KEY，请复制 .env.example 为 .env 并填入密钥")
        return ChatOpenAI(
            model=config.DEEPSEEK_MODEL,
            api_key=config.DEEPSEEK_API_KEY,
            base_url=config.DEEPSEEK_BASE_URL,
            temperature=temperature,
        )

    if provider == "openai":
        if not config.OPENAI_API_KEY:
            raise ValueError("未配置 OPENAI_API_KEY")
        return ChatOpenAI(
            model=config.OPENAI_MODEL,
            api_key=config.OPENAI_API_KEY,
            temperature=temperature,
        )

    if provider == "ollama":
        # 本地免费：需先安装 Ollama 并 ollama pull qwen2.5:7b
        return ChatOpenAI(
            model=config.OLLAMA_MODEL,
            api_key="ollama",
            base_url=config.OLLAMA_BASE_URL,
            temperature=temperature,
        )

    raise ValueError(f"不支持的 LLM_PROVIDER: {provider}（可选 deepseek / openai / ollama）")
