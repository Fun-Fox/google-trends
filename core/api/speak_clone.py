import requests

base_url = "http://x.x.x.x:18180/v1/invoke"

headers = {
    'Content-Type': 'application/json'
}
data = {
    "speaker": "1",  # 一个UUID保持唯一即可，这块本人建议使用时间戳
    "text": "该组件提供四种不同类型的方式。",  # 需要合成的文本内容
    "format": "wav",  # 固定传参
    "topP": 0.7,  # 固定传参
    "max_new_tokens": 1024,  # 固定传参
    "chunk_length": 100,  # 固定传参
    "repetition_penalty": 1.2,  # 固定传
    "temperature": 0.7,  # 固定传参
    "need_asr": "false",  # 固定传参
    "streaming": "false",  # 固定传参
    "is_fixed_seed": 0,  # 固定传参
    "is_norm": 0,  # 固定传参
    "reference_audio": "/code/sessions/20250319/7b9dcb869eac4a1292dfab602e66d00d/format_denoise_raw_part0.wav",
    # 上一步ASR的返回值
    "reference_text": "上述检查项目未完成xxxxxx。"  # 上一步“模特训练”的返回值
}

result = requests.post(url=base_url, json=data, headers=headers)

# 直接返回二进制流，将二进制流写入文件中即可（至此语音克隆完成）：
with open('./file/output.wav', 'wb') as file:
    file.write(result.content)
————————————————

版权声明：本文为博主原创文章，遵循
CC
4.0
BY - SA
版权协议，转载请附上原文出处链接和本声明。

原文链接：https: // blog.csdn.net / qq_45383803 / article / details / 146387044