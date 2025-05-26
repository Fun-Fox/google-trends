# stt.py
import os

from faster_whisper import WhisperModel

from webui.utils.constant import root_dir
import warnings
# 定义模型存放位置

LOCAL_MODEL_PATH=os.path.join(root_dir,'models', "faster-distil-whisper-large-v3.5")

class WhisperModelSingleton:
    _instance = None
    _model = None

    def __new__(cls, model_size="deepdml/faster-whisper-large-v3.5", device="auto", compute_type="float16"):

        warnings.filterwarnings("ignore", category=FutureWarning)
        warnings.filterwarnings("ignore", category=UserWarning)
        if cls._instance is None:
            cls._instance = super(WhisperModelSingleton, cls).__new__(cls)

            # 如果本地存在模型，则从本地加载
            if os.path.exists(LOCAL_MODEL_PATH):
                print(f"📦 正在从本地加载模型: {LOCAL_MODEL_PATH}")
                cls._model = WhisperModel(
                    model_size_or_path=LOCAL_MODEL_PATH,
                    device=device,
                    compute_type=compute_type
                )
            else:
                print(f"🌐 未找到本地模型，正在从远程下载: {model_size}")
                cls._model = WhisperModel("deepdml/faster-whisper-large-v3.5")
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


if __name__ == "__main__":
    # 测试代码
    import warnings

    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    model = get_whisper_model()
    HF_ENDPOINT = "https://hf-mirror.com"
    # 设置环境变量
    os.environ["HF_ENDPOINT"] = HF_ENDPOINT
    segments, info = model.transcribe(r"D:\PycharmProjects\google-trends\doc\数字人\参考音频\Trump.wav")
    segments=list(segments)
    for segment in segments:
        print("[%.2fs -> %.2fs] %s" % (segment.start, segment.end, segment.text))
    print(segments)
    print(info)