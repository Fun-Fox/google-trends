# 主流程
import uuid

from heygem.easy_submit import call_easy_submit, query_easy_status

if __name__ == "__main__":
    try:
        code = uuid.uuid4()
        # 调用音频数字人合成接口
        submit_result = call_easy_submit(
            audio_url="",
            video_url="",
            code=code  # 替换为实际的唯一 key
        )
        print("Submit Result:", submit_result)

        # 查询状态
        query_easy_status(code)

    except Exception as e:
        print(f"Error: {e}")