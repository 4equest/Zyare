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

    def synthesize(self, text: str) -> Optional[bytes]:
        """
        テキストを音声に変換する
        
        Args:
            text (str): 変換するテキスト
            
        Returns:
            Optional[bytes]: 音声データ（MP3形式）。エラー時はNone
        """
        try:
            # 音声合成用のクエリを作成
            query_payload = {"text": text, "speaker": self.speaker_id}
            query_response = requests.post(
                f"{self.api_url}/audio_query",
                params=query_payload
            )
            query_response.raise_for_status()

            # 音声合成を実行
            synthesis_payload = query_response.json()
            synthesis_response = requests.post(
                f"{self.api_url}/synthesis",
                params={"speaker": self.speaker_id},
                json=synthesis_payload
            )
            synthesis_response.raise_for_status()

            return synthesis_response.content

        except Exception as e:
            print(f"VOICEVOX音声合成エラー: {str(e)}")
            return None 