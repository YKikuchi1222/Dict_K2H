#!/usr/bin/env python3
import argparse
import csv
import plistlib
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import jaconv
from pykakasi import kakasi
from sudachipy import Dictionary, SplitMode


GREEK_READINGS = {
    "Α": "あるふぁ",
    "α": "あるふぁ",
    "Β": "べーた",
    "β": "べーた",
    "Γ": "がんま",
    "γ": "がんま",
    "Δ": "でるた",
    "δ": "でるた",
    "Ε": "いぷしろん",
    "ε": "いぷしろん",
    "Ζ": "ぜーた",
    "ζ": "ぜーた",
    "Η": "えーた",
    "η": "えーた",
    "Θ": "しーた",
    "θ": "しーた",
    "Ι": "いおた",
    "ι": "いおた",
    "Κ": "かっぱ",
    "κ": "かっぱ",
    "Λ": "らむだ",
    "λ": "らむだ",
    "Μ": "みゅー",
    "μ": "みゅー",
    "Ν": "にゅー",
    "ν": "にゅー",
    "Ξ": "くさい",
    "ξ": "くさい",
    "Ο": "おみくろん",
    "ο": "おみくろん",
    "Π": "ぱい",
    "π": "ぱい",
    "Ρ": "ろー",
    "ρ": "ろー",
    "Σ": "しぐま",
    "σ": "しぐま",
    "ς": "しぐま",
    "Τ": "たう",
    "τ": "たう",
    "Υ": "うぷしろん",
    "υ": "うぷしろん",
    "Φ": "ふぁい",
    "φ": "ふぁい",
    "Χ": "かい",
    "χ": "かい",
    "Ψ": "ぷさい",
    "ψ": "ぷさい",
    "Ω": "おめが",
    "ω": "おめが",
}

TOKEN_REPLACEMENTS = str.maketrans(GREEK_READINGS)
KATAKANA_RE = re.compile(r"[ァ-ヴヵヶ]")
CJK_RE = re.compile(r"[\u3400-\u9fff]")

PHRASE_OVERRIDES = {
    "晶析": "しょうせき",
    "浅裂": "せんれつ",
    "蘆薈": "ろかい",
    "後彎": "こうわん",
    "後捻": "こうねん",
    "油浸": "ゆしん",
    "油浸レンズ": "ゆしんれんず",
    "胃苓湯": "いれいとう",
    "易溶": "いよう",
    "鰓曳動物": "えらひきどうぶつ",
    "鰓曳動物門": "えらひきどうぶつもん",
    "鰓裂": "さいれつ",
    "鰓裂嚢腫": "さいれつのうしゅ",
    "桂芍知母湯": "けいしゃくちもとう",
    "桂枝加苓朮附湯": "けいしかりょうじゅつぶとう",
    "桂枝茯苓丸加よく苡仁": "けいしぶくりょうがんかよくいにん",
    "五淋散": "ごりんさん",
    "五苓散": "ごれいさん",
    "茵ちん五苓散": "いんちんごれいさん",
    "茵陳五苓散": "いんちんごれいさん",
    "小荳蒄": "しょうずく",
    "竹茹": "ちくじょ",
    "防已": "ぼうい",
    "防已黄耆湯": "ぼういおうぎとう",
    "四苓湯": "しれいとう",
    "炙甘草湯": "しゃかんぞうとう",
    "苓姜朮甘湯": "りょうきょうじゅつかんとう",
    "苓桂朮甘湯": "りょうけいじゅつかんとう",
    "苓甘姜味辛夏仁湯": "りょうかんきょうみしんげにんとう",
    "莪じゅつ": "がじゅつ",
    "梹榔子": "びんろうじ",
    "阿仙薬": "あせんやく",
    "阿仙薬末": "あせんやくまつ",
    "蘚綱": "せんこう",
    "蘚類": "せんるい",
    "蘚類綱": "せんるいこう",
    "蝸電図": "かでんず",
    "蝸電図検査": "かでんずけんさ",
    "羃乗": "べきじょう",
    "訶子": "かし",
    "馴養": "じゅんよう",
    "媾疫": "こうえき",
    "喀石": "かくせき",
    "喘音": "ぜんおん",
    "啼鳴": "ていめい",
    "爆鳴": "ばくめい",
    "填塞": "てんそく",
    "埋入": "まいにゅう",
    "穿子": "せんし",
    "覆布": "ふくふ",
    "詐聴": "さちょう",
    "輸率": "ゆりつ",
    "轢音": "れきおん",
    "顆状": "かじょう",
    "顆管": "かかん",
    "鼡径": "そけい",
}

READING_REPLACEMENTS = [
    ("いっかせいこうてんせいせきがきゅう癆", "いっかせいこうてんせいせきがきゅうろう"),
    ("こうてんせいせきがきゅう癆", "こうてんせいせきがきゅうろう"),
    ("せんてんせいせきがきゅう癆", "せんてんせいせきがきゅうろう"),
    ("まんせいこうてんせいせきがきゅう癆", "まんせいこうてんせいせきがきゅうろう"),
    ("かぞくせいじゃくねんせいねふろん癆", "かぞくせいじゃくねんせいねふろんろう"),
    ("うしろがわ彎", "こうそくわん"),
    ("せきちゅうごがわ彎", "せきちゅうこうそくわん"),
    ("せきちゅうがわ彎", "せきちゅうそくわん"),
    ("せきついがわ彎", "せきついそくわん"),
    ("せんてんせいがわ彎", "せんてんせいそくわん"),
    ("とくはつせいがわ彎", "とくはつせいそくわん"),
    ("まひせいがわ彎", "まひせいそくわん"),
    ("がわ彎", "そくわん"),
    ("せきちゅうご彎", "せきちゅうこうわん"),
    ("せきちゅうまえ彎", "せきちゅうぜんわん"),
    ("まえ彎", "ぜんわん"),
    ("うちがわじょう顆", "ないそくじょうか"),
    ("そとがわじょう顆", "がいそくじょうか"),
    ("そとがわじょう顆", "がいそくじょうか"),
    ("かっしゃじょう顆", "かっしゃじょうか"),
    ("じょうわんこつうちがわじょう顆", "じょうわんこつないそくじょうか"),
    ("じょうわんこつがいじょう顆", "じょうわんこつがいじょうか"),
    ("じょうわんこつそとがわじょう顆", "じょうわんこつがいそくじょうか"),
    ("じょうわんこつ顆上", "じょうわんこつかじょう"),
    ("うえ顆", "じょうか"),
    ("さん尖弁", "さんせんべん"),
    ("せんてんせいさん尖弁", "せんてんせいさんせんべん"),
    ("ひりうまちせいさん尖弁", "ひりうまちせいさんせんべん"),
    ("そうぼうべんご尖", "そうぼうべんこうせん"),
    ("そうぼうべんまえ尖", "そうぼうべんぜんせん"),
    ("だいどうみゃくよん尖弁", "だいどうみゃくよんせんべん"),
    ("に尖大どうみゃくべん", "にせんだいどうみゃくべん"),
    ("に尖", "にせん"),
    ("すいたい尖", "すいたいせん"),
    ("三尖弁", "さんせんべん"),
    ("うち鼡径", "ないそけい"),
    ("こうやくせい鼡径", "こうやくせいそけい"),
    ("そと鼡径", "がいそけい"),
    ("ちょうこつ鼡径", "ちょうこつそけい"),
    ("へいそくせい鼡径", "へいそくせいそけい"),
    ("鼡径", "そけい"),
    ("さつ鼡剤", "さっそざい"),
    ("鼡咬", "そこう"),
    ("あつ挫", "あつざ"),
    ("かしあつ挫", "かしあつざ"),
    ("えんそ挫瘡", "えんそざそう"),
    ("挫瘡", "ざそう"),
    ("あさ裂", "せんれつ"),
    ("いへき裂", "いへきれつ"),
    ("いんとう裂", "いんとうれつ"),
    ("くちびる裂", "しんれつ"),
    ("こうがいすい裂", "こうがいすいれつ"),
    ("こうとうがい裂", "こうとうがいれつ"),
    ("こうもん裂創", "こうもんれっそう"),
    ("しゃかお裂", "しゃがんれつ"),
    ("しんがく裂", "しんがくれつ"),
    ("しん裂", "しんれつ"),
    ("じょうがんか裂", "じょうがんかれつ"),
    ("だいいち裂", "だいいちれつ"),
    ("ちゅう裂", "ちゅうれつ"),
    ("ちょくちょう裂", "ちょくちょうれつ"),
    ("とうひ裂創", "とうひれっそう"),
    ("とりきょ裂", "ちょうきょれつ"),
    ("は裂", "ようれつ"),
    ("び裂", "びれつ"),
    ("まぶた裂", "けんれつ"),
    ("みみたり裂", "じすいれつ"),
    ("め裂", "がんれつ"),
    ("よこがんめん裂", "おうがんめんれつ"),
    ("裂毛", "れつもう"),
    ("裂脳", "れつのう"),
    ("裂創", "れっそう"),
    ("裂手", "れっしゅ"),
    ("えら裂", "さいれつ"),
    ("えら裂嚢", "さいれつのう"),
    ("かがみ映核", "きょうえいかく"),
    ("かがみ映", "きょうえい"),
    ("かい映軸", "かいえいじく"),
    ("かい映", "かいえい"),
    ("映進", "えいしん"),
    ("か撤式", "かてつしき"),
    ("か療", "かりょう"),
    ("きょ睾筋", "きょこうきん"),
    ("ぎゃく嬬動", "ぎゃくぜんどう"),
    ("嬬動", "ぜんどう"),
    ("ぎゃく旋性", "ぎゃくせんせい"),
    ("どう旋的", "どうせんてき"),
    ("ぎょうこせん溶", "ぎょうこせんよう"),
    ("こうせん溶", "こうせんよう"),
    ("しお溶", "えんよう"),
    ("せん溶", "せんよう"),
    ("とも溶", "きょうよう"),
    ("溶れん", "ようれん"),
    ("えき溶", "いよう"),
    ("くび屈", "けいくつ"),
    ("けい屈", "けいくつ"),
    ("さし屈", "しゃっくつ"),
    ("はん屈", "はんくつ"),
    ("ろう屈", "ろうくつ"),
    ("屈地", "くっち"),
    ("げん捻", "げんねん"),
    ("じく捻", "じくねん"),
    ("ちょうじく捻", "ちょうじくねん"),
    ("だいたいこつけいぶまえ捻", "だいたいこつけいぶぜんねん"),
    ("ほねご捻", "こつこうねん"),
    ("ほねまえ捻", "こつぜんねん"),
    ("まえ捻", "ぜんねん"),
    ("捻曲", "ねんきょく"),
    ("捻除", "ねんじょ"),
    ("捻髪", "ねんぱつ"),
    ("こつずい癆", "こつずいろう"),
    ("がんきゅう癆", "がんきゅうろう"),
    ("じん癆", "じんろう"),
    ("ずがい癆", "ずがいろう"),
    ("せきずい癆", "せきずいろう"),
    ("せきがきゅう癆", "せきがきゅうろう"),
    ("しょう疱", "しょうほう"),
    ("こくしょくめん疱", "こくしょくめんぽう"),
    ("めん疱", "めんぽう"),
    ("せい漿", "せいしょう"),
    ("り漿", "りしょう"),
    ("漿尿", "しょうにょう"),
    ("ぜんじん輸管", "ぜんじんゆかん"),
    ("送血くだ", "そうけつかん"),
    ("送血りょう", "そうけつりょう"),
    ("すみ窒比", "たんちつひ"),
    ("すり掃法", "さっそうほう"),
    ("ふき送法", "すいそうほう"),
    ("しょう衰", "しょうすい"),
    ("じゅつご縱隔", "じゅつごじゅうかく"),
    ("よこ隔神きょう", "おうかくしんけい"),
    ("よこ隔", "おうかく"),
    ("うち肛動ぶつもん", "ないこうどうぶつもん"),
    ("うち肛動もの", "ないこうどうぶつ"),
    ("こう侵淫", "こうしんいん"),
    ("こつばんい牽出", "こつばんいけんしゅつ"),
    ("咬翼さつえい", "こうよくさつえい"),
    ("咬翼ほう", "こうよくほう"),
    ("咬し", "こうし"),
    ("咬舌", "こうぜつ"),
    ("咬虫", "こうちゅう"),
    ("じ咬", "じこう"),
    ("つめ咬癖", "そうこうへき"),
    ("傾軸", "けいじく"),
    ("嗜銀", "しぎん"),
    ("妊馬", "にんば"),
    ("尖刃かたな", "せんじんとう"),
    ("尖刃", "せんじん"),
    ("尖晶いし", "せんしょうせき"),
    ("尖度", "せんど"),
    ("尖点", "せんてん"),
    ("就下", "しゅうか"),
    ("弄舌", "ろうぜつ"),
    ("弯剪かたな", "わんせんとう"),
    ("彎剪かたな", "わんせんとう"),
    ("弯足", "わんそく"),
    ("彎足", "わんそく"),
    ("弯入", "わんにゅう"),
    ("捲着", "けんちゃく"),
    ("採皮ぶ", "さいひぶ"),
    ("揮散りょく", "きさんりょく"),
    ("揺変", "ようへん"),
    ("旋尾せんちゅう", "せんびせんちゅう"),
    ("概年", "がいねん"),
    ("概月", "がいげつ"),
    ("概潮しお", "がいちょうせき"),
    ("曖気", "あいき"),
    ("渙散", "かんさん"),
    ("爬行", "はこう"),
    ("移所", "いしょ"),
    ("穿開", "せんかい"),
    ("穿頭", "せんとう"),
    ("腐性ぶどうきゅうきん", "ふせいぶどうきゅうきん"),
    ("腐疽", "ふそ"),
    ("腐蹄", "ふてい"),
    ("くび腐病", "くびぐされびょう"),
    ("無腐性", "むふせい"),
    ("貯せいのう", "ちょせいのう"),
    ("鍍銀", "とぎん"),
    ("顆状とっき", "かじょうとっき"),
    ("むふ性ほねえし", "むふせいこつえし"),
    ("むふ性", "むふせい"),
]

CJK_CHAR_READINGS = {
    "析": "せき",
    "裂": "れつ",
    "薈": "かい",
    "挫": "ざ",
    "彎": "わん",
    "弯": "わん",
    "捻": "ねん",
    "浸": "しん",
    "癆": "ろう",
    "苓": "れい",
    "湯": "とう",
    "顆": "か",
    "肛": "こう",
    "動": "どう",
    "鼡": "そ",
    "径": "けい",
    "溶": "よう",
    "咬": "こう",
    "刺": "し",
    "曳": "ひき",
    "嚢": "のう",
    "瘡": "そう",
    "映": "えい",
    "軸": "じく",
    "核": "かく",
    "芍": "しゃく",
    "知": "ち",
    "撤": "てつ",
    "療": "りょう",
    "睾": "こう",
    "翹": "ぎょう",
    "朮": "じゅつ",
    "苡": "い",
    "仁": "にん",
    "淋": "りん",
    "齡": "れい",
    "荳": "ず",
    "蒄": "く",
    "衰": "すい",
    "係": "けい",
    "縱": "じゅう",
    "窒": "ちつ",
    "掃": "そう",
    "輸": "ゆ",
    "削": "さく",
    "爬": "は",
    "翼": "よく",
    "鳴": "めい",
    "嗜": "し",
    "刃": "じん",
    "剪": "せん",
    "概": "がい",
    "茹": "じょ",
    "窄": "さく",
    "癖": "へき",
    "摘": "てき",
    "腐": "ふ",
    "痃": "げん",
    "隔": "かく",
    "已": "い",
    "痙": "けい",
    "描": "びょう",
    "記": "き",
    "法": "ほう",
    "送": "そう",
    "牽": "けん",
    "出": "しゅつ",
    "散": "さん",
    "尖": "せん",
    "弁": "べん",
    "疱": "ほう",
    "漿": "しょう",
    "穿": "せん",
    "蝸": "か",
    "電": "でん",
    "図": "ず",
    "鍍": "と",
    "銀": "ぎん",
    "阿": "あ",
    "仙": "せん",
    "薬": "やく",
    "状": "じょう",
    "上": "じょう",
    "下": "か",
    "痛": "つう",
    "炎": "えん",
    "狭": "きょう",
    "異": "い",
    "常": "じょう",
    "系": "けい",
    "笑": "しょう",
    "斑": "はん",
    "症": "しょう",
    "性": "せい",
    "能": "のう",
    "開": "かい",
    "杆": "かん",
    "菌": "きん",
    "束": "そく",
    "癌": "がん",
}


def load_labels(csv_path: Path):
    labels = []
    ids = defaultdict(list)
    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        next(reader)
        for row in reader:
            if len(row) < 2 or not row[0]:
                continue
            label, ident = row[0], row[1]
            if label not in ids:
                labels.append(label)
            ids[label].append(ident)
    return labels, ids


def load_plist_overrides(plist_path: Path):
    if not plist_path.exists():
        return {}
    with plist_path.open("rb") as f:
        items = plistlib.load(f)
    overrides = {}
    for item in items:
        phrase = item.get("phrase")
        shortcut = item.get("shortcut")
        if phrase and shortcut:
            overrides[phrase] = shortcut
    return overrides


def load_tsv_overrides(tsv_path: Path):
    if not tsv_path.exists():
        return {}
    with tsv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f, delimiter="\t")
        return {
            row["phrase"]: row["shortcut"]
            for row in reader
            if row.get("phrase") and row.get("shortcut")
        }


def normalize_reading(text: str):
    text = unicodedata.normalize("NFKC", text)
    text = text.translate(TOKEN_REPLACEMENTS)
    text = jaconv.kata2hira(text)
    text = text.replace("･", "・")
    return text


def make_reader():
    sudachi = Dictionary(dict="full").create()
    kks = kakasi()

    def fallback(surface: str):
        parts = kks.convert(surface)
        if parts:
            return "".join(p["hira"] for p in parts)
        return surface

    def read(label: str):
        chunks = []
        for token in sudachi.tokenize(label, SplitMode.C):
            reading = token.reading_form()
            if reading == "*":
                reading = fallback(token.surface())
            chunks.append(reading)
        return normalize_reading("".join(chunks))

    return read


def apply_domain_corrections(label: str, reading: str, ids_for_label):
    if label in PHRASE_OVERRIDES:
        return PHRASE_OVERRIDES[label]

    ident_text = " ".join(ids_for_label).lower()

    if "有糸" in label:
        reading = reading.replace("ゆういと", "ゆうし")
    if "無糸" in label:
        reading = reading.replace("むいと", "むし")

    if label.endswith("相") and reading.endswith("しょう"):
        reading = reading[:-3] + "そう"

    if label.endswith("塩") and reading.endswith("しお"):
        reading = reading[:-2] + "えん"

    if "黄色" in label and label not in {"黄色", "黄色がかった"}:
        reading = reading.replace("きいろ", "おうしょく")

    if "重炭酸" in label:
        reading = reading.replace("じゅうたんさん", "じゅうたんさん")
    if "重クロム酸" in label:
        reading = reading.replace("じゅうくろむさん", "じゅうくろむさん")

    if "mobile phase" in ident_text:
        reading = reading.replace("いどうしょう", "いどうそう")

    for old, new in READING_REPLACEMENTS:
        reading = reading.replace(old, new)

    reading = "".join(CJK_CHAR_READINGS.get(char, char) for char in reading)

    return reading


def build_entries(labels, ids, overrides):
    reader = make_reader()
    entries = []
    rows = []
    review = []

    for label in labels:
        generated = apply_domain_corrections(label, reader(label), ids[label])
        shortcut = normalize_reading(overrides.get(label, generated))
        entries.append({"phrase": label, "shortcut": shortcut})
        rows.append((shortcut, label, "; ".join(ids[label]), generated, overrides.get(label, "")))
        if CJK_RE.search(shortcut) or KATAKANA_RE.search(shortcut):
            review.append((shortcut, label, "; ".join(ids[label]), generated, overrides.get(label, "")))

    entries.sort(key=lambda item: (item["shortcut"], item["phrase"]))
    rows.sort()
    review.sort()
    return entries, rows, review


def write_tsv(path: Path, rows):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n")
        writer.writerow(["shortcut", "phrase", "ids", "generated", "override"])
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", default="LifeScienceDictionaries_J2E.csv")
    parser.add_argument("--plist", default="LSD_J2J.plist")
    parser.add_argument("--seed-plist", default="")
    parser.add_argument("--readings-tsv", default="LSD_J2J_readings.tsv")
    parser.add_argument("--review-tsv", default="LSD_J2J_review.tsv")
    parser.add_argument(
        "--overrides-tsv",
        "--llm-overrides",
        dest="overrides_tsv",
        default="",
        help="TSV file with phrase and shortcut columns for manual reading overrides.",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv)
    plist_path = Path(args.plist)
    labels, ids = load_labels(csv_path)
    overrides = load_plist_overrides(Path(args.seed_plist)) if args.seed_plist else {}
    if args.overrides_tsv:
        overrides.update(load_tsv_overrides(Path(args.overrides_tsv)))
    entries, rows, review = build_entries(labels, ids, overrides)

    with plist_path.open("wb") as f:
        plistlib.dump(entries, f, sort_keys=False)
    write_tsv(Path(args.readings_tsv), rows)
    write_tsv(Path(args.review_tsv), review)

    print(f"labels={len(labels)}")
    print(f"entries={len(entries)}")
    print(f"overrides_used={sum(1 for _, label, _, _, override in rows if override)}")
    print(f"review_rows={len(review)}")


if __name__ == "__main__":
    main()
