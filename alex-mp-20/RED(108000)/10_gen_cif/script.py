#!/usr/bin/env python3
import os
import re
import glob
import uuid
import shutil
import argparse
from collections import Counter, defaultdict

import pandas as pd
from ase.io import read as ase_read


# -----------------------------
# (1) CSV A열 문자열에서: (id, formula) 파싱
# -----------------------------
ID_RE = re.compile(r"^\s*(\d+)\s+")
FORMULA_RE = re.compile(r"-\s*([A-Za-z0-9\s]+?)\s*(?:\(|$)")
TOKEN_RE = re.compile(r"([A-Z][a-z]?)(\d*)")

def parse_entry_id_and_formula(text: str):
    if text is None or (isinstance(text, float) and pd.isna(text)):
        return None, None

    s = str(text)

    m_id = ID_RE.search(s)
    entry_id = int(m_id.group(1)) if m_id else None

    m_f = FORMULA_RE.search(s)
    if not m_f:
        return entry_id, None

    formula = m_f.group(1).strip().replace(" ", "")
    return entry_id, formula


def formula_to_signature(formula: str):
    if not formula:
        return None

    counts = Counter()
    pos = 0
    for m in TOKEN_RE.finditer(formula):
        el, num = m.group(1), m.group(2)
        counts[el] += int(num) if num else 1
        pos = m.end()

    if pos != len(formula):
        return None

    return tuple(sorted(counts.items(), key=lambda x: x[0]))


# -----------------------------
# (2) 구조파일에서 원소/개수 시그니처 만들기
# -----------------------------
def file_to_signature(path: str):
    try:
        atoms = ase_read(path, index=0)
    except Exception as e:
        return None, f"READ_FAIL: {e}"

    syms = atoms.get_chemical_symbols()
    counts = Counter(syms)
    sig = tuple(sorted(((k, int(v)) for k, v in counts.items()), key=lambda x: x[0]))
    return sig, None


def sig_to_formula_string(sig):
    out = []
    for el, n in sig:
        out.append(el + (str(n) if n != 1 else ""))
    return "".join(out)


def safe_copy(src, dst_dir):
    """dst_dir로 안전하게 '복사' (동일 파일명 충돌 시 uuid suffix 붙임)"""
    os.makedirs(dst_dir, exist_ok=True)
    base = os.path.basename(src)
    dst = os.path.join(dst_dir, base)
    if not os.path.exists(dst):
        shutil.copy2(src, dst)
        return dst

    root, ext = os.path.splitext(base)
    for _ in range(1000):
        cand = os.path.join(dst_dir, f"{root}__dup__{uuid.uuid4().hex[:8]}{ext}")
        if not os.path.exists(cand):
            shutil.copy2(src, cand)
            return cand

    raise RuntimeError(f"Too many name collisions while copying: {src}")


# -----------------------------
# (3) 메인: 중복은 복사 + (CSV '몇번째 행' 저장) + 매칭 -> 리네임
# -----------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="metrics_per_structure.csv", help="metrics_per_structure.csv 경로")
    ap.add_argument("--col", default=None, help="A열 컬럼명(없으면 첫 번째 컬럼 사용)")
    ap.add_argument("--struct_dir", default=".", help="gen_xxxx 파일들이 있는 폴더")
    ap.add_argument("--pattern", default="gen_*", help="구조파일 glob 패턴 (예: 'gen_*.cif' 또는 'gen_*')")
    ap.add_argument("--apply", action="store_true", help="실제로 복사/리네임 적용 (기본은 dry-run)")
    ap.add_argument("--use_row_index_if_no_id", action="store_true",
                    help="A열 맨앞 숫자(id) 파싱 실패 시 csv 행번호를 target id로 사용")
    ap.add_argument("--dup_dir", default="_DUPLICATES",
                    help="중복 구조파일을 보낼 폴더명 (struct_dir 하위). 기본: _DUPLICATES")
    ap.add_argument("--dup_report_csv", default="dup_report.csv",
                    help="중복 그룹(조성)별 CSV 행번호 + 파일 목록 리포트 CSV 저장 경로")
    args = ap.parse_args()

    # ✅ Done 직전에 출력할 "중복 참고 목록(전부)" 라인들
    dup_ref_lines = []

    # 1) CSV 로드
    df = pd.read_csv(args.csv)
    if args.col is None:
        a_col = df.columns[0]
    else:
        a_col = args.col
        if a_col not in df.columns:
            raise ValueError(f"--col '{a_col}' 이(가) CSV 컬럼에 없습니다. 실제 컬럼명: {list(df.columns)}")

    # 2) CSV에서 (target_id -> sig) 만들기 + sig -> [csv rows info]
    target_sig = {}
    bad_rows = []

    # sig별로 CSV 행번호 저장
    # row_1based: 데이터 행 기준(1부터)
    # line_in_file: 헤더 포함 CSV 파일 라인 번호(엑셀 row 느낌)
    csv_sig_to_rows = defaultdict(list)

    for i, text in enumerate(df[a_col].tolist()):
        row_1based = i + 1
        line_in_file = i + 2  # header 1줄 있다고 가정

        entry_id, formula = parse_entry_id_and_formula(text)
        if entry_id is None and args.use_row_index_if_no_id:
            entry_id = i

        sig = formula_to_signature(formula) if formula else None
        if entry_id is None or sig is None:
            bad_rows.append((i, entry_id, formula, text))
            continue

        target_sig[entry_id] = sig
        csv_sig_to_rows[sig].append({
            "row_1based": row_1based,
            "line_in_file": line_in_file,
            "entry_id": entry_id,
            "a_value": str(text),
        })

    # CSV 중복(조성 기준)
    csv_duplicates = {sig: rows for sig, rows in csv_sig_to_rows.items() if len(rows) > 1}

    # 3) 구조파일 목록 -> (sig -> [files])
    struct_glob = os.path.join(args.struct_dir, args.pattern)
    files = sorted(glob.glob(struct_glob))
    if not files:
        raise FileNotFoundError(f"구조파일을 못 찾았습니다: {struct_glob}")

    sig_to_files = defaultdict(list)
    read_fail = []
    for fp in files:
        sig, err = file_to_signature(fp)
        if err:
            read_fail.append((fp, err))
            continue
        sig_to_files[sig].append(fp)

    # 4) ✅ 중복(sig에 파일 2개 이상)인 그룹은 dup_dir로 전부 복사
    dup_dir_path = os.path.join(args.struct_dir, args.dup_dir)
    dup_groups = 0
    dup_files_total = 0
    report_rows = []

    for sig, fps in list(sig_to_files.items()):
        if len(fps) <= 1:
            continue

        dup_groups += 1
        fps_sorted = sorted(fps)
        dup_files_total += len(fps_sorted)

        formula_sorted = sig_to_formula_string(sig)

        # CSV에서 해당 sig 행번호 목록(서로 다른 행만)
        csv_rows_info_all = sorted(csv_sig_to_rows.get(sig, []), key=lambda d: (d["row_1based"], d["line_in_file"]))
        seen = set()
        csv_rows_info = []
        for d in csv_rows_info_all:
            key = (d["row_1based"], d["line_in_file"])
            if key in seen:
                continue
            seen.add(key)
            csv_rows_info.append(d)

        csv_row_nums = [d["row_1based"] for d in csv_rows_info]

        # 복사(dry-run이면 경로만 예측)
        copied_paths = []
        if args.apply:
            for src in fps_sorted:
                dst = safe_copy(src, dup_dir_path)
                copied_paths.append(dst)
        else:
            copied_paths = [os.path.join(dup_dir_path, os.path.basename(x)) for x in fps_sorted]

        # ✅ Done 직전에 출력할 "중복 전부" 라인 저장 (잘리지 않음)
        dup_ref_lines.append(f"\n[DUPLICATE GROUP] {formula_sorted}")
        if csv_row_nums:
            dup_ref_lines.append(f"  CSV rows (1-based): {', '.join(map(str, csv_row_nums))}")
        else:
            dup_ref_lines.append("  CSV rows (1-based): (none)")
        for src in fps_sorted:
            dup_ref_lines.append(f"  {os.path.basename(src)}  ->  {args.dup_dir}/")

        # 리포트 CSV 저장(파일 단위)
        for src, dst in zip(fps_sorted, copied_paths):
            report_rows.append({
                "composition_signature": str(sig),
                "composition_formula_sorted": formula_sorted,
                "csv_row_1based_list": ",".join(map(str, csv_row_nums)) if csv_row_nums else "",
                "src_file": os.path.basename(src),
                "src_path": os.path.abspath(src),
                "dup_copy_path": os.path.abspath(dst),
                "applied": bool(args.apply),
            })

    # 5) 기본 출력
    print("=== PARSE ISSUES (CSV rows) ===")
    if bad_rows:
        for (i, entry_id, formula, raw) in bad_rows[:50]:
            print(f"  row_index0={i} entry_id={entry_id} formula={formula} raw={raw} -> PARSE_FAIL")
        if len(bad_rows) > 50:
            print(f"  ... ({len(bad_rows)-50} more)")
    else:
        print("  (none)")

    print("\n=== READ FAIL (structure files) ===")
    if read_fail:
        for fp, err in read_fail[:50]:
            print(f"  {fp} -> {err}")
        if len(read_fail) > 50:
            print(f"  ... ({len(read_fail)-50} more)")
    else:
        print("  (none)")

    print("\n=== DUPLICATE STRUCTURES SUMMARY ===")
    if dup_groups == 0:
        print("  (no duplicates)")
    else:
        print(f"  duplicate composition groups: {dup_groups}")
        print(f"  duplicate files (copied): {dup_files_total}")
        print(f"  dup folder: {os.path.abspath(dup_dir_path)}")

    print("\n=== DUPLICATE COMPOSITIONS IN CSV (A column) ===")
    if csv_duplicates:
        for sig, rows in sorted(csv_duplicates.items(), key=lambda x: (-len(x[1]), sig_to_formula_string(x[0]))):
            row_nums = sorted([d["row_1based"] for d in rows])
            print(f"  {sig_to_formula_string(sig)}  |  count={len(rows)}  |  csv_rows_1based={row_nums}")
    else:
        print("  (none)")

    # 리포트 CSV 저장
    if args.dup_report_csv:
        pd.DataFrame(report_rows).to_csv(args.dup_report_csv, index=False)
        print(f"\n=== DUP REPORT SAVED ===\n  -> {os.path.abspath(args.dup_report_csv)}")

    if not args.apply:
        print("\n(dry-run) 실제 복사/리네임을 적용하려면 --apply 옵션을 붙이세요.")

    # 6) CSV target_id 순서대로 매칭 (기존 로직 유지)
    used = set()
    mapping = {}
    missing = []
    ambiguous = []

    for target_id in sorted(target_sig.keys()):
        sig = target_sig[target_id]
        candidates = [f for f in sig_to_files.get(sig, []) if f not in used]
        if len(candidates) == 0:
            missing.append(target_id)
            continue
        if len(candidates) > 1:
            ambiguous.append((target_id, candidates))
        chosen = candidates[0]
        used.add(chosen)
        mapping[target_id] = chosen

    print("\n=== MISSING MATCH (target_id with no file) ===")
    if missing:
        print("  ", missing[:100], "..." if len(missing) > 100 else "")
    else:
        print("  (none)")

    print("\n=== AMBIGUOUS (multiple unused files match same composition) ===")
    if ambiguous:
        for tid, cands in ambiguous[:30]:
            print(f"  target_id={tid} ({sig_to_formula_string(target_sig[tid])}) -> {len(cands)} candidates (showing up to 5):")
            for c in cands[:5]:
                print(f"    - {os.path.basename(c)}")
        if len(ambiguous) > 30:
            print(f"  ... ({len(ambiguous)-30} more)")
    else:
        print("  (none)")

    # 7) 리네임 계획
    print("\n=== PREVIEW RENAME PLAN ===")
    plan = []
    for tid in sorted(mapping.keys()):
        src = mapping[tid]
        base, ext = os.path.splitext(os.path.basename(src))
        ext = ext if ext else ""
        dst = os.path.join(os.path.dirname(src), f"gen_{tid}{ext}")
        plan.append((src, dst))
        print(f"  {os.path.basename(src)}  ->  {os.path.basename(dst)}")

    if not args.apply:
        return

    # 8) 충돌 방지: 임시 이름으로 1차 변경
    print("\n=== APPLY RENAME ===")
    tmp_map = {}
    for src, dst in plan:
        if os.path.abspath(src) == os.path.abspath(dst):
            continue
        tmp = os.path.join(os.path.dirname(src), f"__tmp__{uuid.uuid4().hex}__")
        os.rename(src, tmp)
        tmp_map[tmp] = dst

    # 9) 임시 -> 최종
    for tmp, dst in tmp_map.items():
        if os.path.exists(dst):
            raise FileExistsError(f"목적지 파일이 이미 존재합니다(충돌): {dst}")
        os.rename(tmp, dst)

    # ✅ Done 직전에 "중복 참고(전부)" 출력
    print("\n=== DUPLICATES (REFERENCE, ALL) ===")
    if dup_ref_lines:
        for line in dup_ref_lines:
            print(line)
    else:
        print("  (none)")

    print("Done.")


if __name__ == "__main__":
    main()
