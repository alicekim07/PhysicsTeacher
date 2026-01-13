import os
import re
from moviepy import AudioFileClip
from openai import OpenAI

client = OpenAI()
# Heuristic 방식 자막 생성
def split_sentence(text):
    """
    문장 단위로 분리
    (마침표, 물음표, 느낌표 기준)
    """
    sentences = re.split(r'(?<=[.!?])\s+', text)
    return [s.strip() for s in sentences if s.strip()]

def sec_to_srt_time(sec):
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    s = int(sec % 60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"

def make_srt_from_script(script_path: str, audio_path: str, out_path: str):
    # 스크립트 로드
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()

    sentences = split_sentence(text)

    # 음성 길이
    audio = AudioFileClip(audio_path)
    total_duration = audio.duration

    # 문장 길이 기반 가중치
    lengths = [len(s) for s in sentences]
    total_len = sum(lengths)

    current_time = 0.0

    with open(out_path, "w", encoding="utf-8") as f:
        for idx, (sentence, length) in enumerate(zip(sentences, lengths), start=1):
            duration = total_duration * (length / total_len)
            start = current_time
            end = current_time + duration
            current_time = end

            f.write(f"{idx}\n")
            f.write(f"{sec_to_srt_time(start)} --> {sec_to_srt_time(end)}\n")
            f.write(sentence+ "\n\n")

# API 방식 자막 생성
def make_srt_api(audio_path, out_path):
    with open(audio_path, "rb") as f:
        srt_text = client.audio.transcriptions.create(
            file=f,
            model="whisper-1",
            response_format="srt",
            language="ko"
        )

    with open(out_path, "w", encoding="utf-8") as f:
        f.write(srt_text)

# Experiment 1: API로 생성한 SRT의 텍스트를 스크립트로 교체
def parse_srt(srt_text: str):
    """
    SRT -> [(index, start, end, text)]
    """
    blocks = re.split(r"\n\s*\n", srt_text.strip())
    entries = []

    for block in blocks:
        lines = block.strip().splitlines()
        if len(lines) >= 3:
            idx = lines[0]
            time = lines[1]
            text = " ".join(lines[2:])
            entries.append((idx, time, text))

    return entries

def fit_sentence_to_slots(sentences, slot_count):
    """
    script 문장들을 SRT 슬롯 개수에 맞춤
    """
    if len(sentences) == slot_count:
        return sentences
    
    # 문장이 너무 많을 때 -> 병합
    if len(sentences) > slot_count:
        merged = []
        ratio = len(sentences) / slot_count
        acc = 0.0
        buf = []

        for s in sentences:
            buf.append(s)
            acc += 1
            if acc >= ratio:
                merged.append(" ".join(buf))
                buf = []
                acc = 0.0

        if buf:
            merged[-1] += " " + " ".join(buf)

        return merged
    
    # 문장이 부족할 때 -> 분산
    if len(sentences) < slot_count:
        expanded = []
        idx = 0

        for i in range(slot_count):
            if idx < len(sentences) - 1:
                expanded.append(sentences[idx])
                idx += 1
            else:
                # 마지막 문장을 조금씩 나눠 채움
                expanded.append(sentences[-1])

        return expanded

def replace_srt_text_with_script(srt_path: str, script_path: str, out_path: str):
    # SRT 로드
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_content = f.read()

    # Script 로드
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 파싱
    srt_entries = parse_srt(srt_content)
    script_sentences = split_sentence(script_text)

    # 문장 개수 맞추기
    fitted_sentences = fit_sentence_to_slots(script_sentences, len(srt_entries))

    # SRT 재구성
    with open(out_path, "w", encoding="utf-8") as f:
        for (idx, time, _), sentence in zip(srt_entries, fitted_sentences):
            f.write(f"{idx}\n")
            f.write(f"{time}\n")
            f.write(f"{sentence}\n\n")

# Experiment 2: N-Chunks 방식(시도 X)

# Experiment 3: SRT 각 블록의 텍스트 길이를 측정 -> Script를 앞에서부터 그 길이만큼 잘라서 대체
def parse_srt_with_text(srt_text: str):
    pattern = re.compile(
        r"(\d+)\n"
        r"(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n"
        r"(.*?)(?=\n\n|\Z)",
        re.S
    )

    blocks = []
    for m in pattern.finditer(srt_text):
        idx, start, end, text = m.groups()
        clean = text.replace("\n", " ").strip()
        blocks.append({
            "idx": int(idx),
            "start": start,
            "end": end,
            "len": len(clean)
        })
    return blocks

def replace_by_sentence_length(blocks, script_text):
    script = script_text.replace("\n", " ").strip()
    cursor = 0
    results = []

    for i, block in enumerate(blocks):
        if i == len(blocks) - 1:
            chunk = script[cursor:].strip()
        else:
            take = block["len"]
            chunk = script[cursor:cursor + take].strip()
            cursor += take

        results.append(chunk)

    return results

def replace_srt_text_with_script_by_length(srt_path: str, script_path: str, out_path: str):
    # SRT 로드
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_text = f.read()

    # Script 로드
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 파싱
    blocks = parse_srt_with_text(srt_text)
    new_texts = replace_by_sentence_length(blocks, script_text)

    output = []
    for block, text in zip(blocks, new_texts):
        output.append(f"{block['idx']}")
        output.append(f"{block['start']} --> {block['end']}")
        output.append(text)
        output.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

# Experiment 4: 길이는 목표치, cut은 공백/조사 기준
def smart_cut(text, start, target_len, margin=15):
    """
    start부터 target_len 근처에서
    가장 자연스러운 cut 위치를 찾는다
    """
    end_min = max(start + target_len - margin, start + 1)
    end_max = min(start + target_len + margin, len(text))

    window = text[end_min:end_max]

    # 우선순위 높은 순
    cut_chars = [".", "?", ",", " "]

    best = None
    best_dist = None

    for i, ch in enumerate(window):
        if ch in cut_chars:
            pos = end_min + i
            dist = abs(pos - (start + target_len))
            if best is None or dist < best_dist:
                best = pos
                best_dist = dist

    if best is not None:
        return best

    # fallback: 그냥 target_len
    return min(start + target_len, len(text))

def replace_by_sentence_length_smart(blocks, script_text):
    script = script_text.replace("\n", " ").strip()
    cursor = 0
    results = []

    for i, block in enumerate(blocks):
        if cursor >= len(script):
            results.append("")
            continue

        if i == len(blocks) - 1:
            # 마지막 블록은 남은 거 전부
            chunk = script[cursor:].strip()
            cursor = len(script)
        else:
            take = block["len"]
            cut = smart_cut(script, cursor, take)
            chunk = script[cursor:cut].strip()
            cursor = cut

        results.append(chunk)

    return results

def replace_srt_text_with_script_smart_cut(srt_path: str, script_path: str, out_path: str):
    # SRT 로드
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_text = f.read()

    # Script 로드
    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 1. SRT 파싱 (길이 기준)
    blocks = parse_srt_with_text(srt_text)

    # 2. smart_cut 기반으로 script 분할
    new_texts = replace_by_sentence_length_smart(blocks, script_text)

    # 3. SRT 재구성 (타임스탬프 유지)
    output = []
    for block, text in zip(blocks, new_texts):
        output.append(str(block["idx"]))
        output.append(f"{block['start']} --> {block['end']}")
        output.append(text)
        output.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))

# Experiment 5: 문장 단위 정렬
def split_script_sentences(script_text: str):
    sentences = re.split(r'(?<=[.!?])\s+', script_text.strip())
    return [s.strip() for s in sentences if s.strip()]

def group_blocks_by_script_sentences(blocks, script_sentences, ratio=0.9):
    """
    script 문장 하나에 대해
    SRT block 여러 개를 묶는다
    """
    groups = []
    block_idx = 0

    for sentence in script_sentences:
        target_len = len(sentence)
        acc_len = 0
        group = []

        while block_idx < len(blocks) and acc_len < target_len * ratio:
            group.append(blocks[block_idx])
            acc_len += blocks[block_idx]["len"]
            block_idx += 1

        groups.append((group, sentence))

    return groups

def split_sentence_to_blocks(sentence, blocks):
    """
    하나의 문장을 여러 SRT block에 자연스럽게 분할
    """
    results = []
    cursor = 0
    total_len = len(sentence)

    for i, block in enumerate(blocks):
        if cursor >= total_len:
            results.append("")
            continue

        if i == len(blocks) - 1:
            # 마지막 block은 남은 문장 전부
            chunk = sentence[cursor:].strip()
            cursor = total_len
        else:
            target = block["len"]
            cut = smart_cut(sentence, cursor, target, margin=20)
            chunk = sentence[cursor:cut].strip()
            cursor = cut

        results.append(chunk)

    return results

def cleanup_leading_punctuation(text):
    return re.sub(r"^[,.\s]+", "", text)

def replace_srt_text_by_sentence_alignment(
    srt_path: str,
    script_path: str,
    out_path: str
):
    with open(srt_path, "r", encoding="utf-8") as f:
        srt_text = f.read()

    with open(script_path, "r", encoding="utf-8") as f:
        script_text = f.read()

    # 1. 파싱
    blocks = parse_srt_with_text(srt_text)
    script_sentences = split_script_sentences(script_text)

    # 2. 문장 기준으로 block 묶기
    groups = group_blocks_by_script_sentences(blocks, script_sentences)

    # 3. 재구성
    output = []
    for group_blocks, sentence in groups:
        texts = split_sentence_to_blocks(sentence, group_blocks)

        for block, text in zip(group_blocks, texts):
            clean_text = cleanup_leading_punctuation(text)

            output.append(str(block["idx"]))
            output.append(f"{block['start']} --> {block['end']}")
            output.append(clean_text)
            output.append("")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output))



def audio_to_subs(
    audio_dir: str,
    subs_dir: str,
    method: str = "api_replace", # "api" or "heuristic" or "api_replace"
    scripts_dir: str | None = None
):
    for fname in sorted(os.listdir(audio_dir)):
        if not fname.endswith(".mp3"):
            continue

        base = fname.replace(".mp3", "")
        audio_path = os.path.join(audio_dir, fname)
        out_path = os.path.join(subs_dir, base + ".srt")

        # Whisper로 SRT 생성
        if method in ("api", "api_replace"):
            make_srt_api(audio_path, out_path)

        # Heuristic 방식
        if method == "heuristic":
            if scripts_dir is None:
                raise ValueError("heuristic 방식은 scripts_dir가 필요합니다")
            
            script_path = os.path.join(scripts_dir, base + ".txt")
            make_srt_from_script(script_path, audio_path, out_path)

        elif method == "api_replace":
            if scripts_dir is None:
                raise ValueError("api_replace 방식은 scripts_dir가 필요합니다")
            
            script_path = os.path.join(scripts_dir, base + ".txt")

            tmp_path = out_path + ".tmp"

            replace_srt_text_by_sentence_alignment(
                srt_path=out_path,
                script_path=script_path,
                out_path=tmp_path
            )
        
            backup_path = out_path.replace(".srt", "_backup.srt")
            os.replace(out_path, backup_path)
            os.replace(tmp_path, out_path)

        elif method not in ("api", "heuristic"):
            raise ValueError(f"알 수 없는 method: {method}")

        print(f"[subs] {out_path} 생성 완료")


def main():
    for fname in os.listdir(AUDIO_DIR):
        if not fname.endswith(".mp3"):
            continue

        base = fname.replace(".mp3", "")
        audio_path = os.path.join(AUDIO_DIR, base + ".mp3")
        out_path = os.path.join(SUB_DIR, base + ".srt")

        make_srt_api(audio_path, out_path)
        print(f"[OK] {out_path} 생성")

if __name__ == "__main__":
    main()