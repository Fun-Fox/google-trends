import os

from webui.utils.constant import root_dir


def get_reference_audios():
    audio_dir = os.path.join(root_dir, "doc", "数字人", "参考音频")
    if not os.path.exists(audio_dir):
        return []
    audios = [f for f in os.listdir(audio_dir) if f.lower().endswith(('.wav', '.mp3'))]
    return [os.path.join(audio_dir, audio) for audio in audios]