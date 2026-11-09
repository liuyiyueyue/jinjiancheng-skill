# AWS Bedrock 版本使用说明

> 此文保留早期服务配置示例。当前项目定位、模型 ID 环境变量、历史时点查询和内容质量要求以 [README](README.md) 为准；下面的旧模型、定价、区域及控制台步骤不代表当前可用性。

## 🎯 为什么选择 Bedrock？

### Bedrock vs 直接调用 Anthropic API

| 特性 | Bedrock | Anthropic API |
|------|---------|---------------|
| **价格** | 同价（$3/$15 per 1M tokens） | 同价 |
| **可用区域** | 多个 AWS 区域 | 全球（但国内受限） | 
| **网络** | AWS 内网（稳定） | 公网（可能需要代理） |
| **计费** | AWS 账单统一管理 | 单独付费 |
| **权限管理** | IAM 精细控制 | API Key |
| **适合场景** | 已有 AWS 账号 | 独立使用 |

### 推荐使用 Bedrock 的情况

✅ **你已经有 AWS 账号**
✅ **需要在 EC2/Lambda 上运行**
✅ **需要 IAM 权限管理**
✅ **国内网络访问受限**（可以用 AWS 中国区）
✅ **想统一在 AWS 账单中管理费用**

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip3 install boto3 jieba
```

### 2. 配置 AWS 凭证

#### 方式 A：使用 AWS CLI（推荐）

```bash
# 安装 AWS CLI
brew install awscli  # macOS
# 或
pip3 install awscli

# 配置凭证
aws configure

# 输入：
# AWS Access Key ID: AKIA...
# AWS Secret Access Key: ...
# Default region name: us-east-1
# Default output format: json
```

#### 方式 B：环境变量

```bash
export AWS_ACCESS_KEY_ID='AKIA...'
export AWS_SECRET_ACCESS_KEY='...'
export AWS_REGION='us-east-1'
```

#### 方式 C：IAM Role（EC2/Lambda）

如果在 EC2 或 Lambda 上运行，直接使用 IAM Role，无需配置。

### 3. 启用 Bedrock 访问

在 AWS Console 中：

1. 进入 **Amazon Bedrock** 服务
2. 左侧菜单 → **Model access**
3. 点击 **Manage model access**
4. 勾选 **Anthropic - Claude 3.5 Sonnet**
5. 点击 **Save changes**

等待几分钟，状态变为 **Access granted**

### 4. 运行脚本

```bash
python3 jinjiancheng_bedrock.py "我有100万，想买房，你怎么看？"
```

---

## 🌍 可用区域

### Bedrock Claude 3.5 Sonnet 支持的区域

| 区域 | Region Code | 延迟（从国内） |
|------|-------------|--------------|
| 美国东部（弗吉尼亚） | `us-east-1` | ~180ms |
| 美国西部（俄勒冈） | `us-west-2` | ~150ms |
| 欧洲（法兰克福） | `eu-central-1` | ~250ms |
| 亚太（东京） | `ap-northeast-1` | ~80ms ⭐ |
| 亚太（新加坡） | `ap-southeast-1` | ~60ms ⭐⭐ |

**推荐**：国内用户选择 `ap-northeast-1`（东京）或 `ap-southeast-1`（新加坡）

### 修改区域

```bash
# 方式1：环境变量
export AWS_REGION='ap-northeast-1'

# 方式2：修改代码
# 编辑 jinjiancheng_bedrock.py
BEDROCK_REGION = 'ap-northeast-1'
```

---

## 💰 费用对比

### Bedrock 定价（2024年）

**Claude 3.5 Sonnet**
- 输入：$3.00 / 1M tokens
- 输出：$15.00 / 1M tokens

**单次查询费用**：
```
输入：~5000 tokens（文章 + prompt）
输出：~500 tokens（回答）

费用 = (5000 × $3 + 500 × $15) / 1,000,000
     = $0.015 + $0.0075
     ≈ $0.02-0.03 / 次
     ≈ ¥0.15 / 次
```

### 与其他方案对比

| 方案 | 单次费用 | 网络 | 延迟 |
|------|---------|------|------|
| **Bedrock** | ¥0.15 | AWS内网 | 低 |
| **Anthropic API** | ¥0.15 | 公网 | 中 |
| **Azure OpenAI** | ¥0.10 | Azure内网 | 中 |
| **本地模型** | ¥0 | 无需网络 | 低（需GPU） |

---

## 🔧 高级配置

### 1. 使用不同的模型

编辑 `jinjiancheng_bedrock.py`：

```python
# Claude 3.5 Sonnet（推荐，最新）
BEDROCK_MODEL_ID = 'anthropic.claude-3-5-sonnet-20241022-v2:0'

# Claude 3 Sonnet（便宜一半，质量略差）
# BEDROCK_MODEL_ID = 'anthropic.claude-3-sonnet-20240229-v1:0'

# Claude 3 Haiku（最便宜，速度快）
# BEDROCK_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'
```

**模型对比**：

| 模型 | 输入价格 | 输出价格 | 质量 | 速度 |
|------|---------|---------|------|------|
| Claude 3.5 Sonnet | $3 | $15 | ⭐⭐⭐⭐⭐ | 快 |
| Claude 3 Sonnet | $3 | $15 | ⭐⭐⭐⭐ | 快 |
| Claude 3 Haiku | $0.25 | $1.25 | ⭐⭐⭐ | 很快 |

### 2. 调整参数

```python
request_body = {
    "anthropic_version": "bedrock-2023-05-31",
    "max_tokens": 2000,        # 回答长度（1000-4096）
    "temperature": 0.7,         # 创造性（0-1）
    "top_p": 0.9,              # 可选：采样范围
    "top_k": 250,              # 可选：候选词数量
    "messages": [...]
}
```

**参数说明**：
- `temperature`: 
  - 0.3 = 更保守，更贴近原文
  - 0.7 = 平衡（推荐）
  - 1.0 = 更有创造性
- `max_tokens`: 回答最大长度
- `top_p`: 核采样参数

### 3. 流式输出（Streaming）

如果想看到逐字输出效果：

```python
response = bedrock.invoke_model_with_response_stream(
    modelId=model_id,
    body=json.dumps(request_body)
)

for event in response['body']:
    chunk = json.loads(event['chunk']['bytes'])
    if chunk['type'] == 'content_block_delta':
        print(chunk['delta']['text'], end='', flush=True)
```

---

## 🛡️ 安全最佳实践

### 1. 使用 IAM 角色（推荐）

而不是在代码中硬编码凭证：

```python
# ❌ 不要这样
AWS_ACCESS_KEY_ID = 'AKIA...'  # 写在代码里

# ✅ 应该这样
# 使用 IAM Role 或环境变量
session = boto3.Session()  # 自动读取凭证
```

### 2. 最小权限原则

创建专门的 IAM 用户，只授予 Bedrock 权限：

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "bedrock:InvokeModel"
      ],
      "Resource": "arn:aws:bedrock:*::foundation-model/anthropic.claude-3-5-sonnet-*"
    }
  ]
}
```

### 3. 启用 CloudWatch 日志

监控 API 调用和费用：

```bash
aws logs tail /aws/bedrock/modelinvocations --follow
```

---

## 🚨 常见问题

### Q1: `AccessDeniedException`

```
错误：An error occurred (AccessDeniedException) when calling the InvokeModel operation
```

**原因**：
1. 没有在 Bedrock Console 中启用模型访问
2. IAM 权限不足

**解决**：
1. 进入 AWS Console → Bedrock → Model access
2. 启用 Claude 3.5 Sonnet
3. 检查 IAM 权限

### Q2: 网络超时

```
错误：Read timeout on endpoint URL
```

**原因**：网络连接慢或不稳定

**解决**：
```python
# 增加超时时间
config = boto3.Config(
    connect_timeout=30,
    read_timeout=300
)

bedrock = boto3.client(
    'bedrock-runtime',
    region_name=region,
    config=config
)
```

### Q3: 费用过高

**省钱方案**：

1. **使用 Claude 3 Haiku**（便宜10倍）
   ```python
   BEDROCK_MODEL_ID = 'anthropic.claude-3-haiku-20240307-v1:0'
   ```

2. **减少上下文**
   ```python
   # 从3篇改成2篇
   articles = search_relevant_articles(question, kb, limit=2)
   
   # 截取更短的内容
   content = article['content'][:800] + "..."
   ```

3. **设置预算告警**
   ```bash
   aws budgets create-budget \
     --budget file://budget.json
   ```

### Q4: 国内网络访问

如果在国内：

**选项1：使用 AWS 中国区域**
- 需要在 AWS 中国区注册账号
- 支持的模型可能较少

**选项2：使用代理**
```bash
export HTTP_PROXY=http://your-proxy:port
export HTTPS_PROXY=http://your-proxy:port
```

**选项3：选择亚太区域**
```bash
export AWS_REGION='ap-northeast-1'  # 东京，延迟较低
```

---

## 📊 性能优化

### 1. 批量处理

如果有多个问题：

```python
questions = [
    "问题1",
    "问题2",
    "问题3"
]

# 批量调用（共享知识库加载）
kb = load_knowledge_base()  # 只加载一次

for q in questions:
    answer = ask_jinjiancheng_with_kb(q, kb)
    print(answer)
```

### 2. 缓存结果

对于重复问题：

```python
import hashlib
import pickle

def get_cached_answer(question):
    cache_key = hashlib.md5(question.encode()).hexdigest()
    cache_file = f"cache/{cache_key}.pkl"
    
    if os.path.exists(cache_file):
        with open(cache_file, 'rb') as f:
            return pickle.load(f)
    
    # 调用 API
    answer = ask_jinjiancheng(question)
    
    # 保存缓存
    with open(cache_file, 'wb') as f:
        pickle.dump(answer, f)
    
    return answer
```

### 3. 异步调用

如果需要处理大量请求：

```python
import asyncio
import aioboto3

async def ask_async(question):
    session = aioboto3.Session()
    async with session.client('bedrock-runtime') as bedrock:
        response = await bedrock.invoke_model(...)
        return response
```

---

## 🔄 迁移指南

### 从 Anthropic API 迁移到 Bedrock

只需要改几行代码：

**之前**（`jinjiancheng_ai.py`）：
```python
import anthropic

client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
message = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    messages=[{"role": "user", "content": prompt}]
)
answer = message.content[0].text
```

**之后**（`jinjiancheng_bedrock.py`）：
```python
import boto3

bedrock = boto3.client('bedrock-runtime', region_name='us-east-1')
response = bedrock.invoke_model(
    modelId='anthropic.claude-3-5-sonnet-20241022-v2:0',
    body=json.dumps({
        "messages": [{"role": "user", "content": prompt}]
    })
)
answer = json.loads(response['body'].read())['content'][0]['text']
```

---

## 🎯 最佳实践总结

1. ✅ **使用 IAM Role**，不要硬编码凭证
2. ✅ **选择就近区域**（亚太用户选 `ap-northeast-1`）
3. ✅ **启用 CloudWatch**，监控费用和性能
4. ✅ **设置预算告警**，避免意外高额账单
5. ✅ **缓存常见问题**，减少重复调用
6. ✅ **使用流式输出**，改善用户体验

---

## 🚀 开始使用

```bash
# 1. 配置 AWS
aws configure

# 2. 启用 Bedrock 模型访问（在 AWS Console）

# 3. 测试
python3 jinjiancheng_bedrock.py "测试问题"

# 4. 享受！
```

---

有问题随时问！Bedrock 版本和 Anthropic API 版本功能完全一样，只是底层调用方式不同。
