import requests
url = "http://192.168.1.12"
base_url = url+":8383/easy/submit"

headers = {
    'Content-Type': 'application/json'
}
data = {
    "audio_url": "output.wav",  # 音频路径,容器内部路径（docker-compose.yaml有映射），目前这块没自带上传下载接口，本人这段时间会写接口串起来。
    "video_url": "1.mp4",  # 音频路径,容器内部路径（docker-compose.yaml有映射），目前这块没自带上传下载接口，本人这段时间会写接口串起来。
    "code": "2",  # 唯一key（时间戳即可）
    "chaofen": 0,  # 固定值
    "watermark_switch": 0,  # 固定值
    "pn": 1  # 固定值
}

result = requests.post(url=base_url, json=data, headers=headers)

print(result.text)
# 返回参数
# {
#     "code": 10000,  # 改code用查询视频生成状态
#     "data": {},
#     "msg": 10000,
#     "success": true
# }
