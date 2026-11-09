#!/usr/bin/env python3
"""
金渐成AI顾问 - AWS Bedrock版本
使用 AWS Bedrock 调用 Claude 模型
"""

import argparse
import json
import sys
import os

from jinjiancheng_grounding import (
    KNOWLEDGE_BASE, build_context, build_prompt, load_answer_policy,
    load_knowledge_base, parse_date, search_relevant_articles, supporting_sources,
)

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

# Bedrock 配置
BEDROCK_REGION = os.environ.get('AWS_REGION', 'us-east-1')  # 默认 us-east-1
BEDROCK_MODEL_ID = os.environ.get('BEDROCK_MODEL_ID', 'anthropic.claude-3-5-sonnet-20241022-v2:0')


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
            "temperature": 0.3,
            "system": load_answer_policy(),
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


def ask_jinjiancheng(question, as_of=None):
    """依据原文、时点和适用条件分析问题。"""

    print("🔍 正在搜索知识库...")
    kb = load_knowledge_base()

    print("📚 分析相关文章...")
    articles = search_relevant_articles(question, kb, limit=3, as_of=as_of)

    if not articles and not supporting_sources(question, kb, as_of):
        return '在指定资料范围内没有找到足够依据，无法据此归因给金渐成。可以提供文章或换一个更具体的问题。'

    print(f"✅ 找到 {len(articles)} 篇相关文章")
    print(f"🤖 正在调用 Bedrock Claude (region: {BEDROCK_REGION})...")

    # 完整原文与核对摘录作为资料传入，行为要求放在 system 中。
    prompt = build_prompt(question, articles, kb, as_of)

    # 调用 Bedrock
    response = call_bedrock_claude(prompt)

    # 引用由回答按实际支持的主张给出。
    return response



def main():
    parser = argparse.ArgumentParser(description='依据金渐成历史文章，解释观点、条件与变化')
    parser.add_argument('question', nargs='+', help='需要分析的问题')
    parser.add_argument('--as-of', type=parse_date, help='只使用不晚于此日期发表的文章')
    args = parser.parse_args()
    if not check_aws_credentials():
        sys.exit(1)
    question = ' '.join(args.question)
    print(f'\n❓ {question}\n')
    answer = ask_jinjiancheng(question, as_of=args.as_of)
    print('金渐成历史观点分析：\n')
    print(answer)


if __name__ == "__main__":
    main()
