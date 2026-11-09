#!/usr/bin/env python3
"""
金渐成历史观点分析 - Anthropic API版本
需要Claude API Key
"""

import argparse
import json
import sys
import subprocess
import os
from pathlib import Path

from jinjiancheng_grounding import (
    KNOWLEDGE_BASE, build_context, build_prompt, load_answer_policy,
    load_knowledge_base, parse_date, search_relevant_articles, supporting_sources,
)

# 检查是否设置了API Key
CLAUDE_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

if not CLAUDE_API_KEY:
    print("⚠️  需要设置 ANTHROPIC_API_KEY 环境变量")
    print("\n设置方法:")
    print("  export ANTHROPIC_API_KEY='your-api-key'")
    print("\n或在命令前添加:")
    print("  ANTHROPIC_API_KEY='your-key' python3 jinjiancheng_ai.py '你的问题'")
    sys.exit(1)

try:
    import anthropic
except ImportError:
    print("❌ 需要安装 anthropic 库")
    print("\n安装方法:")
    print("  pip3 install anthropic")
    sys.exit(1)

def ask_jinjiancheng(question, as_of=None):
    """依据原文、时点和适用条件分析问题。"""

    print("🔍 正在搜索知识库...")
    kb = load_knowledge_base()

    print("📚 分析相关文章...")
    articles = search_relevant_articles(question, kb, limit=3, as_of=as_of)

    if not articles and not supporting_sources(question, kb, as_of):
        return '在指定资料范围内没有找到足够依据，无法据此归因给金渐成。可以提供文章或换一个更具体的问题。'

    print(f"✅ 找到 {len(articles)} 篇相关文章")
    print("🤖 正在生成回答...")

    # 完整原文与核对摘录作为资料传入，行为要求放在 system 中。
    prompt = build_prompt(question, articles, kb, as_of)

    # 调用Claude API
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    try:
        message = client.messages.create(
            model=os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022"),
            system=load_answer_policy(),
            max_tokens=2000,
            temperature=0.3,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response = message.content[0].text

        # 引用由回答按实际支持的主张给出，不把所有检索结果自动列为论据。
        return response

    except Exception as e:
        return f"❌ API调用失败: {e}\n\n请检查：\n1. API Key是否正确\n2. 网络连接是否正常\n3. API配额是否充足"


def main():
    parser = argparse.ArgumentParser(description='依据金渐成历史文章，解释观点、条件与变化')
    parser.add_argument('question', nargs='+', help='需要分析的问题')
    parser.add_argument('--as-of', type=parse_date, help='只使用不晚于此日期发表的文章')
    args = parser.parse_args()
    question = ' '.join(args.question)
    print(f'\n❓ {question}\n')
    answer = ask_jinjiancheng(question, as_of=args.as_of)
    print('金渐成历史观点分析：\n')
    print(answer)


if __name__ == "__main__":
    main()
