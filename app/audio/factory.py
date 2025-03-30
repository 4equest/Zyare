import os
from typing import Optional
from .base import BaseAudioSynthesizer
from .voicevox import VoicevoxSynthesizer
from .style_bert_vits2 import StyleBertVITS2Synthesizer

def create_synthesizer(engine: Optional[str] = None) -> BaseAudioSynthesizer:
    """
    音声合成エンジンを指定してインスタンスを作成する
    
    Args:
        engine (Optional[str]): 音声合成エンジンの種類。'voicevox' または 'style_bert_vits2'。
                              指定しない場合は環境変数 AUDIO_SYNTHESIZER の値を使用。
    
    Returns:
        BaseAudioSynthesizer: 音声合成クラスのインスタンス
    """
    # エンジンが指定されていない場合は環境変数から取得
    if engine is None:
        engine = os.getenv('AUDIO_SYNTHESIZER', 'voicevox')
    
    # エンジンに応じて適切なクラスを返す
    if engine.lower() == 'voicevox':
        return VoicevoxSynthesizer()
    elif engine.lower() == 'style_bert_vits2':
        return StyleBertVITS2Synthesizer()
    else:
        raise ValueError(f"未対応の音声合成エンジン: {engine}") 