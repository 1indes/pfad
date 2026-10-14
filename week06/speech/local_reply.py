"""Small, standard-library client for LM Studio's local chat server."""

import argparse
import json
import re
from urllib import request
from urllib.parse import urlparse

DEFAULT_URL = 'http://127.0.0.1:1234/v1'
SYSTEM = ('You are Pip, a curious, quick-witted studio companion for artists and designers. '
          'Be warm, playful and useful: offer concrete ideas, a surprising analogy when it fits, '
          'and occasional gentle humor. Do not force a joke into every reply. '
          'Reply in English, usually in three to five conversational sentences, around 60-90 words; '
          'simple questions can have shorter answers. Ask at most one natural follow-up question. '
          'Keep real-world suggestions practical. Use plain text that sounds good spoken aloud. '
          'Use words rather than emoji. Avoid markdown, lists and reasoning traces.')


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        raise ValueError('The local server redirected the request. Check its localhost URL.')


def server_url(base):
    parsed = urlparse(base)
    if (parsed.scheme != 'http' or parsed.hostname not in ('localhost', '127.0.0.1', '::1')
            or parsed.username or parsed.password or parsed.query or parsed.fragment):
        raise ValueError('Use a local HTTP server URL, such as http://127.0.0.1:1234/v1.')
    return base.rstrip('/')


def call(base, route, payload=None, timeout=90):
    url = server_url(base) + route
    data = None if payload is None else json.dumps(payload).encode('utf-8')
    req = request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    # Local requests should neither use an OS proxy nor follow a redirect elsewhere.
    opener = request.build_opener(request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=timeout) as response:
        body = response.read(65537)
    if len(body) > 65536:
        raise ValueError('The local server returned too much data.')
    return json.loads(body)


def list_models(base=DEFAULT_URL):
    models = call(base, '/models', timeout=5).get('data', [])
    if not isinstance(models, list):
        raise ValueError('The local server returned an invalid model list.')
    return [model['id'] for model in models if isinstance(model, dict)
            and isinstance(model.get('id'), str) and not model['id'].startswith('text-embedding-')]


def ask(checked_text, model, history=(), base=DEFAULT_URL, system_prompt=SYSTEM):
    text = checked_text.strip()
    if not text or len(text) > 500:
        raise ValueError('Keep the corrected transcript between 1 and 500 characters.')
    if not model.strip():
        raise ValueError('Select the model loaded in LM Studio first.')
    if not isinstance(system_prompt, str) or not system_prompt.strip() or len(system_prompt) > 2000:
        raise ValueError('Keep the assistant personality between 1 and 2000 characters.')
    messages = [{'role': 'system', 'content': system_prompt.strip()}]
    for message in list(history)[-8:]:
        if message.get('role') not in ('user', 'assistant') or not isinstance(message.get('content'), str):
            raise ValueError('Invalid conversation history.')
        messages.append({'role': message['role'], 'content': message['content'][:1000]})
    messages.append({'role': 'user', 'content': text})
    if 'minicpm5' in model.lower():
        # LM Studio ignores enable_thinking for this GGUF. The documented
        # assistant prefill skips thinking so the reply budget reaches an answer.
        messages.append({'role': 'assistant', 'content': '<think>\n\n</think>\n\n'})
    result = call(base, '/chat/completions', {
        'model': model, 'messages': messages, 'stream': False,
        'temperature': 0.7, 'max_tokens': 256,
    })
    answer = result['choices'][0]['message']['content']
    if not isinstance(answer, str) or not answer.strip():
        raise ValueError('The local model returned an empty reply.')
    answer = re.sub(r'<think>.*?</think>', '', answer, flags=re.DOTALL).strip()
    if not answer or '<think>' in answer:
        raise ValueError('The model did not finish a spoken answer. Check its reasoning settings.')
    return answer.strip()[:1000]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default=DEFAULT_URL)
    parser.add_argument('--model', help='Exact model identifier from --check')
    parser.add_argument('--text', help='Send one short text prompt to the local model')
    parser.add_argument('--check', action='store_true', help='List models from the local server')
    args = parser.parse_args()
    try:
        if args.check:
            models = list_models(args.url)
            print('\n'.join(models) if models else 'No models available. Load a chat model in LM Studio.')
            return 0 if models else 1
        if not args.text or not args.model:
            parser.error('Use --check, or provide --model and --text.')
        print(ask(args.text, args.model, base=args.url))
        return 0
    except (OSError, ValueError, KeyError, IndexError, TypeError) as error:
        print(f'Local reply unavailable: {error}. Start LM Studio\'s local server and load a model.')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
