# stt.py
from faster_whisper import WhisperModel

<<<<<<< HEAD
from webui.utils.constant import root_dir
import warnings
# 定义模型存放位置

LOCAL_MODEL_PATH=os.path.join(root_dir,'models', "faster-distil-whisper-large-v3.5")

=======
>>>>>>> parent of 4562e4d (fix)
class WhisperModelSingleton:
    _instance = None
    _model = None

<<<<<<< HEAD
    def __new__(cls, model_size="deepdml/faster-whisper-large-v3.5", device="auto", compute_type="float16"):

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
=======
    def __new__(cls, model_size="large-v3", device="cpu", compute_type="int8"):
>>>>>>> parent of 4562e4d (fix)
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
