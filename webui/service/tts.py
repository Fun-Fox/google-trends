import os
import warnings
import sys

from torchvision.version import cuda

from webui.utils.constant import root_dir, task_root_dir


def singleton(func):
    instances = {}

    def wrapper(*args, **kwargs):
        if 'instance' not in instances:
            instances['instance'] = func(*args, **kwargs)
        return instances['instance']

    return wrapper


@singleton
def init_tts():
    warnings.filterwarnings("ignore", category=FutureWarning)
    warnings.filterwarnings("ignore", category=UserWarning)

    sys.path.append(root_dir)
    sys.path.append(os.path.join(root_dir, 'index-tts', "indextts"))
    from indextts.infer import IndexTTS
    from tools.i18n.i18n import I18nAuto
    i18n = I18nAuto(language="zh_CN")
    # 自动判断是否支持 CUDA
    if cuda.is_available():
        print("🎮 CUDA 可用，使用 GPU 加载模型")
        device = "cuda:0"
    else:
        print("☁️ CUDA 不可用，使用 CPU 加载模型")
        device = "cpu"
    try:
        tts = IndexTTS(
            model_dir=os.path.join(root_dir, "index-tts/checkpoints"),
            cfg_path=os.path.join(root_dir, "index-tts/checkpoints/config.yaml"),
            device=device,
            use_cuda_kernel=cuda.is_available()  # 如果有 CUDA 才使用加速内核
        )
    except Exception as e:
        print(f"⚠️ 使用指定设备加载失败: {e}，尝试使用默认设备重新加载...")
        # 再次兜底
        fallback_device = "cpu"
        tts = IndexTTS(
            model_dir=os.path.join(root_dir, "index-tts/checkpoints"),
            cfg_path=os.path.join(root_dir, "index-tts/checkpoints/config.yaml"),
            device=fallback_device,
            use_cuda_kernel=False
        )

    return tts, i18n


def parse_speakers_and_texts(selected_row_tmp_value):
    parts = selected_row_tmp_value.split("/")
    if len(parts) < 3:
        return []

    content = "/".join(parts[2:])  # 获取实际文本部分，防止热词或序号中包含 '/'

    if '\n' not in content.strip():
        speaker, text = content.replace("<", "").replace(">", "").strip().strip('\n').split(':', 1)

        return [{"speaker": speaker.strip(), "text": text.strip()}]

    lines = content.strip().split('\n')
    lines = [line for line in lines if line.strip()]

    result = []
    for line in lines:
        colon_pos = line.find(':') if ':' in line else line.find('：')
        if colon_pos != -1:
            speaker, text = line.split(line[colon_pos], 1)
            result.append({"speaker": speaker.strip(), "text": text.strip()})

    return result