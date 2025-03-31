from pydub import AudioSegment
import io
from abc import ABC, abstractmethod
from typing import Optional
from pathlib import Path

class BaseAudioSynthesizer(ABC):
    """音声合成の基底クラス"""
    
    def __init__(self):
        self.api_key = None
        self.api_url = None
        self.speaker_id = 1  # デフォルトの話者ID

    @abstractmethod
    def synthesize(self, text: str) -> Optional[bytes]:
        """
        テキストを音声に変換する
        
        Args:
            text (str): 変換するテキスト
            
        Returns:
            Optional[bytes]: 音声データ（MP3形式）。エラー時はNone
        """
        pass

    def save_audio(self, audio_data: bytes, room_id: int, note_id: int, turn: int) -> Optional[str]:
        """
        音声データをファイルとして保存する
        
        Args:
            audio_data (bytes): 音声データ
            room_id (int): ルームID
            note_id (int): ノートID
            turn (int): ターン番号
            
        Returns:
            Optional[str]: 保存したファイルのパス。エラー時はNone
        """
        try:
            # 保存先ディレクトリを作成
            save_dir = Path(f"instance/audio/{room_id}")
            save_dir.mkdir(parents=True, exist_ok=True)

            # ファイル名を生成
            filename = f"{note_id}_{turn}.mp3"
            filepath = save_dir / filename

            # audio_dataがmp3でなければmp3に変換する
            if not audio_data.startswith(b'ID3'):
                audio_segment = AudioSegment.from_file(io.BytesIO(audio_data))
                audio_data = io.BytesIO()
                audio_segment.export(audio_data, format="mp3")
                audio_data = audio_data.getvalue()
            # 音声データを保存
            with open(filepath, "wb") as f:
                f.write(audio_data)

            return str(filepath)

        except Exception as e:
            print(f"音声ファイル保存エラー: {str(e)}")
            return None 