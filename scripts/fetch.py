import json, os, urllib.request, urllib.parse

IDS = ["VVsZ4LupGew", "2odWQBNJMRc", "1Xylvz58p0k"]
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"

def get(url, data=None, headers=None, timeout=50):
    h = {"User-Agent": UA, "Accept": "*/*"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()

def save(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)

invidious = ["https://inv.nadeko.net", "https://invidious.nerdvpn.de", "https://yewtu.be",
             "https://invidious.f5.si", "https://iv.melmac.space", "https://invidious.privacyredirect.com",
             "https://inv.tux.pizza", "https://invidious.jing.rocks"]
piped = ["https://pipedapi.kavin.rocks", "https://api.piped.private.coffee", "https://pipedapi.adminforge.de",
         "https://pipedapi.reallyaweso.me"]

log = []
for vid in IDS:
    d = "out/%s" % vid
    os.makedirs(d, exist_ok=True)
    # ---- Invidious ----
    for inst in invidious:
        host = urllib.parse.urlparse(inst).netloc.replace(".", "_")
        try:
            st, b = get(inst + "/api/v1/captions/" + vid)
            save("%s/inv_%s_list.json" % (d, host), b)
            log.append([vid, inst, "list", st, len(b)])
            try:
                j = json.loads(b)
            except Exception:
                continue
            for cap in j.get("captions", []) or []:
                lang = cap.get("language_code") or cap.get("srclang") or "na"
                u = cap.get("url", "")
                if u.startswith("/"):
                    u = inst + u
                try:
                    st2, b2 = get(u)
                    save("%s/inv_%s_%s.vtt" % (d, host, lang.replace("/", "_")), b2)
                    log.append([vid, inst, "cap_" + lang, st2, len(b2)])
                except Exception as e:
                    log.append([vid, inst, "cap_err_" + lang, type(e).__name__, str(e)[:120]])
        except Exception as e:
            log.append([vid, inst, "err", type(e).__name__, str(e)[:120]])
    # ---- Piped ----
    for inst in piped:
        host = urllib.parse.urlparse(inst).netloc.replace(".", "_")
        try:
            st, b = get(inst + "/streams/" + vid)
            save("%s/piped_%s_streams.json" % (d, host), b)
            log.append([vid, inst, "streams", st, len(b)])
            try:
                j = json.loads(b)
            except Exception:
                continue
            for sub in j.get("subtitles", []) or []:
                u = sub.get("url", "")
                if u.startswith("/"):
                    u = inst + u
                code = sub.get("code", "na")
                try:
                    st2, b2 = get(u)
                    save("%s/piped_%s_%s.vtt" % (d, host, code.replace("/", "_")), b2)
                    log.append([vid, inst, "sub_" + code, st2, len(b2)])
                except Exception as e:
                    log.append([vid, inst, "sub_err_" + code, type(e).__name__, str(e)[:120]])
        except Exception as e:
            log.append([vid, inst, "err", type(e).__name__, str(e)[:120]])
    # ---- Tactiq ----
    for lang in ["hi", "en"]:
        try:
            body = json.dumps({"videoUrl": "https://www.youtube.com/watch?v=" + vid, "langCode": lang}).encode()
            st, b = get("https://tactiq-apps-prod.tactiq.io/transcript", data=body,
                        headers={"Content-Type": "application/json", "Origin": "https://tactiq.io",
                                 "Referer": "https://tactiq.io/"})
            save("%s/tactiq_%s.json" % (d, lang), b)
            log.append([vid, "tactiq", lang, st, len(b)])
        except Exception as e:
            log.append([vid, "tactiq", "err_" + lang, type(e).__name__, str(e)[:150]])
    # ---- Kome ----
    try:
        body = json.dumps({"video_id": vid, "format": True}).encode()
        st, b = get("https://api.kome.ai/api/tools/youtube-transcripts", data=body,
                    headers={"Content-Type": "application/json", "Origin": "https://kome.ai",
                             "Referer": "https://kome.ai/"})
        save("%s/kome.json" % d, b)
        log.append([vid, "kome", "t", st, len(b)])
    except Exception as e:
        log.append([vid, "kome", "err", type(e).__name__, str(e)[:150]])
    # ---- notegpt ----
    try:
        st, b = get("https://notegpt.io/api/v2/video-transcript?platform=youtube&video_id=" + vid)
        save("%s/notegpt.json" % d, b)
        log.append([vid, "notegpt", "t", st, len(b)])
    except Exception as e:
        log.append([vid, "notegpt", "err", type(e).__name__, str(e)[:150]])
    # ---- youtubetranscript.com ----
    try:
        st, b = get("https://youtubetranscript.com/?server_vid2=" + vid)
        save("%s/ytcom.html" % d, b)
        log.append([vid, "youtubetranscript.com", "t", st, len(b)])
    except Exception as e:
        log.append([vid, "youtubetranscript.com", "err", type(e).__name__, str(e)[:150]])

save("out/log.json", json.dumps(log, indent=1).encode())
print(json.dumps(log, indent=1))
