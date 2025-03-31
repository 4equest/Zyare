じゃれ何とか本みたいなやつです。  
リロードでセッションが爆散する仕様が嫌になったので自作しています。  
ある程度は動くかもしれない

# セットアップ
1. requirements入れるだけなのでお好きなように。
```bash
git clone https://github.com/4equest/Zyare.git
cd Zyare
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

2. AI用のプロンプト設定
```bash
mkdir -p instance/prompts
touch instance/prompts/base.txt #編集してね
```
prompts直下にbase.txt以外のtxtを入れるとランダムにbaseに合成するようになります。
たぶん。

3. apikeyとかの設定
```bash
cp .env.example .env
```
読み上げをする場合は良い感じに設定してください。
aiを使う場合は使うサービスのapikeyを設定してください。

4. _Run_
```bash
python run.py
```