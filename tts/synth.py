#!/usr/bin/env python3
"""ナレーション係（2026-10-17 神田さん決定：声は Google Cloud TTS Chirp 3 HD の Kore）
n-* ブランチの n/req.json を読み、1行ずつ音声（MP3）を作って n/out/ に置く。
APIキーは GitHub の Secrets（GOOGLE_TTS_KEY）だけに置く。ファイル・ログには書かない。
req.json: {"voice": "Kore", "rate": 1.1, "lines": ["文1", "文2", ...]}
出力:     n/out/00.mp3, 01.mp3, ... と n/out/done.json（{"ok": true, "files": [...]} か {"ok": false, "error": "..."}）
"""
import base64, json, os, sys, urllib.request, urllib.error

KEY = os.environ.get('GOOGLE_TTS_KEY', '')
URL = 'https://texttospeech.googleapis.com/v1/text:synthesize'
os.makedirs('n/out', exist_ok=True)

def done(obj):
    json.dump(obj, open('n/out/done.json', 'w'), ensure_ascii=False, indent=1)
    print(json.dumps(obj, ensure_ascii=False)[:500])

def main():
    if not KEY:
        return done({'ok': False, 'error': 'GOOGLE_TTS_KEY（GitHub の Secrets）が設定されていません'})
    req = json.load(open('n/req.json', encoding='utf-8'))
    voice = req.get('voice') or 'Kore'
    rate = float(req.get('rate') or 1.0)
    lines = [str(t).strip() for t in req.get('lines') or [] if str(t).strip()]
    if not lines:
        return done({'ok': False, 'error': 'lines が空です'})
    files = []
    for i, t in enumerate(lines):
        body = {'input': {'text': t},
                'voice': {'languageCode': 'ja-JP', 'name': f'ja-JP-Chirp3-HD-{voice}'},
                'audioConfig': {'audioEncoding': 'MP3', 'speakingRate': rate, 'sampleRateHertz': 24000}}
        r = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                   headers={'Content-Type': 'application/json', 'X-Goog-Api-Key': KEY})
        try:
            with urllib.request.urlopen(r, timeout=60) as res:
                audio = base64.b64decode(json.load(res)['audioContent'])
        except urllib.error.HTTPError as e:
            msg = e.read().decode(errors='replace')[:300]
            return done({'ok': False, 'error': f'Google TTS {e.code}: {msg}', 'line': i})
        except Exception as e:
            return done({'ok': False, 'error': f'Google TTS 通信エラー: {e}', 'line': i})
        f = f'{i:02d}.mp3'
        open(os.path.join('n/out', f), 'wb').write(audio)
        files.append(f)
    done({'ok': True, 'voice': voice, 'rate': rate, 'files': files})

if __name__ == '__main__':
    main()
