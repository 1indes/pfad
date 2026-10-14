"""Small, standard-library-only setup and output helpers for the speech demos."""

import importlib.metadata
import json
import os
from pathlib import Path
import re
import shutil
import sys

OUTPUT = Path(__file__).resolve().parents[1] / 'out'
PACKAGES = {
    'whisper': ('faster-whisper', 'numpy', 'huggingface-hub'),
    'kokoro': ('kokoro', 'torch', 'misaki', 'numpy', 'soundfile', 'en-core-web-sm'),
}
MODELS = {
    'whisper': ('Systran/faster-whisper-base.en', ('config.json', 'model.bin', 'tokenizer.json', 'vocabulary.txt')),
    'kokoro': ('hexgrad/Kokoro-82M', ('config.json', 'kokoro-v1_0.pth', 'voices/af_heart.pt')),
}


def versions(kind, microphone=False):
    result = {}
    for package in PACKAGES[kind] + (('sounddevice',) if microphone else ()):
        try:
            result[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            result[package] = None
    return result


def require_dependencies(kind, microphone=False):
    if sys.version_info[:2] != (3, 12):
        raise RuntimeError('Use the separate Python 3.12 environment in README.md.')
    missing = [name for name, version in versions(kind, microphone).items() if version is None]
    if missing:
        raise RuntimeError('Missing packages: ' + ', '.join(missing) + '. Follow speech/README.md setup.')
    if kind == 'kokoro' and not has_espeak():
        raise RuntimeError('Install espeak-ng; on Windows configure PHONEMIZER_ESPEAK_LIBRARY. See README.md.')


def has_espeak():
    if shutil.which('espeak-ng') or os.environ.get('PHONEMIZER_ESPEAK_LIBRARY'):
        return True
    try:
        package = importlib.metadata.distribution('espeakng-loader')
    except importlib.metadata.PackageNotFoundError:
        return False
    filename = ('espeak-ng.dll' if sys.platform == 'win32' else
                'libespeak-ng.dylib' if sys.platform == 'darwin' else 'libespeak-ng.so')
    return (Path(package.locate_file('espeakng_loader/' + filename)).is_file()
            and Path(package.locate_file('espeakng_loader/espeak-ng-data')).is_dir())


def whisper_model():
    """Prefer the explicit local conversion, otherwise use the usual Hub cache."""
    converted = OUTPUT / 'models/faster-whisper-base.en'
    return str(converted) if (converted / 'model.bin').is_file() else 'base.en'


def whisper_compute_type(model, device):
    # CPU int8 caused repeated punctuation with our converted float16 checkpoint.
    # Keep local directories in float32 on CPU; standard Hub base.en uses int8.
    return 'float16' if device == 'cuda' else ('float32' if Path(model).is_dir() else 'int8')


def missing_model_files(repo_id, filenames):
    """Inspect Hugging Face's local main snapshot; never import or download a model."""
    default = Path(os.environ.get('XDG_CACHE_HOME', Path.home() / '.cache')) / 'huggingface'
    home = Path(os.environ.get('HF_HOME', default))
    cache = Path(os.environ.get('HF_HUB_CACHE', os.environ.get('HUGGINGFACE_HUB_CACHE', home / 'hub')))
    repo = cache / ('models--' + repo_id.replace('/', '--'))
    try:
        revision = (repo / 'refs/main').read_text().strip()
    except FileNotFoundError:
        return list(filenames)
    if not re.fullmatch(r'[0-9a-f]{40}', revision):
        return list(filenames)
    snapshot = repo / 'snapshots' / revision
    return [name for name in filenames if not (snapshot / name).is_file()]


def preflight(kind, microphone=False, model_path=None):
    print('Offline preflight: package metadata and cached filenames only; no model or microphone is opened.')
    for name, version in versions(kind, microphone).items():
        print(f'{name}: {version or "MISSING"}')
    ready = True
    try:
        require_dependencies(kind, microphone)
    except RuntimeError as error:
        print(f'MISSING setup: {error}')
        ready = False
    repo, files = MODELS[kind]
    selected = model_path or (whisper_model() if kind == 'whisper' else None)
    if selected and selected != 'base.en':
        repo = selected
        files = ('config.json', 'model.bin', 'tokenizer.json')
        missing = [name for name in files if not (Path(selected) / name).is_file()]
    else:
        missing = missing_model_files(repo, files)
    print(f'{repo}: ' + ('MISSING cache files: ' + ', '.join(missing) if missing else 'expected cache files present'))
    print('File presence does not verify model integrity, compatible libraries, audio devices or inference.')
    return ready and not missing


def configure_network(offline):
    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    if offline:
        os.environ['HF_HUB_OFFLINE'] = '1'
        os.environ['TRANSFORMERS_OFFLINE'] = '1'


def check_output(path, suffix):
    if path.suffix.lower() != suffix:
        raise ValueError(f'--out must end in {suffix}.')
    for target in (path, path.with_suffix('.json')):
        if target.exists() or target.is_symlink():
            raise FileExistsError(f'Refusing to overwrite {target}. Choose another --out name.')


def save_outputs(path, data, settings):
    """Exclusive creation protects existing files; failed writes remove only our new files."""
    encoded = (json.dumps(settings, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
    check_output(path, path.suffix)
    path.parent.mkdir(parents=True, exist_ok=True)
    created = []
    try:
        for target, content in ((path, data), (path.with_suffix('.json'), encoded)):
            with target.open('xb') as output:
                created.append(target)
                output.write(content)
    except BaseException:
        for target in created:
            target.unlink()
        raise
