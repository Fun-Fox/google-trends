import os
import shutil
import time

import gradio as gr

from webui.func.constant import task_root_dir, root_dir
from webui.func.csv import get_csv_files, clear_result_button_click
from webui.func.folder import get_task_folders, update_drop_down, read_result_csv_file
from webui.service.tts import init_tts, parse_speakers_and_texts


# 口播音频生成
def build_tab():
    with gr.Row():
        with gr.Column():
            task_folders = gr.Dropdown(label="选择采集热词任务列表", multiselect=False,
                                       choices=[''] + get_task_folders(),
                                       allow_custom_value=True)
            refresh_button = gr.Button("刷新任务列表")  # 新增刷新按钮

            refresh_button.click(update_drop_down, outputs=task_folders)

        with gr.Column():
            hot_word_csv_files_path = gr.Dropdown(label="选择热词清单(CSV文件)", choices=[],
                                                  allow_custom_value=False)
            refresh_csv_1_button = gr.Button("刷新热词清单(CSV文件)")

            task_folders.change(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)
            refresh_csv_1_button.click(fn=get_csv_files, inputs=task_folders, outputs=hot_word_csv_files_path)

    with gr.Row():
        content_textbox = gr.DataFrame(value=None, label="热词口播文案显示(CSV文件)",
                                       column_widths=[20, 50, 50, 50], max_height=150, max_chars=100)
        selected_row_tmp = gr.Dropdown(label="选择口播文案", choices=[], allow_custom_value=True)

        hot_word_csv_files_path.change(fn=read_result_csv_file, inputs=[hot_word_csv_files_path],
                                       outputs=[content_textbox, selected_row_tmp])
    with gr.Row():
        synthesize_button = gr.Button("开始合成语音", variant="primary")
        clear_result_button = gr.Button("清空口播文案", variant="primary")

        clear_result_button.click(clear_result_button_click, inputs=[hot_word_csv_files_path], outputs=gr.Textbox())

    def get_reference_audios():
        audio_dir = os.path.join(root_dir, "doc", "数字人", "参考音频")
        if not os.path.exists(audio_dir):
            return []
        audios = [f for f in os.listdir(audio_dir) if f.lower().endswith(('.wav', '.mp3'))]
        return [os.path.join(audio_dir, audio) for audio in audios]

    @gr.render(inputs=selected_row_tmp)
    def render_audio_inputs(selected_row_tmp_value):
        if not selected_row_tmp_value:
            return

        speaker_text_list = parse_speakers_and_texts(selected_row_tmp_value)
        speaker_list = []
        for item in speaker_text_list:
            speaker = item["speaker"]
            if speaker not in speaker_list:
                speaker_list.append(speaker)
        speaker_audio_list = []
        with gr.Row():
            reference_audios = get_reference_audios()
            for speaker in speaker_list:
                with gr.Column():
                    speaker_audio = gr.Audio(label=f"请上传角色[{speaker}]的参考音频(要求60s-110s)",
                                             sources=["upload", "microphone"],
                                             type="filepath")

                    # 下拉选择参考音频
                    audio_dropdown = gr.Dropdown(
                        label=f"或者请选择角色[{speaker}]现有的参考音频",
                        choices=reference_audios,
                        value='',
                        allow_custom_value=True
                    )

                    # 使用 .state() 来传递当前状态到函数，并选择最终使用的路径
                    def select_audio(dropdown_val, audio_val):
                        return dropdown_val if dropdown_val else audio_val

                    # 将下拉框选择的值同步到Audio 组件

                    audio_dropdown.change(
                        fn=select_audio,
                        inputs=[audio_dropdown, speaker_audio],
                        outputs=speaker_audio
                    )
                    speaker_audio.change(
                        fn=select_audio,
                        inputs=[audio_dropdown, speaker_audio],
                        outputs=speaker_audio
                    )
                    speaker_audio_list.append(speaker_audio)

        with gr.Column():
            for idx, item in enumerate(speaker_text_list):
                speaker = item["speaker"]
                text = item["text"]
                gr.Textbox(label=f"{speaker} 的台词[{idx}]", value=text, interactive=False)

        from pydub import AudioSegment

        def ms_to_srt_time(ms):
            """将毫秒转换为 SRT 时间格式"""
            total_seconds = ms // 1000
            milliseconds = ms % 1000
            seconds = total_seconds % 60
            minutes = (total_seconds // 60) % 60
            hours = total_seconds // 3600
            return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

        from datetime import datetime
        def synthesize_multiple_voices(*speaker_au_list):
            tts, i18n = init_tts()
            output_files_by_speaker = {}
            # output_files_by_speaker_list = []
            # 存储语音路径 + speaker 名称 + 时长信息
            output_files_with_duration = []
            output_files = []
            progress = gr.Progress()
            progress(0, desc="开始生成语音")
            text_length = len(speaker_text_list)
            # 初始化时间轴变量
            current_time = 0
            formatted_time = datetime.fromtimestamp(time.time()).strftime("%Y年%m月%d日%H时%M分%S秒")

            for i, audio_item in enumerate(speaker_text_list, start=1):
                progress(i / text_length * 0.1, f"开始生成第{i}段文本的语音")
                speaker_name = audio_item["speaker"]
                speaker_audio_path = speaker_au_list[speaker_list.index(speaker_name)]
                content = audio_item["text"]
                if not speaker_audio_path or not content:
                    return None
                print(f"参考音频数据:角色：{speaker_name},路径:{speaker_audio_path}")
                output_path = os.path.join(task_root_dir, "tmp", f"{i}_{speaker_name}_{formatted_time}.wav")
                progress(i / text_length * 0.6, f"第{i}段文本的语音生成成功")
                tts.infer_fast(speaker_audio_path, content, output_path)
                output_files.append(output_path)

                # 获取语音时长（毫秒）
                segment = AudioSegment.from_wav(output_path)
                duration_ms = len(segment)  # 毫秒

                # 添加时间轴信息

                start_time = current_time
                end_time = current_time + duration_ms
                current_time = end_time  # 更新时间轴

                # 存储完整信息
                output_files_with_duration.append({
                    "speaker": speaker_name,
                    "path": output_path,
                    "duration": duration_ms,
                    "content": content,
                    "start_time": start_time,
                    "end_time": end_time
                })

            # 第二步：对每个 speaker 的音频按 i 升序排序并拼接
            progress(0.7, f"开始按角色进行独立音轨拼接（含等待静音）")
            hot_word = selected_row_tmp_value.split("/")[0]
            results_id = selected_row_tmp_value.split("/")[1]
            task_path = os.path.join(task_root_dir, os.path.basename(task_folders.value), hot_word, "tts" )

            for speaker_name in set(seg["speaker"] for seg in output_files_with_duration):
                # 筛选当前 speaker 的语音段
                speaker_segments = [seg for seg in output_files_with_duration if seg["speaker"] == speaker_name]
                speaker_segments.sort(key=lambda x: x["start_time"])  # 按时间排序

                combined_audio = AudioSegment.empty()
                last_end_time = 0  # 上一段结束时间

                for seg in speaker_segments:
                    start_time = seg["start_time"]
                    file_path = seg["path"]

                    # 插入等待静音
                    if start_time > last_end_time:
                        silence_duration = start_time - last_end_time
                        print(f"插入等待静音片段： {silence_duration}ms ")
                        silence = AudioSegment.silent(duration=silence_duration)
                        combined_audio += silence

                    # 添加当前语音
                    segment = AudioSegment.from_wav(file_path)
                    combined_audio += segment

                    # 更新最后时间
                    last_end_time = seg["end_time"]

                # 保存最终拼接文件

                os.makedirs(task_path, exist_ok=True)

                final_output_path = os.path.join(
                    task_path,
                    f"热点词_{hot_word}_口播稿ID_{results_id}_角色_{speaker_name}_{formatted_time}.wav"
                )
                combined_audio.export(final_output_path, format="wav")
                output_files_by_speaker[speaker_name] = final_output_path
            progress(0.8, f"角色独立音轨拼接完成")

            # 第三步 导出 SRT 字幕文件
            srt_path = os.path.join(task_path, f"热点词_{hot_word}__口播稿ID_{results_id}_{formatted_time}_字幕.srt")
            with open(srt_path, "w", encoding="utf-8-sig") as f:
                for i, seg in enumerate(output_files_with_duration, start=1):
                    start = ms_to_srt_time(seg["start_time"])
                    end = ms_to_srt_time(seg["end_time"])
                    content = seg["content"].strip()
                    # speaker = seg["speaker"]
                    f.write(f"{i}\n{start} --> {end}\n{content}\n\n")
                    # f.write(f"{i}\n{start} --> {end}\n[{speaker}] {content}\n\n")
            progress(1, f"SRT 字幕已经生成")

            # 清空零时文件夹
            tmp_folder = os.path.join(task_root_dir, "tmp")
            if os.path.exists(tmp_folder):
                for file in os.listdir(tmp_folder):
                    file_path = os.path.join(tmp_folder, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                        elif os.path.isdir(file_path):
                            shutil.rmtree(file_path)
                    except Exception as e:
                        print(f"删除 {file_path} 失败: {e}")
            else:
                os.makedirs(tmp_folder, exist_ok=True)
            output_text = '\n\n'.join([f"{k}:{v}" for k, v in output_files_by_speaker.items()])

            return gr.Textbox(value=output_text)

        output_audio = gr.Textbox()

        synthesize_button.click(
            synthesize_multiple_voices,
            inputs=speaker_audio_list,
            outputs=output_audio
        )
