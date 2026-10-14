"""Offline checks: python week06/speech/test_speech.py (standard library only)."""

import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from queue import Empty
import types
import unittest
from unittest.mock import Mock, patch
import wave

import common
import synthesise
import transcribe

HERE = Path(__file__).resolve().parent


class OutputTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / 'nested/result.txt'

    def test_default_output_is_independent_of_working_directory(self):
        self.assertEqual(common.OUTPUT, HERE.parent / 'out')

    def test_save_text_and_settings_without_overwrite(self):
        common.save_outputs(self.path, b'hello\n', {'rate': 16000})
        self.assertEqual(self.path.read_text(), 'hello\n')
        self.assertEqual(json.loads(self.path.with_suffix('.json').read_text()), {'rate': 16000})
        with self.assertRaises(FileExistsError):
            common.save_outputs(self.path, b'changed', {})
        self.assertEqual(self.path.read_text(), 'hello\n')

    def test_existing_settings_alone_are_protected(self):
        self.path.parent.mkdir()
        self.path.with_suffix('.json').write_text('keep')
        with self.assertRaises(FileExistsError):
            common.save_outputs(self.path, b'new', {})
        self.assertFalse(self.path.exists())
        self.assertEqual(self.path.with_suffix('.json').read_text(), 'keep')

    def test_invalid_settings_leave_no_partial_output(self):
        with self.assertRaises(ValueError):
            common.save_outputs(self.path, b'new', {'bad': float('nan')})
        self.assertFalse(self.path.exists())

    def test_bad_output_suffix_is_rejected(self):
        with self.assertRaises(ValueError):
            common.check_output(self.path.with_suffix('.json'), '.txt')


class BoundaryTests(unittest.TestCase):
    def test_microphone_limits_and_exact_frame_count(self):
        self.assertEqual(transcribe.capture_frames(3, 5), 80000)
        self.assertEqual(transcribe.capture_frames(4, 15), 240000)
        for chunks, seconds in [(0,5),(13,1),(5,15),(1,0),(1,16),(1,float('nan')),(1,float('inf'))]:
            with self.subTest(chunks=chunks, seconds=seconds), self.assertRaises(ValueError):
                transcribe.capture_frames(chunks, seconds)

    def test_text_and_speed_limits(self):
        self.assertEqual(synthesise.validate(' Hello. ', 1.0), 'Hello.')
        for text, speed in [('',1),(' ',1),('a'*501,1),('hi',0.4),('hi',2.1),('hi',float('nan')),('hi',float('inf'))]:
            with self.subTest(text=text[:10], speed=speed), self.assertRaises(ValueError):
                synthesise.validate(text, speed)

    def test_wav_metadata_and_invalid_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input.wav'
            with wave.open(str(path), 'wb') as audio:
                audio.setnchannels(2)
                audio.setsampwidth(2)
                audio.setframerate(24000)
                audio.writeframes(b'\0' * 24000 * 4)
            self.assertEqual(transcribe.validate_wav(path), 1.0)
            for frames, width in [(0,2),(16000*61,2),(100,1)]:
                with wave.open(str(path), 'wb') as audio:
                    audio.setnchannels(1)
                    audio.setsampwidth(width)
                    audio.setframerate(16000)
                    audio.writeframes(b'\0' * frames * width)
                with self.assertRaises(ValueError):
                    transcribe.validate_wav(path)
            path.write_text('not audio')
            with self.assertRaises(ValueError):
                transcribe.validate_wav(path)

    def test_rejects_unreasonable_wav_rate_before_loading_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'input.wav'
            with wave.open(str(path), 'wb') as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(1000000)
                audio.writeframes(b'\0' * 100)
            with self.assertRaises(ValueError):
                transcribe.validate_wav(path)

    def test_zero_rate_wav_is_rejected_before_model_or_dependencies(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'zero-rate.wav'
            with wave.open(str(path), 'wb') as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(16000)
                audio.writeframes(b'\0' * 32)
            data = bytearray(path.read_bytes())
            data[24:28] = b'\0' * 4
            path.write_bytes(data)
            with self.assertRaises(ValueError):
                transcribe.validate_wav(path)
            errors = io.StringIO()
            with patch.object(transcribe, 'load_model') as model, patch.object(common, 'require_dependencies') as deps, contextlib.redirect_stderr(errors):
                self.assertEqual(transcribe.main(['--audio', str(path)]), 1)
            model.assert_not_called()
            deps.assert_not_called()
            self.assertIn('Cannot transcribe:', errors.getvalue())
            self.assertNotIn('Traceback', errors.getvalue())

    def test_transcription_consumes_lazy_segments_with_english_settings(self):
        model = Mock()
        consumed = []
        def segments():
            consumed.append(True)
            yield types.SimpleNamespace(text=' hello ')
            yield types.SimpleNamespace(text=' world ')
        model.transcribe.return_value = segments(), object()
        self.assertEqual(transcribe.transcribe_audio(model, 'test.wav'), 'hello world')
        self.assertTrue(consumed)
        model.transcribe.assert_called_once_with('test.wav', language='en', beam_size=1,
                                               vad_filter=True, condition_on_previous_text=False)

    def test_synthesis_keeps_all_chunks_and_rejects_empty_audio(self):
        first = Mock(); first.cpu.return_value.numpy.return_value = [0.1, 0.2]
        last = Mock(); last.cpu.return_value.numpy.return_value = [0.3]
        pipeline = Mock(return_value=iter([('a','a',first), ('b','b',last)]))
        self.assertEqual(synthesise.audio_parts(pipeline, 'Hello.', 1.2), [[0.1,0.2],[0.3]])
        pipeline.assert_called_once_with('Hello.', voice='af_heart', speed=1.2)
        with self.assertRaises(ValueError):
            synthesise.audio_parts(Mock(return_value=iter([])), 'Hello.', 1)


class CacheTests(unittest.TestCase):
    def test_cpu_compute_type_preserves_local_checkpoint_accuracy(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(common.whisper_compute_type(tmp, 'cpu'), 'float32')
            self.assertEqual(common.whisper_compute_type(tmp, 'cuda'), 'float16')
        self.assertEqual(common.whisper_compute_type('base.en', 'cpu'), 'int8')

    def test_preflight_checks_cached_files_without_loading_model(self):
        with tempfile.TemporaryDirectory() as tmp, patch.dict(os.environ, {'HF_HUB_CACHE':tmp}):
            repo = Path(tmp) / 'models--example--model'
            (repo / 'refs').mkdir(parents=True)
            (repo / 'refs/main').write_text('a' * 40)
            snapshot = repo / 'snapshots' / ('a' * 40)
            snapshot.mkdir(parents=True)
            (snapshot / 'config.json').write_text('{}')
            self.assertEqual(common.missing_model_files('example/model', ('config.json','model.bin')), ['model.bin'])
            (snapshot / 'model.bin').write_bytes(b'x')
            self.assertEqual(common.missing_model_files('example/model', ('config.json','model.bin')), [])

    def test_offline_mode_set_before_library_import(self):
        with patch.dict(os.environ, {}, clear=True):
            common.configure_network(True)
            self.assertEqual(os.environ['HF_HUB_OFFLINE'], '1')
            self.assertEqual(os.environ['TRANSFORMERS_OFFLINE'], '1')
            self.assertEqual(os.environ['HF_HUB_DISABLE_TELEMETRY'], '1')

    def test_import_help_and_preflight_work_without_site_packages(self):
        for script in ('synthesise.py','transcribe.py'):
            with self.subTest(script=script):
                result = subprocess.run([sys.executable,'-S',str(HERE/script),'--help'], capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)
                result = subprocess.run([sys.executable,'-S',str(HERE/script),'--check'], capture_output=True,text=True)
                self.assertEqual(result.returncode,1,result.stderr)
                self.assertIn('MISSING', result.stdout)
                self.assertNotIn('Traceback', result.stderr)
        result = subprocess.run([sys.executable,'-S','-c','import synthesise, transcribe'],cwd=HERE,capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stderr)

    def test_no_input_does_not_start_microphone(self):
        with patch.object(transcribe, 'load_model') as load, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as error:
                transcribe.main([])
        self.assertEqual(error.exception.code,2)
        load.assert_not_called()


class MicrophoneTests(unittest.TestCase):
    def fake_device(self, status=None, interrupt=False):
        device = types.SimpleNamespace(CallbackStop=type('Stop',(Exception,),{}),
                                       CallbackAbort=type('Abort',(Exception,),{}),
                                       PortAudioError=type('PortAudioError',(Exception,),{}),stop=Mock())
        events = []
        class Buffer:
            def __getitem__(self, key):
                return [0.25, -0.25]
        class Stream:
            def __init__(self, **kwargs):
                self.args = kwargs
                device.options = kwargs
            def __enter__(self):
                for number in range(3):
                    events.append(f'capture{number}')
                    try:
                        self.args['callback'](Buffer(),80000,None,status)
                    except (device.CallbackStop,device.CallbackAbort):
                        break
                return self
            def __exit__(self, *args):
                events.append('closed')
        device.InputStream = Stream
        model = Mock()
        def transcribe_call(audio, **kwargs):
            events.append('inference')
            if interrupt:
                raise KeyboardInterrupt
            return iter([types.SimpleNamespace(text=' hello ')]), None
        model.transcribe.side_effect = transcribe_call
        return device, model, events

    def test_bounded_continuous_capture_queues_all_chunks_and_closes(self):
        device, model, events = self.fake_device()
        with patch.dict(sys.modules, {'sounddevice':device}), contextlib.redirect_stdout(io.StringIO()):
            lines = transcribe.microphone_lines(model,3,5)
        self.assertEqual(lines,['[0.00-5.00s] hello','[5.00-10.00s] hello','[10.00-15.00s] hello'])
        self.assertEqual(events[:3],['capture0','capture1','capture2'])
        self.assertEqual(events[-1],'closed')
        self.assertEqual(device.options['blocksize'],80000)
        self.assertEqual(device.options['samplerate'],16000)
        self.assertEqual(device.options['channels'],1)
        self.assertEqual(device.options['dtype'],'float32')
        self.assertEqual(model.transcribe.call_count,3)
        device.stop.assert_called_once()

    def test_device_permission_failure_has_actionable_error(self):
        device, model, events = self.fake_device()
        device.InputStream = Mock(side_effect=device.PortAudioError('permission denied'))
        with patch.dict(sys.modules, {'sounddevice':device}), contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, '--audio'):
            transcribe.microphone_lines(model,3,5)
        device.stop.assert_called_once()

    def test_microphone_timeout_closes_stream(self):
        device, model, events = self.fake_device()
        queue = Mock()
        queue.get.side_effect = Empty
        with patch.dict(sys.modules, {'sounddevice':device}), patch.object(transcribe, 'Queue', return_value=queue), contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError, 'timed out'):
            transcribe.microphone_lines(model,3,5)
        queue.get.assert_called_once_with(timeout=10)
        device.stop.assert_called_once()
        self.assertEqual(events[-1], 'closed')

    def test_ctrl_c_closes_stream_and_stops_device(self):
        device, model, events = self.fake_device(interrupt=True)
        with patch.dict(sys.modules, {'sounddevice':device}), contextlib.redirect_stdout(io.StringIO()), self.assertRaises(KeyboardInterrupt):
            transcribe.microphone_lines(model,3,5)
        self.assertEqual(events[-1],'closed')
        device.stop.assert_called_once()

    def test_device_error_is_reported_without_inference(self):
        device, model, events = self.fake_device(status='input overflow')
        with patch.dict(sys.modules, {'sounddevice':device}), contextlib.redirect_stdout(io.StringIO()), self.assertRaisesRegex(RuntimeError,'overflow'):
            transcribe.microphone_lines(model,3,5)
        model.transcribe.assert_not_called()
        device.stop.assert_called_once()


class WiringTests(unittest.TestCase):
    def test_whisper_uses_cpu_int8_and_respects_offline(self):
        factory = Mock()
        with patch.dict(sys.modules, {'faster_whisper':types.SimpleNamespace(WhisperModel=factory)}), patch.dict(os.environ, {}, clear=True), patch.object(common, 'whisper_model', return_value='base.en'):
            transcribe.load_model(True)
            self.assertEqual(os.environ['HF_HUB_OFFLINE'], '1')
        factory.assert_called_once_with('base.en', device='cpu', compute_type='int8', local_files_only=True)

    def test_synthesis_writes_24khz_pcm_wav_using_all_chunks(self):
        class Samples(list):
            ndim = 1
        parts = [[0.1, 0.2], [0.3]]
        numpy = types.SimpleNamespace(concatenate=lambda values: Samples(sum(values, [])),
                                      isfinite=lambda values: types.SimpleNamespace(all=lambda: True))
        factory = Mock()
        writer = Mock(side_effect=lambda buffer, audio, rate, **kwargs: buffer.write(b'fake wav'))
        modules = {'kokoro':types.SimpleNamespace(KPipeline=factory), 'numpy':numpy,
                   'soundfile':types.SimpleNamespace(write=writer)}
        with patch.dict(sys.modules, modules), patch.object(synthesise, 'audio_parts', return_value=parts):
            data, duration = synthesise.synthesise('Hi.', 1, False)
        self.assertEqual(data, b'fake wav')
        self.assertEqual(duration, 3 / 24000)
        factory.assert_called_once_with(lang_code='a', repo_id='hexgrad/Kokoro-82M', device='cpu')
        self.assertEqual(writer.call_args.args[1:], ([0.1,0.2,0.3], 24000))
        self.assertEqual(writer.call_args.kwargs, {'format':'WAV', 'subtype':'PCM_16'})

    def test_synthesis_cli_saves_explicit_settings_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'voice.wav'
            with patch.object(common, 'require_dependencies'), patch.object(synthesise, 'synthesise', return_value=(b'fake wav',1.5)) as infer, contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(synthesise.main(['--text','Hello.','--speed','0.85','--out',str(path)]),0)
                self.assertEqual(synthesise.main(['--out',str(path)]),1)
            infer.assert_called_once_with('Hello.',0.85,False)
            settings = json.loads(path.with_suffix('.json').read_text())
            self.assertEqual(settings['sample_rate_hz'],24000)
            self.assertEqual(settings['voice'],'af_heart')
            self.assertEqual(settings['speed'],0.85)
            self.assertTrue(settings['synthetic'])

    def test_invalid_cli_text_never_initialises_model(self):
        with patch.object(synthesise, 'synthesise') as infer, contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(synthesise.main(['--text',' ']),1)
        infer.assert_not_called()

    def test_microphone_cancellation_leaves_no_transcript_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'transcript.txt'
            with patch.object(common, 'require_dependencies'), patch.object(transcribe, 'load_model'), patch.object(transcribe, 'microphone_lines', side_effect=KeyboardInterrupt), contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(transcribe.main(['--microphone','--out',str(path)]),130)
            self.assertFalse(path.exists())
            self.assertFalse(path.with_suffix('.json').exists())

    def test_check_flag_does_not_load_model_or_read_audio(self):
        with patch.object(common, 'preflight', return_value=True) as check, patch.object(transcribe, 'load_model') as load:
            self.assertEqual(transcribe.main(['--check','--audio','absent.wav']),0)
        check.assert_called_once_with('whisper',False)
        load.assert_not_called()


if __name__ == '__main__':
    unittest.main()
