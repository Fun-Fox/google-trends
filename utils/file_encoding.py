import chardet
def detect_encoding(file_path, sample_size=10000):
    """自动检测文件编码"""
    with open(file_path, "rb") as f:
        raw_data = f.read(sample_size)
    result = chardet.detect(raw_data)
    return result["encoding"]
