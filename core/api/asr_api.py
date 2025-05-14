import json
import requests
import os

url = "http://192.168.1.12/"
# 上传文件
def upload(file_path, file_format):
    if not os.path.exists(file_path):
        print(f"文件 {file_path} 不存在")
        return

    base_url = url+":15000/voice/upload"
    files = [
        ('filename', (os.path.basename(file_path),
                      open(file_path, 'rb')))
    ]
    data = {
        'format': file_format
    }
    response = requests.post(base_url, files=files, data=data)
    return response.json()


# ASR
def asr(file_name, file_format):
    base_url = url+":18180/v1/preprocess_and_tran"
    data = {
        "format": f"{file_format}",
        "reference_audio": furl+":18080/upload/wav/{file_name}.{file_format}",
        "lang": "zh"
    }
    response = requests.post(url=base_url, json=data)
    return response.json()


def tts(speaker, text, reaudio, retext):
    base_url = url+":18180/v1/invoke"
    data = {
        "speaker": f"{speaker}",  # 一个UUID保持唯一即可
        "text": f"{text}",  # 需要合成的文本内容
        "format": "wav",  # 固定传参
        "topP": 0.7,  # 固定传参
        "max_new_tokens": 1024,  # 固定传参
        "chunk_length": 100,  # 固定传参
        "repetition_penalty": 1.2,  # 固定传参
        "temperature": 0.7,  # 固定传参
        "need_asr": "false",  # 固定传参
        "streaming": "false",  # 固定传参
        "is_fixed_seed": 0,  # 固定传参
        "is_norm": 0,  # 固定传参
        "reference_audio": f"{reaudio}",  # 上一步“模特训练”的返回值
        "reference_text": f"{retext}"  # 上一步“模特训练”的返回值
    }

    response = requests.post(url=base_url, json=data)
    # 检查响应状态码
    if response.status_code != 200:
        return {"filecode": "failed", "msg": f"请求失败，状态码: {response.status_code}"}
    # 检查响应的内容类型
    if response.headers.get('Content-Type') != 'audio/wav':
        return {"filecode": "failed", "msg": f"响应内容类型不正确: {response.headers.get('Content-Type')}"}
    # 生成文件名
    file_name = f"{speaker}.wav"  # 使用 speaker 和 text 的前10个字符作为文件名
    # 保存二进制数据到文件
    with open(f'./download/{file_name}', 'wb') as f:
        f.write(response.content)
    return {"filecode": "succeed", "filename": file_name}


# 下载文件
def download(timecode, format):
    base_url = url+":15000/voice/download"
    data = {
        "format": format,
        "timecode": timecode
    }
    response = requests.get(base_url, json=data)
    print()
    if response.status_code == 200:
        with open(f'./download/{timecode}_download.{format}', 'wb') as f:
            f.write(response.content)
        return json.dumps({'success': 'download successfully'})
    else:
        return json.dumps({'error': 'File download failure'})


if __name__ == '__main__':
    upload_file = upload("./file/bb.wav", "wav")
    print(upload_file)
    # print(upload_file['timecode'])
    # download_file = download("20250322185649883", "wav")
    # print(download_file)
    asr = asr(upload_file['timecode'], upload_file['format'])
    print(asr)
    text = '哎哟，说到这赛季的寒冰射手，我真是有话要说！别看她现在技能改得好像有点用，什么Q技能加攻速、W技能减速带伤害，听起来挺牛掰，但实际上呢？还是那个脆皮到不行的老问题。你稍微一露头，对面刺客直接就给你秒了，根本没得商量。玩艾希就像在走钢丝，稍不注意就被人家抓个正着。'
    tts = tts(upload_file['timecode'], text, asr['asr_format_audio_url'], asr['reference_audio_text'])
