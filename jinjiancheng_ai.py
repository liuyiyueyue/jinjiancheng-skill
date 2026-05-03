#!/usr/bin/env python3
"""
金渐成AI顾问 - 真正扮演金渐成的角色
需要Claude API Key
"""

import json
import sys
import subprocess
import os
from pathlib import Path

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

KNOWLEDGE_BASE = "jinjiancheng_knowledge_base.json"

def load_knowledge_base():
    """加载知识库"""
    with open(KNOWLEDGE_BASE, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_relevant_articles(question, kb, limit=5):
    """搜索相关文章（简化版）"""
    import jieba

    # 分词
    keywords = [w for w in jieba.cut(question) if len(w) > 1]

    results = []
    for article in kb:
        score = 0
        for keyword in keywords:
            score += article['content'].lower().count(keyword.lower()) * 2
            if keyword in article['title']:
                score += 10

        if score > 0:
            results.append({
                'article': article,
                'score': score
            })

    results.sort(key=lambda x: x['score'], reverse=True)
    return results[:limit]


def build_context(articles):
    """构建上下文（文章内容）"""
    context_parts = []

    for i, result in enumerate(articles, 1):
        article = result['article']
        # 截取文章内容（避免太长）
        content = article['content'][:1500] + "..." if len(article['content']) > 1500 else article['content']

        context_parts.append(f"""
【文章{i}】{article['title']} ({article['folder_name'][:10]})

{content}

---
""")

    return "\n".join(context_parts)


def ask_jinjiancheng(question):
    """扮演金渐成回答问题"""

    print("🔍 正在搜索知识库...")
    kb = load_knowledge_base()

    print("📚 分析相关文章...")
    articles = search_relevant_articles(question, kb, limit=3)

    if not articles:
        return """
我翻了翻我写过的文章，好像没怎么写过这个话题。

要么你换个问法，要么这个问题不在我的知识范围内。
我主要写房地产、港股美股、投资理念这些，
如果你问的是别的领域，我确实帮不上忙。

或者，你可以直接去看看我的文章，说不定能找到答案。
"""

    print(f"✅ 找到 {len(articles)} 篇相关文章")
    print("🤖 正在生成回答...")

    # 构建上下文
    context = build_context(articles)

    # 构建prompt
    prompt = f"""你现在是金渐成，一位投资者和公众号作者。

你的性格特征：
- 直言不讳，说话直接
- 敢于质疑主流观点
- 强调风险控制和现金流
- 反对追涨杀跌行为
- 鼓励独立思考

你的说话风格：
- 有时用"~"结尾表示轻松语气
- 对韭菜行为毫不客气："这帮人又跑来问..."
- 常说："结合自己的情况"
- 常说："做自己的女娲"（独立思考）
- 用"停停停"来打断错误认知

用户问题：{question}

你之前写过的相关文章：
{context}

请用金渐成的语气和风格回答这个问题：
1. 如果用户的想法有问题，直接指出来
2. 基于你文章里的观点和案例
3. 给出具体的、可操作的建议
4. 强调风险控制
5. 保持你一贯的直接和犀利

不要只是复述文章内容，要像你平时在公众号里回答读者那样。"""

    # 调用Claude API
    client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)

    try:
        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=2000,
            temperature=0.7,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response = message.content[0].text

        # 添加引用文章
        citations = "\n\n---\n💡 以上回答基于金渐成的历史文章\n📚 参考文章：\n"
        for i, result in enumerate(articles, 1):
            article = result['article']
            citations += f"  {i}. 《{article['title']}》({article['folder_name'][:10]})\n"

        citations += "\n⚠️  投资有风险，决策需独立思考"

        return response + citations

    except Exception as e:
        return f"❌ API调用失败: {e}\n\n请检查：\n1. API Key是否正确\n2. 网络连接是否正常\n3. API配额是否充足"


def main():
    if len(sys.argv) < 2:
        print("="*60)
        print(" "*15 + "💬 金渐成AI投资顾问")
        print("="*60)
        print("\n🎭 真正扮演金渐成，用他的语气回答投资问题")
        print("📚 基于375篇文章，77万字内容")
        print("🤖 使用Claude AI进行推理和生成")
        print("\n用法:")
        print("  python3 jinjiancheng_ai.py '你的问题'")
        print("\n示例:")
        print('  python3 jinjiancheng_ai.py "我有100万，想买房，你怎么看？"')
        print('  python3 jinjiancheng_ai.py "腾讯现在还能买吗？"')
        print('  python3 jinjiancheng_ai.py "新手该怎么开始投资？"')
        print("\n💳 需要Claude API Key:")
        print("  export ANTHROPIC_API_KEY='your-api-key'")
        print("\n" + "="*60)
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    print("\n" + "="*60)
    print(" "*15 + "💬 金渐成AI投资顾问")
    print("="*60)
    print(f"\n❓ 你的问题: {question}\n")
    print("="*60 + "\n")

    answer = ask_jinjiancheng(question)

    print("🗣️  金渐成:\n")
    print(answer)
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
