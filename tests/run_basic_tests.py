"""Quick smoke test - no external deps needed."""
import sys
sys.path.insert(0, 'src')

from autovideocraft.config import (
    _deep_merge, validate_llm_config, validate_media_config,
    PROVIDER_PRESETS, DEFAULT_CONFIG, TTS_VOICES,
)
from autovideocraft.utils import vtt_to_srt as _vtt_to_srt

tests_passed = 0

# Test 1: deep merge
r = _deep_merge({'a': 1, 'b': {'c': 2, 'd': 3}}, {'b': {'c': 99}})
assert r['b']['c'] == 99 and r['b']['d'] == 3
print("PASS  deep_merge basic")
tests_passed += 1

# Test 2: LLM validation - missing key
ok, err = validate_llm_config({'llm': {'api_key': '', 'base_url': 'x', 'model': 'y'}})
assert not ok and 'API Key' in err
print("PASS  validate_llm_config missing key")
tests_passed += 1

# Test 3: LLM validation - valid
ok, err = validate_llm_config({'llm': {'api_key': 'sk-x', 'base_url': 'x', 'model': 'y'}})
assert ok and err == ''
print("PASS  validate_llm_config valid")
tests_passed += 1

# Test 4: Media validation
ok, err = validate_media_config({'media': {'preferred_source': 'pexels', 'pexels_api_key': ''}})
assert not ok
print("PASS  validate_media_config missing key")
tests_passed += 1

# Test 5: Provider presets
for name, preset in PROVIDER_PRESETS.items():
    assert 'base_url' in preset and 'default_model' in preset, f"Missing fields in {name}"
print("PASS  provider_presets structure")
tests_passed += 1

# Test 6: Default config sections
for key in ['llm', 'media', 'tts', 'video']:
    assert key in DEFAULT_CONFIG, f"Missing section: {key}"
print("PASS  default_config sections")
tests_passed += 1

# Test 7: VTT to SRT conversion
vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:03.500\nHello world\n"
srt = _vtt_to_srt(vtt)
assert '00:00:01,000' in srt and 'Hello world' in srt
print("PASS  vtt_to_srt conversion")
tests_passed += 1

# Test 8: TTS voices dict
assert len(TTS_VOICES) >= 5
print("PASS  TTS_VOICES dict populated")
tests_passed += 1

print(f"\n{'='*40}")
print(f"  {tests_passed} tests PASSED")
print(f"{'='*40}")
