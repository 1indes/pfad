"""Prepare local speech weights, reusing a cached OpenAI base.en checkpoint when available."""

import argparse
import hashlib
import json
from pathlib import Path
import shutil
import tempfile
from urllib import request

import common


def convert_whisper(checkpoint, destination, cache):
    if destination.exists():
        required = ('config.json', 'model.bin', 'tokenizer.json')
        if all((destination / name).is_file() for name in required):
            print(f'Reusing converted Whisper: {destination}', flush=True)
            return
        raise FileExistsError(f'Incomplete model directory: {destination}. Choose a new --whisper-out.')
    import torch
    from transformers import WhisperConfig, WhisperForConditionalGeneration
    from ctranslate2.converters import TransformersConverter
    from huggingface_hub import hf_hub_download
    saved = torch.load(checkpoint, map_location='cpu', weights_only=True)
    dims = saved['dims']
    if dims['n_vocab'] != 51864 or dims['n_audio_layer'] != 6:
        raise ValueError('This conversion expects the English base.en checkpoint.')
    config = WhisperConfig(
        vocab_size=dims['n_vocab'], num_mel_bins=dims['n_mels'], d_model=dims['n_audio_state'],
        encoder_layers=dims['n_audio_layer'], encoder_attention_heads=dims['n_audio_head'],
        decoder_layers=dims['n_text_layer'], decoder_attention_heads=dims['n_text_head'],
        encoder_ffn_dim=4 * dims['n_audio_state'], decoder_ffn_dim=4 * dims['n_text_state'],
        max_source_positions=dims['n_audio_ctx'], max_target_positions=dims['n_text_ctx'],
        bos_token_id=50257, eos_token_id=50256, pad_token_id=50256, decoder_start_token_id=50257,
    )
    state = {}
    substitutions = (
        ('blocks.', 'layers.'), ('cross_attn_ln.', 'encoder_attn_layer_norm.'),
        ('cross_attn.', 'encoder_attn.'), ('attn_ln.', 'self_attn_layer_norm.'),
        ('attn.', 'self_attn.'), ('mlp_ln.', 'final_layer_norm.'),
        ('mlp.0.', 'fc1.'), ('mlp.2.', 'fc2.'), ('query.', 'q_proj.'),
        ('key.', 'k_proj.'), ('value.', 'v_proj.'), ('out.', 'out_proj.'),
        ('ln_post.', 'layer_norm.'), ('decoder.ln.', 'decoder.layer_norm.'),
        ('token_embedding.', 'embed_tokens.'), ('positional_embedding', 'embed_positions.weight'),
    )
    for name, value in saved['model_state_dict'].items():
        # Replace cross-attention separately so its name does not become encoder_self_attn.
        name = name.replace('cross_attn_ln.', 'encoder_attention_layer_norm.').replace('cross_attn.', 'encoder_attention.')
        for old, new in substitutions:
            name = name.replace(old, new)
        name = name.replace('encoder_attention_layer_norm.', 'encoder_attn_layer_norm.').replace('encoder_attention.', 'encoder_attn.')
        state[name] = value
    model = WhisperForConditionalGeneration(config)
    model.model.load_state_dict(state, strict=True)
    model.tie_weights()
    resources = {}
    for filename in ('tokenizer.json', 'vocabulary.txt'):
        resources[filename] = hf_hub_download(common.MODELS['whisper'][0], filename, cache_dir=str(cache))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='whisper-conversion-', dir=destination.parent) as temporary:
        intermediate = Path(temporary)
        model.save_pretrained(intermediate)
        for filename, source in resources.items():
            shutil.copyfile(source, intermediate / filename)
        TransformersConverter(str(intermediate), copy_files=['tokenizer.json', 'vocabulary.txt']).convert(
            str(destination), quantization='float16')
    config_file = hf_hub_download(common.MODELS['whisper'][0], 'config.json', cache_dir=str(cache))
    shutil.copyfile(config_file, destination / 'config.json')
    print(f'Converted existing weights to float16 (CPU or CUDA): {destination}', flush=True)


def prepare_onnx(destination):
    api = 'https://api.github.com/repos/thewh1teagle/kokoro-onnx/releases/tags/model-files-v1.0'
    with request.urlopen(request.Request(api, headers={'User-Agent': 'PFAD-speech-setup'}), timeout=30) as response:
        assets = {asset['name']: asset for asset in json.load(response)['assets']}
    destination.mkdir(parents=True, exist_ok=True)
    for name in ('kokoro-v1.0.onnx', 'voices-v1.0.bin'):
        asset = assets[name]
        target = destination / name
        digest = asset.get('digest')
        if target.exists():
            if target.stat().st_size != asset['size']:
                raise ValueError(f'Incomplete existing file: {target}. Choose another --onnx-out.')
            if digest and hashlib.sha256(target.read_bytes()).hexdigest() != digest.removeprefix('sha256:'):
                raise ValueError(f'Checksum mismatch: {target}.')
            print(f'Reusing {target}', flush=True)
            continue
        print(f'Downloading missing {name} ({asset["size"] / 1024**2:.1f} MiB)', flush=True)
        partial = target.with_suffix(target.suffix + '.partial')
        with partial.open('xb') as output:
            with request.urlopen(asset['browser_download_url'], timeout=120) as response:
                shutil.copyfileobj(response, output)
        if partial.stat().st_size != asset['size']:
            raise ValueError(f'Download size mismatch: {partial}.')
        if digest and hashlib.sha256(partial.read_bytes()).hexdigest() != digest.removeprefix('sha256:'):
            raise ValueError(f'Download checksum mismatch: {partial}.')
        partial.rename(target)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache-dir', type=Path, default=common.OUTPUT / 'huggingface/hub')
    parser.add_argument('--whisper-checkpoint', type=Path, default=Path.home() / '.cache/whisper/base.en.pt')
    parser.add_argument('--whisper-out', type=Path, default=common.OUTPUT / 'models/faster-whisper-base.en')
    parser.add_argument('--onnx-out', type=Path, default=common.OUTPUT / 'models/kokoro-onnx')
    parser.add_argument('--backend', choices=('onnx', 'torch', 'both'), default='onnx')
    args = parser.parse_args()
    from huggingface_hub import snapshot_download
    common.configure_network(False)
    if (args.whisper_out / 'model.bin').is_file():
        required = ('config.json', 'model.bin', 'tokenizer.json')
        if not all((args.whisper_out / name).is_file() for name in required):
            raise ValueError(f'Incomplete Whisper model: {args.whisper_out}')
        print(f'Reusing local Whisper: {args.whisper_out}', flush=True)
    elif args.whisper_checkpoint.is_file():
        print(f'Reusing OpenAI Whisper weights: {args.whisper_checkpoint}', flush=True)
        convert_whisper(args.whisper_checkpoint, args.whisper_out, args.cache_dir)
    else:
        repo, files = common.MODELS['whisper']
        print('Preparing standard faster-whisper base.en; Hub cache files are reused when available.', flush=True)
        snapshot_download(repo, cache_dir=str(args.cache_dir), local_dir=str(args.whisper_out),
                          allow_patterns=list(files))
    if args.backend in ('onnx', 'both'):
        prepare_onnx(args.onnx_out)
    if args.backend in ('torch', 'both'):
        repo, files = common.MODELS['kokoro']
        print('Preparing PyTorch Kokoro: download only missing files.', flush=True)
        snapshot_download(repo, cache_dir=str(args.cache_dir), allow_patterns=list(files))
    print('Speech models prepared. Use run_conversation.ps1 on Windows.', flush=True)


if __name__ == '__main__':
    main()
