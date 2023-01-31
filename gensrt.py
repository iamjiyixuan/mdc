import os
import argparse
import ffmpy
import whisper
from whisper.utils import write_srt

# 命令行参数解析
parser = argparse.ArgumentParser()
parser.add_argument('--verbose', action='store_true')
parser.add_argument('--language', default='English')
args = parser.parse_args()


def extract_audio(file: str, verbose: bool = False) -> str:
    """
    提取音频
    """
    filename = os.path.splitext(file)[0]
    tmpMp3FilePath = os.path.join(os.getcwd(), filename + ".mp3")
    outConfig = '-y -f mp3 -ar 16000 -hide_banner -loglevel error'
    if verbose:
        outConfig = '-y -f mp3 -ar 16000'

    ff = ffmpy.FFmpeg(
        inputs={file: None},
        outputs={
            tmpMp3FilePath: outConfig}
    )
    ff.run()
    return tmpMp3FilePath


def gen_srt(audio_file: str, language: str = "English", verbose: bool = False) -> str:
    """
    生成字幕
    """
    filename = os.path.splitext(audio_file)[0]
    model = whisper.load_model("large", device="cuda")
    result = model.transcribe(
        # why set beam_size and best_of? @see https://github.com/openai/whisper/discussions/177
        tmpMp3FilePath, language=language, beam_size=5, best_of=5, verbose=verbose)
    srtFilePath = os.path.join(os.getcwd(), filename + ".srt")
    with open(srtFilePath, "w", encoding="utf-8") as srt:
        write_srt(result["segments"], file=srt)
    return srtFilePath


if __name__ == "__main__":

    for file in os.listdir(os. getcwd()):
        # 跳过隐藏文件
        if file.startswith("."):
            continue

        # 跳过文件夹
        isDirectory = os.path.isdir(os.path.join(os. getcwd(), file))
        if isDirectory:
            continue

        print("=====================", file, "=====================")

        suffix = os.path.splitext(file)[-1]
        print("suffix =", suffix)

        isMovieFile = suffix.lower().endswith((".mp4", ".mkv", ".avi"))
        if not isMovieFile:
            print("非视频文件，不处理\r\n")
            continue

        tmpMp3FilePath = extract_audio(file=file, verbose=args.verbose)
        print("已生成临时mp3文件", "===>", tmpMp3FilePath)

        print("正在生成字幕...")
        srtFilePath = gen_srt(audio_file=tmpMp3FilePath,
                              language=args.language, verbose=args.verbose)
        print("已生成srt文件", "===>", srtFilePath)

        os.remove(tmpMp3FilePath)
        print("已删除临时mp3文件", "===>", tmpMp3FilePath)
        break
