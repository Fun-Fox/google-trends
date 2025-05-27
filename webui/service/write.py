import csv
import datetime
import os

import pandas as pd

from agent.main import write_in_style_assistant
from core import get_logger


def write_in_style(draft, prompt, language="中文"):
    agent_log_file_path = f"agent_{datetime.datetime.now().strftime('%Y年%m月%d日%H时%M分')}.log"
    agent_logger = get_logger(__name__, agent_log_file_path)
    try:
        ret = write_in_style_assistant(draft, prompt, language, agent_logger)
        return ret
    except Exception as e:
        print(f"处理热词时发生错误: {e}")
        return f"处理热词时发生错误: {e}"


def process_prompt(selected_row, prompt, language):
    draft = selected_row.split('/')[1]
    if not draft:
        return "无法获取 draft"
    return write_in_style(draft, prompt, language)


def save_result(result, csv_file_path, selected_row):
    if not result or not csv_file_path or not selected_row:
        return "参数不完整，无法保存"

    hot_word = selected_row.split("/")[0]  # 提取热词
    temp_file = csv_file_path + ".tmp"  # 使用临时文件避免写入失败导致数据丢失

    try:
        with open(csv_file_path, mode='r', newline='', encoding='utf-8-sig', ) as csvfile:
            reader = csv.DictReader(csvfile)
            fieldnames = reader.fieldnames

            # 检查 'result' 字段是否存在
            has_result_field = 'result' in fieldnames

            # 构建新的字段列表（如果需要）
            if not has_result_field:
                fieldnames.append('result')

            with open(temp_file, mode='w', newline='', encoding='utf-8-sig') as tmpfile:
                writer = csv.DictWriter(tmpfile, fieldnames=fieldnames)
                writer.writeheader()

                for row in reader:
                    if row['hot_word'] == hot_word:
                        # 如果有旧的 result，拼接新内容；否则直接写入
                        # old_result = row.get('result', '')
                        # if old_result is not None or old_result != "" or old_result != "nan":
                        #     row['result'] = f"{old_result}\n---\n{result}"
                        # else:
                        row['result'] = result
                    writer.writerow(row)

        # 替换原文件
        os.replace(temp_file, csv_file_path)
        return "✅ 保存成功"
    except Exception as e:
        print(f"保存失败: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        return f"❌ 保存失败: {str(e)}"


def batch_gen_save_result(prompt, hot_word_csv_files_path, language="中文"):
    if not hot_word_csv_files_path or not prompt:
        return "参数不完整，无法保存"

    try:
        # 读取CSV文件
        df = pd.read_csv(hot_word_csv_files_path, encoding='utf-8-sig')

        # 检查是否包含必要的列
        if 'hot_word' not in df.columns or 'output' not in df.columns:
            return "CSV文件缺少必要列（hot_word或output）"

        # 遍历每一行处理
        for index, row in df.iterrows():
            draft = row['output']

            if pd.isna(draft) or draft.strip() == "":
                continue  # 跳过空的output字段

            # 生成内容
            result = write_in_style(draft, prompt, language)
            if not result:
                continue  # 如果生成失败，跳过

            # 更新result列
            if 'result' in df.columns:
                # 如果已有result字段，则拼接新内容
                # tmp = df.at[index, 'result']
                # old_result = str(tmp).strip() if pd.notna(tmp) and tmp != "" else ""
                # if old_result is not None or old_result != "" or old_result != "nan":
                #     df.at[index, 'result'] = f"{old_result}\n---\n{result}"
                # else:
                df.at[index, 'result'] = result
                print(f"保存结果: {result}")
            else:
                # 添加新的result列并写入结果
                df.at[index, 'result'] = result

        # 写回CSV文件
        df.to_csv(hot_word_csv_files_path, index=False, encoding='utf-8-sig')
        return "✅ 批量生成并保存成功"
    except Exception as e:
        print(f"批量生成和保存失败: {e}")
        return f"❌ 批量生成和保存失败: {str(e)}"
