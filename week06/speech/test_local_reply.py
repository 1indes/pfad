"""Offline checks for the local chat boundary; no real server or model required."""

import unittest
from unittest.mock import patch

import local_reply


class LocalReplyTests(unittest.TestCase):
    def test_remote_urls_are_rejected(self):
        for url in ('https://example.com/v1', 'http://192.168.0.1/v1',
                    'http://user:pass@localhost/v1', 'http://localhost/v1?key=value'):
            with self.subTest(url=url), self.assertRaises(ValueError):
                local_reply.server_url(url)

    def test_model_discovery_preserves_the_server_identifier(self):
        with patch.object(local_reply, 'call', return_value={'data': [{'id': 'gemma-3-1b-it'}, {'id': 'another-model'}]}):
            self.assertEqual(local_reply.list_models(), ['gemma-3-1b-it', 'another-model'])

    def test_conversation_is_bounded_and_latest_turn_is_sent_once(self):
        history = [{'role': 'user' if i % 2 == 0 else 'assistant', 'content': str(i)} for i in range(20)]
        with patch.object(local_reply, 'call', return_value={'choices': [{'message': {'content': ' Hello. '}}]}) as call:
            self.assertEqual(local_reply.ask(' How are you? ', 'gemma', history), 'Hello.')
        payload = call.call_args.args[2]
        self.assertEqual(len(payload['messages']), 10)
        self.assertEqual(payload['messages'][1]['content'], '12')
        self.assertEqual(payload['messages'][-1], {'role': 'user', 'content': 'How are you?'})

    def test_empty_or_invalid_reply_is_reported(self):
        for content in ('', '   ', None, []):
            with self.subTest(content=content), patch.object(local_reply, 'call', return_value={'choices': [{'message': {'content': content}}]}):
                with self.assertRaises(ValueError):
                    local_reply.ask('Hello.', 'gemma')

    def test_minicpm_prefill_and_custom_personality(self):
        with patch.object(local_reply, 'call', return_value={'choices': [{'message': {'content': 'Hello.'}}]}) as call:
            local_reply.ask('Hello', 'minicpm5-2b', system_prompt='Be playful.')
        payload = call.call_args.args[2]
        self.assertEqual(payload['messages'][0]['content'], 'Be playful.')
        self.assertEqual(payload['messages'][-2], {'role': 'user', 'content': 'Hello'})
        self.assertEqual(payload['messages'][-1]['content'], '<think>\n\n</think>\n\n')
        self.assertEqual(payload['max_tokens'], 256)

    def test_reasoning_is_not_spoken(self):
        with patch.object(local_reply, 'call', return_value={'choices': [{'message': {'content': '<think>hidden</think> Hello.'}}]}):
            self.assertEqual(local_reply.ask('Hi', 'model'), 'Hello.')

    def test_invalid_input_never_contacts_server(self):
        with patch.object(local_reply, 'call') as call:
            for text, model in [('', 'gemma'), ('a' * 501, 'gemma'), ('Hello.', '')]:
                with self.subTest(text=text, model=model), self.assertRaises(ValueError):
                    local_reply.ask(text, model)
        call.assert_not_called()


if __name__ == '__main__':
    unittest.main()
