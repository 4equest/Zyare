import os
import requests
from typing import Optional
from .base import BaseAudioSynthesizer

class VoicevoxSynthesizer(BaseAudioSynthesizer):
    """VOICEVOXを使用した音声合成クラス"""
    
    def __init__(self):
        super().__init__()
        self.api_key = os.getenv('VOICEVOX_API_KEY')
        self.api_url = os.getenv('VOICEVOX_API_URL', 'http://localhost:50021')
        self.speaker_id = int(os.getenv('VOICEVOX_SPEAKER_ID', '1'))

    def synthesize(self, text: str, speaker_id: int|None = None) -> Optional[bytes]:
        """
        テキストを音声に変換する
        
        Args:
            text (str): 変換するテキスト
            
        Returns:
            Optional[bytes]: 音声データ（MP3形式）。エラー時はNone
        """
        if speaker_id is None:
            speaker_id = self.speaker_id
        try:
            query_payload = {
                "text": text,
                "speaker": speaker_id,
                "key": self.api_key
            }
            response = requests.post(
                f"{self.api_url}/audio/",
                params=query_payload
            )
            response.raise_for_status()

            return response.content

        except Exception as e:
            print(f"VOICEVOX音声合成エラー: {str(e)}")
            return None 