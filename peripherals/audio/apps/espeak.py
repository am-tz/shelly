# External libs
from subprocess import run, CompletedProcess

# Internal libs
from peripherals.audio.audio import Audio
from peripherals.audio.enums.espeak_mode import EspeakMode

from gpt.langauge import Language

# General utilities
from datetime import datetime
from os.path import join, pardir, realpath, dirname, exists, expandvars
from os import remove


class ESpeak:

    __temp_tts_dir: str = None
    __espeak_cmd: str = None

    def __init__(self):

        directory: str = dirname(realpath(__file__))
        self.__temp_tts_dir = realpath(join(directory, pardir, pardir, pardir, "files", "tts"))
        windows_path: str = expandvars(join("%ProgramFiles%", "eSpeak NG", "espeak-ng.exe"))
        self.__espeak_cmd = windows_path if exists(windows_path) else "espeak"

    def tts(self, text: str, language: Language = Language.EN, mode: EspeakMode = None) -> Audio:
        tmp_txt_path: str = join(self.__temp_tts_dir, f"tts-espeak-{datetime.now():%y-%m-%d--%H-%M-%S.%f}.txt")
        with open(tmp_txt_path, "w") as fh:
            fh.write(text)
        tmp_wav_path: str = join(self.__temp_tts_dir, f"tts-espeak-{datetime.now():%y-%m-%d--%H-%M-%S.%f}.wav")

        voice_parameter: str = language.name.lower()
        if mode:
            voice_parameter += f"+{mode.name.lower()}"
        command: str = f"\"{self.__espeak_cmd}\" -f \"{tmp_txt_path}\" -w \"{tmp_wav_path}\" -v{voice_parameter}"
        proc: CompletedProcess = run(command)
        assert proc.returncode == 0

        audio = Audio(wav_filename=tmp_wav_path)

        remove(tmp_txt_path)
        remove(tmp_wav_path)

        return audio
