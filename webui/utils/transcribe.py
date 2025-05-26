# stt.py
from faster_whisper import WhisperModel

class WhisperModelSingleton:
    _instance = None
    _model = None

    def __new__(cls, model_size="large-v3", device="cpu", compute_type="int8"):
        if cls._instance is None:
            cls._instance = super(WhisperModelSingleton, cls).__new__(cls)
            # 只加载一次模型
            cls._model = WhisperModel(model_size, device=device, compute_type=compute_type)
        return cls._instance

    def transcribe(self, audio_path, **kwargs):
        """
        调用 whisper 模型进行语音识别
        :param audio_path: 音频文件路径
        :param kwargs: 其他 transcribe 参数
        :return: segments, info
        """
        segments, info = self._model.transcribe(audio_path, **kwargs)
        segments = list(segments)
        return segments, info

# 提供一个全局接口调用
def get_whisper_model():
    """
    获取单例的 Whisper 模型
    """
    return WhisperModelSingleton()
