import os
import warnings
import sys

from webui.func.constant import root_dir, task_root_dir


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
    tts = IndexTTS(model_dir=os.path.join(root_dir,"index-tts/checkpoints"), cfg_path=os.path.join(root_dir,"index-tts/checkpoints/config.yaml"),
                   device="cuda:0",
                   use_cuda_kernel=True)
    os.makedirs(os.path.join(task_root_dir, "tts/tmp"), exist_ok=True)
    return  tts,i18n


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