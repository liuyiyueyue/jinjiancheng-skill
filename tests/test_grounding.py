import contextlib
import io
import json
import os
from pathlib import Path
import runpy
import subprocess
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import jinjiancheng_grounding as grounding


class GroundingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.kb = grounding.load_knowledge_base()
        cls.sources = grounding.load_sources()
        cls.by_folder = {article['folder_name']: article for article in cls.kb}
        cls.by_id = {source['id']: source for source in cls.sources}

    def article(self, source_id):
        return self.by_folder[self.by_id[source_id]['folder_name']]

    def test_all_curated_excerpts_and_metadata_match_originals(self):
        self.assertEqual(len(self.by_id), len(self.sources))
        for source in self.sources:
            with self.subTest(source=source['id']):
                article = self.by_folder[source['folder_name']]
                for field in ('title', 'publish_time', 'file_path'):
                    self.assertEqual(source[field], article[field])
                path = (grounding.ROOT / source['file_path']).resolve()
                self.assertTrue(path.is_relative_to(grounding.ROOT))
                self.assertTrue(path.is_file())
                self.assertTrue(source['excerpts'])
                for excerpt in source['excerpts']:
                    self.assertIn(excerpt, article['content'])

    def test_full_article_keeps_relevant_late_passages(self):
        article = self.article('S10')
        self.assertGreater(len(article['content']), 1500)
        items = [{'article': article, 'score': 1}]
        self.assertIn(article['content'], grounding.build_context(items))
        prompt = json.loads(grounding.build_prompt('估值', items, self.kb))
        document = next(doc for doc in prompt['sources'] if doc['id'] == 'S10')
        self.assertEqual(document['content'], article['content'])

    def test_historical_cutoff_applies_to_search_and_curated_evidence(self):
        items = grounding.search_relevant_articles('中国平安 茅台', self.kb, as_of='2022-12-31')
        self.assertTrue(items)
        self.assertTrue(all(item['article']['publish_time'] <= '2022-12-31' for item in items))
        prompt = json.loads(grounding.build_prompt('中国平安 茅台', items, self.kb, '2022-12-31'))
        ids = {doc['id'] for doc in prompt['sources']}
        self.assertIn('S01', ids)
        self.assertNotIn('S04', ids)
        self.assertNotIn('S08', ids)
        self.assertTrue(all(doc['publish_time'] <= '2022-12-31' for doc in prompt['sources']))
        self.assertLessEqual(prompt['available_articles_through'], '2022-12-31')

    def test_future_article_supplied_by_caller_is_still_filtered(self):
        items = [{'article': self.article('S08'), 'score': 100}]
        prompt = json.loads(grounding.build_prompt('茅台', items, self.kb, '2023-12-31'))
        self.assertNotIn('S08', {doc['id'] for doc in prompt['sources']})
        self.assertNotIn('全部清仓走人', json.dumps(prompt, ensure_ascii=False))

    def test_before_corpus_start_has_no_evidence(self):
        prompt = json.loads(grounding.build_prompt('茅台 平安', [], self.kb, '2021-12-31'))
        self.assertEqual(prompt['sources'], [])
        self.assertIsNone(prompt['available_articles_through'])

    def test_evaluation_questions_can_reach_their_core_sources(self):
        cases = json.loads((grounding.REFERENCES / 'evaluation-cases.json').read_text())['cases']
        for case in cases:
            with self.subTest(case=case['id']):
                prompt = json.loads(grounding.build_prompt(case['question'], [], self.kb, case['as_of']))
                ids = {source['id'] for source in prompt['sources']}
                self.assertTrue(set(case['required_sources']) <= ids,
                                f"缺少核对材料：{set(case['required_sources']) - ids}")
                for source_id in case['required_sources']:
                    if case['as_of']:
                        self.assertLessEqual(self.by_id[source_id]['publish_time'], case['as_of'])

    def test_failure_and_conditions_accompany_averaging_down(self):
        prompt = json.loads(grounding.build_prompt('龙头越跌越买就行吗？', [], self.kb))
        ids = {source['id'] for source in prompt['sources']}
        self.assertTrue({'S05', 'S09', 'S10', 'S13'} <= ids)

    def test_retrieved_full_source_is_not_duplicated_as_excerpt(self):
        article = self.article('S04')
        prompt = json.loads(grounding.build_prompt('中国平安', [{'article': article}], self.kb))
        documents = [doc for doc in prompt['sources'] if doc['id'] == 'S04']
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]['content'], article['content'])

    def test_mismatched_excerpt_is_rejected(self):
        source = dict(self.by_id['S04'], excerpts=['不存在于原文的杜撰引语'])
        with patch.object(grounding, 'load_sources', return_value=[source]):
            with self.assertRaisesRegex(ValueError, 'S04'):
                grounding.supporting_sources('中国平安', self.kb)

    def test_source_reader_works_from_another_directory_and_respects_cutoff(self):
        with tempfile.TemporaryDirectory() as directory:
            command = [sys.executable, str(grounding.ROOT / 'jinjiancheng_grounding.py'),
                       '--source', 'S04', '--full']
            result = subprocess.run(command, cwd=directory, text=True, capture_output=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(json.loads(result.stdout)['content'], self.article('S04')['content'])
            blocked = subprocess.run(command + ['--as-of', '2022-12-31'], cwd=directory,
                                     text=True, capture_output=True)
            self.assertNotEqual(blocked.returncode, 0)
            self.assertEqual(blocked.stdout, '')

    def test_invalid_calendar_date_rejected(self):
        result = subprocess.run(
            [sys.executable, str(grounding.ROOT / 'jinjiancheng_grounding.py'),
             '--source', 'S04', '--as-of', '2023-02-29'],
            text=True, capture_output=True,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, '')

    def test_both_providers_receive_same_policy_and_historical_evidence(self):
        calls = {}
        anthropic = ModuleType('anthropic')
        boto3 = ModuleType('boto3')

        def create(**kwargs):
            calls['anthropic'] = kwargs
            return SimpleNamespace(content=[SimpleNamespace(text='模拟回答')])

        anthropic.Anthropic = lambda **kwargs: SimpleNamespace(messages=SimpleNamespace(create=create))

        def invoke_model(**kwargs):
            calls['bedrock'] = kwargs
            body = json.dumps({'content': [{'type': 'text', 'text': '模拟回答'}]}).encode()
            return {'body': io.BytesIO(body)}

        boto3.client = lambda **kwargs: SimpleNamespace(invoke_model=invoke_model)
        boto3.exceptions = SimpleNamespace(Boto3Error=Exception)
        with patch.dict(sys.modules, {'anthropic': anthropic, 'boto3': boto3}), \
             patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'offline-test-placeholder',
                                     'ANTHROPIC_MODEL': 'test-anthropic-model',
                                     'BEDROCK_MODEL_ID': 'test-bedrock-model'}), \
             contextlib.redirect_stdout(io.StringIO()):
            direct = runpy.run_path(str(grounding.ROOT / 'jinjiancheng_ai.py'))
            bedrock = runpy.run_path(str(grounding.ROOT / 'jinjiancheng_bedrock.py'))
            for entrypoint in (direct, bedrock):
                self.assertEqual(entrypoint['ask_jinjiancheng']('中国平安', as_of='2022-12-31'), '模拟回答')

        direct_request = calls['anthropic']
        bedrock_request = json.loads(calls['bedrock']['body'])
        self.assertEqual(direct_request['system'], grounding.load_answer_policy())
        self.assertEqual(direct_request['system'], bedrock_request['system'])
        self.assertEqual(direct_request['messages'], bedrock_request['messages'])
        self.assertEqual(direct_request['model'], 'test-anthropic-model')
        self.assertEqual(calls['bedrock']['modelId'], 'test-bedrock-model')
        evidence = json.loads(direct_request['messages'][0]['content'])
        self.assertTrue(evidence['sources'])
        self.assertTrue(all(doc['publish_time'] <= '2022-12-31' for doc in evidence['sources']))
        self.assertNotIn('offline-test-placeholder', direct_request['messages'][0]['content'])


if __name__ == '__main__':
    unittest.main()
