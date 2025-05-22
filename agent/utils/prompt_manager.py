import os
from pathlib import Path
import yaml
import re


class PromptLoader:
    def __init__(self):
        self.cache = {}
        self.base_path = Path(__file__).parent.parent.parent / "resources" / "prompts"

    def load_prompt(self, category, name):
        """加载指定的提示词模板"""
        cache_key = f"{category}/{name}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # 构建文件路径
        file_path = self.base_path / category / f"{name}.md"

        if not file_path.exists():
            raise FileNotFoundError(f"提示词文件未找到: {file_path}")

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取元数据
        metadata_match = re.search(r'^---+\s*$(.*?)^---+\s*$',
                                   content, re.DOTALL | re.MULTILINE)
        metadata = {}
        if metadata_match:
            metadata = yaml.safe_load(metadata_match.group(1))
            body_content = content[metadata_match.end():]
        else:
            body_content = content

        # 解析依赖项
        dependencies = metadata.get("dependencies", [])
        for dep in dependencies:
            dep_parts = dep.split("/")
            dep_content = self.load_prompt(dep_parts[0], dep_parts[1])
            body_content = dep_content + "\n" + body_content

        # 替换变量占位符
        processed_content = body_content.strip()

        # 缓存结果
        self.cache[cache_key] = processed_content
        return processed_content

    def get_config(self, category, name):
        """获取提示词配置"""
        file_path = self.base_path / category / f"{name}.md"

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取元数据
        metadata_match = re.search(r'^---+\s*$(.*?)^---+\s*$',
                                   content, re.DOTALL | re.MULTILINE)
        if metadata_match:
            metadata = yaml.safe_load(metadata_match.group(1))
        else:
            metadata = {}

        return {
            "temperature": float(metadata.get("temperature", 0.7)),
            "max_tokens": int(metadata.get("max_tokens", 1000)),
            "stop_sequences": ["/n"] if metadata.get("stop_newline") else [],
            "top_p": float(metadata.get("top_p", 1.0)),
            "presence_penalty": float(metadata.get("presence_penalty", 0)),
            "frequency_penalty": float(metadata.get("frequency_penalty", 0)),
            "best_of": int(metadata.get("best_of", 1)),
            "log_level": metadata.get("log_level", "INFO")
        }


class PromptManager:
    def __init__(self):
        self.loader = PromptLoader()
        self.default_language = os.getenv("DEFAULT_LANGUAGE", "en-US")
        self.log_level = os.getenv("PROMPT_LOG_LEVEL", "INFO")

    def get_prompt(self, category, name, variables=None):
        """获取并渲染提示词"""
        prompt = self.loader.load_prompt(category, name)

        # 应用变量替换
        if variables:
            prompt = prompt.format(**variables)

        # 处理多语言
        lang_suffix = os.getenv("PROMPT_LANG_SUFFIX", "_CN")
        if lang_suffix:
            prompt += self.loader.load_prompt(category, f"{name}{lang_suffix}")

        return prompt

    def get_config(self, category, name):
        """获取提示词配置"""
        return self.loader.get_config(category, name)

    def log_prompt(self, category, name, logger):
        """记录当前使用的提示词"""
        if self.log_level == "DEBUG":
            prompt = self.loader.load_prompt(category, name)
            logger.debug(f"使用提示词:\n{prompt}")
