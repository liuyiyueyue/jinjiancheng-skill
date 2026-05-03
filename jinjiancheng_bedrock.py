#!/usr/bin/env python3
"""
金渐成AI顾问 - AWS Bedrock版本
使用 AWS Bedrock 调用 Claude 模型
"""

import json
import sys
import os

# 检查boto3
try:
    import boto3
except ImportError:
    print("❌ 需要安装 boto3 库")
    print("\n安装方法:")
    print("  pip3 install boto3")
    sys.exit(1)

try:
    import jieba
except ImportError:
    print("❌ 需要安装 jieba 库")
    print("  pip3 install jieba")
    sys.exit(1)

KNOWLEDGE_BASE = "jinjiancheng_knowledge_base.json"

# Bedrock 配置
BEDROCK_REGION = os.environ.get('AWS_REGION', 'us-east-1')  # 默认 us-east-1
BEDROCK_MODEL_ID = 'anthropic.claude-3-5-sonnet-20241022-v2:0'  # Claude 3.5 Sonnet


def check_aws_credentials():
    """检查AWS凭证"""
    try:
        session = boto3.Session()
        credentials = session.get_credentials()

        if credentials is None:
            print("⚠️  未找到 AWS 凭证")
            print("\n配置方法:")
            print("\n方式1：使用 AWS CLI 配置")
            print("  aws configure")
            print("\n方式2：设置环境变量")
            print("  export AWS_ACCESS_KEY_ID='your-key'")
            print("  export AWS_SECRET_ACCESS_KEY='your-secret'")
            print("  export AWS_REGION='us-east-1'")
            print("\n方式3：使用 IAM Role（EC2/Lambda）")
            return False

        return True
    except Exception as e:
        print(f"❌ AWS 凭证检查失败: {e}")
        return False


def load_knowledge_base():
    """加载知识库"""
    with open(KNOWLEDGE_BASE, 'r', encoding='utf-8') as f:
        return json.load(f)


def search_relevant_articles(question, kb, limit=5):
    """搜索相关文章"""
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
    """构建上下文"""
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


def call_bedrock_claude(prompt, region=BEDROCK_REGION, model_id=BEDROCK_MODEL_ID):
    """调用 Bedrock Claude API"""

    try:
        # 创建 Bedrock Runtime 客户端
        bedrock = boto3.client(
            service_name='bedrock-runtime',
            region_name=region
        )

        # 构建请求体（Claude 3.5 格式）
        request_body = {
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "temperature": 0.7,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        }

        # 调用模型
        response = bedrock.invoke_model(
            modelId=model_id,
            body=json.dumps(request_body)
        )

        # 解析响应
        response_body = json.loads(response['body'].read())

        # Claude 3.5 响应格式
        if 'content' in response_body and len(response_body['content']) > 0:
            return response_body['content'][0]['text']
        else:
            return "❌ 模型响应格式错误"

    except boto3.exceptions.Boto3Error as e:
        return f"❌ Bedrock API 调用失败: {e}"
    except Exception as e:
        return f"❌ 错误: {e}"


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
    print(f"🤖 正在调用 Bedrock Claude (region: {BEDROCK_REGION})...")

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

    # 调用 Bedrock
    response = call_bedrock_claude(prompt)

    # 添加引用文章
    citations = "\n\n---\n💡 以上回答基于金渐成的历史文章\n📚 参考文章：\n"
    for i, result in enumerate(articles, 1):
        article = result['article']
        citations += f"  {i}. 《{article['title']}》({article['folder_name'][:10]})\n"

    citations += f"\n⚠️  投资有风险，决策需独立思考\n"
    citations += f"🔧 使用 AWS Bedrock (region: {BEDROCK_REGION})"

    return response + citations


def main():
    if len(sys.argv) < 2:
        print("="*60)
        print(" "*12 + "💬 金渐成AI投资顾问 (Bedrock版)")
        print("="*60)
        print("\n🎭 真正扮演金渐成，用他的语气回答投资问题")
        print("📚 基于375篇文章，77万字内容")
        print("☁️  使用 AWS Bedrock 调用 Claude")
        print("\n用法:")
        print("  python3 jinjiancheng_bedrock.py '你的问题'")
        print("\n示例:")
        print('  python3 jinjiancheng_bedrock.py "我有100万，想买房，你怎么看？"')
        print('  python3 jinjiancheng_bedrock.py "腾讯现在还能买吗？"')
        print("\n🔧 AWS 配置:")
        print("  1. 确保已配置 AWS 凭证 (aws configure)")
        print("  2. 确保有 Bedrock 访问权限")
        print("  3. 可选：设置 AWS_REGION 环境变量")
        print(f"     当前 region: {BEDROCK_REGION}")
        print(f"     当前模型: {BEDROCK_MODEL_ID}")
        print("\n💰 费用:")
        print("  Claude 3.5 Sonnet (Bedrock):")
        print("  - 输入: $3/1M tokens")
        print("  - 输出: $15/1M tokens")
        print("  - 约 ¥0.15/次")
        print("\n" + "="*60)
        sys.exit(1)

    # 检查 AWS 凭证
    if not check_aws_credentials():
        sys.exit(1)

    question = " ".join(sys.argv[1:])

    print("\n" + "="*60)
    print(" "*12 + "💬 金渐成AI投资顾问 (Bedrock版)")
    print("="*60)
    print(f"\n❓ 你的问题: {question}\n")
    print("="*60 + "\n")

    answer = ask_jinjiancheng(question)

    print("🗣️  金渐成:\n")
    print(answer)
    print("\n" + "="*60)


if __name__ == "__main__":
    main()
