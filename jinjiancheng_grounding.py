#!/usr/bin/env python3
"""共享原文检索、日期筛选和回答依据；直接运行仅查本地资料。"""

import argparse
import json
from datetime import date
from pathlib import Path


ROOT = Path(__file__).resolve().parent
KNOWLEDGE_BASE = ROOT / 'jinjiancheng_knowledge_base.json'
REFERENCES = ROOT / '.claude/skills/jinjiancheng/references'


def load_knowledge_base():
    with KNOWLEDGE_BASE.open(encoding='utf-8') as file:
        return json.load(file)


def load_sources():
    with (REFERENCES / 'sources.json').open(encoding='utf-8') as file:
        return json.load(file)['sources']


def load_answer_policy():
    return (REFERENCES / 'answer-policy.md').read_text(encoding='utf-8')


def parse_date(value):
    try:
        parsed = date.fromisoformat(value)
        if parsed.isoformat() != value:
            raise ValueError
    except ValueError:
        raise argparse.ArgumentTypeError('日期需为有效的 YYYY-MM-DD')
    return value


def search_relevant_articles(question, kb, limit=5, as_of=None):
    """保留关键词检索；命中只用于发现资料，不代表结论已获支持。"""
    import jieba

    stopwords = {'现在', '怎么', '如何', '是否', '什么', '应该', '可以',
                 '为什么', '是不是', '还是', '这个', '那个', '时候'}
    keywords = {word.lower() for word in jieba.cut(question)
                if len(word.strip()) > 1 and word not in stopwords}
    results = []
    for article in kb:
        if as_of and article['publish_time'] > as_of:
            continue
        content = article['content'].lower()
        title = article['title'].lower()
        score = sum(content.count(word) * 2 + (10 if word in title else 0)
                    for word in keywords)
        if score > 0:
            results.append({'article': article, 'score': score})
    results.sort(key=lambda result: result['score'], reverse=True)
    return results[:limit]


def supporting_sources(question, kb, as_of=None):
    """按主题补充已核对的观点变化与反例，不参与模型指令。"""
    by_folder = {article['folder_name']: article for article in kb}
    question = question.lower()
    selected = []
    for source in load_sources():
        if as_of and source['publish_time'] > as_of:
            continue
        if not any(topic.lower() in question for topic in source['topics']):
            continue
        article = by_folder.get(source['folder_name'])
        if article is None:
            continue
        if (source['publish_time'] != article['publish_time'] or
                source['title'] != article['title'] or
                source['file_path'] != article['file_path']):
            raise ValueError(f"来源元数据与知识库不一致：{source['id']}")
        if not all(excerpt in article['content'] for excerpt in source['excerpts']):
            raise ValueError(f"来源摘录与知识库不一致：{source['id']}")
        selected.append(source)
    return selected


def build_context(articles):
    """保留检索到的全文，避免匹配段落或反思被前1500字截断。"""
    return '\n\n'.join(
        f"《{item['article']['title']}》({item['article']['publish_time']})\n"
        f"{item['article']['content']}"
        for item in articles
    )


def build_prompt(question, articles, kb, as_of=None):
    """资料与系统规则分离；即使调用方传入未来文章，也在这里过滤。"""
    source_ids = {source['folder_name']: source['id'] for source in load_sources()}
    corpus_ids = {article['folder_name']: f'K{index:03d}'
                  for index, article in enumerate(kb, 1)}
    documents = []
    seen = set()
    for result in articles:
        article = result['article']
        if as_of and article['publish_time'] > as_of:
            continue
        folder = article['folder_name']
        if folder in seen:
            continue
        seen.add(folder)
        documents.append({
            'id': source_ids.get(folder, corpus_ids[folder]),
            'title': article['title'],
            'publish_time': article['publish_time'],
            'file_path': article['file_path'],
            'kind': '完整原文',
            'content': article['content'],
        })
    for source in supporting_sources(question, kb, as_of):
        if source['folder_name'] not in seen:
            documents.append({
                'id': source['id'],
                'title': source['title'],
                'publish_time': source['publish_time'],
                'file_path': source['file_path'],
                'kind': '原文摘录，各段不保证相邻；细节不足时不可补造',
                'excerpts': source['excerpts'],
            })
    eligible_dates = [article['publish_time'] for article in kb
                      if not as_of or article['publish_time'] <= as_of]
    return json.dumps({
        'question': question,
        'requested_as_of': as_of,
        'available_articles_through': max(eligible_dates, default=None),
        'coverage_note': '关键词检索加精选核对材料，不是完整主题检索；'
                         '交易、价格、收益和预测均为历史文章自述。',
        'sources': documents,
    }, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('question', nargs='*')
    parser.add_argument('--source', help='读取来源编号，如 S04')
    parser.add_argument('--full', action='store_true', help='与 --source 一起读取全文')
    parser.add_argument('--as-of', type=parse_date, help='只使用不晚于此日期发表的文章')
    parser.add_argument('--limit', type=int, default=3, help='额外关键词全文检索数量')
    args = parser.parse_args()
    if args.limit < 1:
        parser.error('--limit 必须大于0')
    kb = load_knowledge_base()
    if args.source:
        if args.question:
            parser.error('--source 与问题检索二选一')
        source = next((source for source in load_sources() if source['id'] == args.source), None)
        if source is None:
            parser.error('来源编号不存在')
        if args.as_of and source['publish_time'] > args.as_of:
            parser.error('该文章晚于指定历史时点')
        if args.full:
            source = dict(source)
            source['content'] = next(article['content'] for article in kb
                                     if article['folder_name'] == source['folder_name'])
        print(json.dumps(source, ensure_ascii=False, indent=2))
        return
    if args.full or not args.question:
        parser.error('请提供问题，或使用 --source S04 --full')
    question = ' '.join(args.question)
    articles = search_relevant_articles(question, kb, args.limit, args.as_of)
    print(build_prompt(question, articles, kb, args.as_of))


if __name__ == '__main__':
    main()
