"""Isolated serving wrapper: sampling constraints plus existing audio profiling."""
from pathlib import Path
import sys

def main():
    if sys.argv[1] == 'thinker':
        import server_thinker
        from s1_listening_rules import install_sampling_rules
        install_sampling_rules(server_thinker)
    source = (Path(__file__).parent/'duplex_server_smoke.py').read_text()
    needle = 'limit_mm_per_prompt={"audio": audio_limit, "image": 0, "video": 0}'
    assert source.count(needle) == 1
    source = source.replace(needle, 'limit_mm_per_prompt={"audio": {"count": audio_limit, "length": 7680}, "image": 0, "video": 0}')
    exec(compile(source, str(Path(__file__).parent/'duplex_server_smoke.py')+' [listening constraints]', 'exec'), {'__name__':'__main__','__file__':__file__})

if __name__ == '__main__':
    main()
