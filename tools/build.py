"""events.json から index.html と calendar.ics を作る。  python3 tools/build.py"""
import json, hashlib, datetime, os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ev = json.load(open(os.path.join(ROOT, "events.json"), encoding="utf-8"))
ev.sort(key=lambda e: (e["date"], e["start"]))

# --- index.html
tpl = open(os.path.join(ROOT, "tools", "template.html"), encoding="utf-8").read()
a, b = tpl.split("/*EVENTS*/[]/*END*/")
data = json.dumps(ev, ensure_ascii=False).replace("</", "<\\/")
open(os.path.join(ROOT, "index.html"), "w", encoding="utf-8").write(a + data + b)

# --- calendar.ics
JST = datetime.timezone(datetime.timedelta(hours=9))
def utc(d, t):
    y, m, dd = map(int, d.split("-")); hh, mm = map(int, t.split(":"))
    return datetime.datetime(y, m, dd, hh, mm, tzinfo=JST).astimezone(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
def esc(s): return s.replace("\\", "\\\\").replace(";", "\\;").replace(",", "\\,").replace("\n", "\\n")
def fold(line):
    out, cur = [], b""
    for ch in line:
        c = ch.encode()
        if len(cur) + len(c) > 73: out.append(cur.decode()); cur = b" "
        cur += c
    out.append(cur.decode()); return "\r\n".join(out)
now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
L = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//Purpose of Life//Schedule//JA", "CALSCALE:GREGORIAN", "METHOD:PUBLISH",
     "X-WR-CALNAME:Purpose of Life", "X-WR-TIMEZONE:Asia/Tokyo", "REFRESH-INTERVAL;VALUE=DURATION:PT6H", "X-PUBLISHED-TTL:PT6H"]
for e in ev:
    end = e["end"] or f'{min(int(e["start"][:2]) + 2, 23):02d}:{e["start"][3:]}'
    desc = [x for x in [
        "開場 " + e["open"] if e.get("open") else "", "開始 " + e["start"] + ("／終了 " + e["end"] if e["end"] else "（終了時刻未定）"),
        "参加費：" + e["fee"] if e.get("fee") else "", "登壇：" + e["speakers"] if e.get("speakers") else "",
        "主催：" + e["host"] if e.get("host") else "", e.get("note", ""),
        "https://pol-schedule.github.io/cal-bangnv/"] if x]
    uid = hashlib.sha1((e["date"] + e["title"]).encode()).hexdigest()[:16] + "@pol-schedule"
    L += ["BEGIN:VEVENT", "UID:" + uid, "DTSTAMP:" + now, "DTSTART:" + utc(e["date"], e["start"]), "DTEND:" + utc(e["date"], end),
          "SUMMARY:" + esc(e["title"]), "LOCATION:" + esc(e.get("addr") or e["place"]), "DESCRIPTION:" + esc("\n".join(desc)), "END:VEVENT"]
L.append("END:VCALENDAR")
open(os.path.join(ROOT, "calendar.ics"), "w", encoding="utf-8", newline="").write("\r\n".join(fold(l) for l in L) + "\r\n")
print(f"built {len(ev)} events")
