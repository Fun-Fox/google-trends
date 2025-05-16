# 主流程
if __name__ == "__main__":
    try:
        # 调用 preprocess_and_tran
        preprocess_result = call_preprocess_and_tran(
            format=".wav",
            reference_audio="tasks/tts/2025年05月16日13时05分_日本_汽车与交通工具/音频.wav",
            lang="zh"
        )
        print("Preprocess Result:", preprocess_result)

        # 调用 easy_submit
        submit_result = call_easy_submit(
            audio_url=preprocess_result["asr_format_audio_url"],
            video_url="doc/数字人/参考视频/a.mp4",
            code="your_unique_code_here"  # 替换为实际的唯一 key
        )
        print("Submit Result:", submit_result)

        # 查询状态
        query_easy_status(submit_result["code"])

    except Exception as e:
        print(f"Error: {e}")