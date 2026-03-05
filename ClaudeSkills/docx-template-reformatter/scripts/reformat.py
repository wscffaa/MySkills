#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Docx Template Reformatter

目标：将源论文 .docx 的内容注入目标模板 .docx，尽量复刻模板的样式体系与分节结构（如单栏→双栏）。
实现方式：基于 OOXML（document.xml / rels / content-types）做确定性变换，避免 python-docx 对公式等结构的缺口。
"""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import sys
import tempfile
import zipfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from lxml import etree
except Exception as e:  # pragma: no cover
    raise SystemExit(
        "缺少依赖：lxml。请先安装（例如：pip install lxml），或在具备 lxml 的环境中运行。\n"
        f"原始错误：{e}"
    )


NS: Dict[str, str] = {
    "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main",
    "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
    "rel": "http://schemas.openxmlformats.org/package/2006/relationships",
}
CT_NS = "http://schemas.openxmlformats.org/package/2006/content-types"


def parse_xml(path: Path) -> etree._ElementTree:
    return etree.parse(str(path), etree.XMLParser(remove_blank_text=False, recover=True))


def write_xml(tree: etree._ElementTree, path: Path) -> None:
    path.write_bytes(
        etree.tostring(tree, xml_declaration=True, encoding="UTF-8", pretty_print=False)
    )


def unzip_docx(docx: Path, out_dir: Path) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(docx), "r") as zf:
        zf.extractall(str(out_dir))


def zip_docx(unpacked_dir: Path, out_docx: Path) -> None:
    out_docx.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(str(out_docx), "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(unpacked_dir.rglob("*")):
            if p.is_dir():
                continue
            rel = p.relative_to(unpacked_dir).as_posix()
            zf.write(str(p), rel)


def p_text(p: etree._Element) -> str:
    return "".join(t.text or "" for t in p.xpath(".//w:t", namespaces=NS)).strip()


def normalize_text(s: str) -> str:
    s = s.replace("\u3000", " ")
    return re.sub(r"\s+", "", s).strip()


def is_englishish(s: str) -> bool:
    letters = sum(1 for ch in s if ("A" <= ch <= "Z") or ("a" <= ch <= "z"))
    return letters >= max(10, len(s) // 3)


def get_p_style_id(p: etree._Element) -> Optional[str]:
    ps = p.find("w:pPr/w:pStyle", namespaces=NS)
    return ps.get(f"{{{NS['w']}}}val") if ps is not None else None


def set_p_style_id(p: etree._Element, style_id: str) -> None:
    ppr = p.find("w:pPr", namespaces=NS)
    if ppr is None:
        ppr = etree.Element(f"{{{NS['w']}}}pPr")
        p.insert(0, ppr)
    ps = ppr.find("w:pStyle", namespaces=NS)
    if ps is None:
        ps = etree.SubElement(ppr, f"{{{NS['w']}}}pStyle")
    ps.set(f"{{{NS['w']}}}val", style_id)


def replace_para_text(p: etree._Element, new_text: str) -> None:
    # 删除所有 run 并写入单 run 文本；保持段落 pPr 不变
    for r in list(p.findall("w:r", namespaces=NS)):
        p.remove(r)
    r = etree.SubElement(p, f"{{{NS['w']}}}r")
    t = etree.SubElement(r, f"{{{NS['w']}}}t")
    # Word 对前后空格敏感；需要保留时用 xml:space，但此处不处理，交给模板样式
    t.text = new_text


def load_paragraph_style_name_map(styles_xml: Path) -> Dict[str, str]:
    """读取 styles.xml，返回 paragraph 样式 styleId -> name 映射。"""

    if not styles_xml.is_file():
        return {}
    tree = parse_xml(styles_xml)
    out: Dict[str, str] = {}
    for st in tree.getroot().xpath(".//w:style[@w:type='paragraph']", namespaces=NS):
        sid = st.get(f"{{{NS['w']}}}styleId")
        if not sid:
            continue
        name_el = st.find("w:name", namespaces=NS)
        name = name_el.get(f"{{{NS['w']}}}val") if name_el is not None else ""
        out[sid] = name or ""
    return out


def guess_style_id_by_name(
    style_name_by_id: Dict[str, str],
    *,
    prefer_exact: Sequence[str],
    contains_any: Sequence[str],
) -> Optional[str]:
    """根据样式 name 进行高置信度猜测；若不唯一则返回 None。"""

    if not style_name_by_id:
        return None

    def norm(s: str) -> str:
        return s.strip().lower()

    prefer_exact_n = [norm(s) for s in prefer_exact if s.strip()]
    contains_any_n = [norm(s) for s in contains_any if s.strip()]

    # 精确匹配优先
    exact_hits = [
        sid
        for sid, name in style_name_by_id.items()
        if norm(name) in set(prefer_exact_n)
    ]
    exact_hits = list(dict.fromkeys(exact_hits))
    if len(exact_hits) == 1:
        return exact_hits[0]

    # contains 匹配
    hits: List[str] = []
    for sid, name in style_name_by_id.items():
        n = norm(name)
        if any(k in n for k in contains_any_n):
            hits.append(sid)
    hits = list(dict.fromkeys(hits))
    return hits[0] if len(hits) == 1 else None


def strip_descendants(el: etree._Element, xpath_expr: str) -> None:
    for node in el.xpath(xpath_expr, namespaces=NS):
        parent = node.getparent()
        if parent is not None:
            parent.remove(node)


def strip_p_styles(el: etree._Element) -> None:
    """移除插入内容中的段落样式引用（w:pStyle），避免把源文档的样式体系带入模板。"""

    paras = list(el.xpath(".//w:p", namespaces=NS))
    if el.tag == f"{{{NS['w']}}}p":
        paras.insert(0, el)

    for p in paras:
        ppr = p.find("w:pPr", namespaces=NS)
        if ppr is None:
            continue
        ps = ppr.find("w:pStyle", namespaces=NS)
        if ps is not None:
            ppr.remove(ps)


def strip_para_direct_formatting(p: etree._Element) -> None:
    """移除段落级“直接格式”，让模板样式主导对齐/缩进/制表位等关键版式。"""

    ppr = p.find("w:pPr", namespaces=NS)
    if ppr is None:
        return
    for tag in ("jc", "tabs", "ind", "spacing", "rPr"):
        el = ppr.find(f"w:{tag}", namespaces=NS)
        if el is not None:
            ppr.remove(el)


def apply_para_style(p: etree._Element, style_id: str, *, strip_numpr: bool = True) -> None:
    set_p_style_id(p, style_id)
    strip_para_direct_formatting(p)
    if not strip_numpr:
        return
    ppr = p.find("w:pPr", namespaces=NS)
    if ppr is None:
        return
    numpr = ppr.find("w:numPr", namespaces=NS)
    if numpr is not None:
        ppr.remove(numpr)


def collect_used_rids(el: etree._Element) -> set[str]:
    rids: set[str] = set()
    for node in el.xpath(".//*[@r:embed or @r:id or @r:link]", namespaces=NS):
        for attr in (f"{{{NS['r']}}}embed", f"{{{NS['r']}}}id", f"{{{NS['r']}}}link"):
            v = node.get(attr)
            if v:
                rids.add(v)
    return rids


def rewrite_rids(el: etree._Element, rid_map: Dict[str, str]) -> None:
    for node in el.xpath(".//*[@r:embed or @r:id or @r:link]", namespaces=NS):
        for attr in (f"{{{NS['r']}}}embed", f"{{{NS['r']}}}id", f"{{{NS['r']}}}link"):
            v = node.get(attr)
            if v and v in rid_map:
                node.set(attr, rid_map[v])


def ensure_ct_default(ct_root: etree._Element, ext: str, ctype: str) -> None:
    for d in ct_root.findall(f"{{{CT_NS}}}Default"):
        if d.get("Extension") == ext:
            return
    d = etree.SubElement(ct_root, f"{{{CT_NS}}}Default")
    d.set("Extension", ext)
    d.set("ContentType", ctype)


def ensure_ct_override(ct_root: etree._Element, part_name: str, ctype: str) -> None:
    for o in ct_root.findall(f"{{{CT_NS}}}Override"):
        if o.get("PartName") == part_name:
            return
    o = etree.SubElement(ct_root, f"{{{CT_NS}}}Override")
    o.set("PartName", part_name)
    o.set("ContentType", ctype)


def max_rid_num(rels_path: Path) -> int:
    rels = parse_xml(rels_path)
    nums: List[int] = []
    for rel in rels.getroot().findall(f"{{{NS['rel']}}}Relationship"):
        rid = rel.get("Id") or ""
        m = re.match(r"rId(\d+)$", rid)
        if m:
            nums.append(int(m.group(1)))
    return max(nums) if nums else 0


def merge_relationships_and_parts(
    *,
    src_root: Path,
    out_root: Path,
    inserted: Sequence[etree._Element],
    rid_start: int,
) -> Dict[str, str]:
    src_rels_path = src_root / "word/_rels/document.xml.rels"
    out_rels_path = out_root / "word/_rels/document.xml.rels"
    src_ct_path = src_root / "[Content_Types].xml"
    out_ct_path = out_root / "[Content_Types].xml"

    src_rels = parse_xml(src_rels_path)
    out_rels = parse_xml(out_rels_path)
    out_root_el = out_rels.getroot()

    rel_by_id = {
        rel.get("Id"): rel
        for rel in src_rels.getroot().findall(f"{{{NS['rel']}}}Relationship")
        if rel.get("Id")
    }

    used: set[str] = set()
    for el in inserted:
        used |= collect_used_rids(el)

    src_ct = parse_xml(src_ct_path)
    src_override = {
        o.get("PartName"): o.get("ContentType")
        for o in src_ct.getroot().findall(f"{{{CT_NS}}}Override")
        if o.get("PartName") and o.get("ContentType")
    }
    out_ct = parse_xml(out_ct_path)
    out_ct_root = out_ct.getroot()

    rid_map: Dict[str, str] = {}
    n = rid_start

    def alloc() -> str:
        nonlocal n
        rid = f"rId{n}"
        n += 1
        return rid

    def prefixed_target(target: str) -> str:
        target = target.replace("\\", "/")
        p = Path(target)
        if p.parts and p.parts[0] in {"media", "embeddings"}:
            return str(Path(p.parts[0]) / ("src_" + p.name))
        return str(p.parent / ("src_" + p.name)) if p.name else target

    for old in sorted(used):
        rel = rel_by_id.get(old)
        if rel is None:
            continue
        new = alloc()
        rid_map[old] = new

        new_rel = etree.SubElement(out_root_el, f"{{{NS['rel']}}}Relationship")
        for k, v in rel.attrib.items():
            new_rel.set(k, v)
        new_rel.set("Id", new)

        target = rel.get("Target") or ""
        mode = rel.get("TargetMode") or ""
        if mode == "External" or not target or target.startswith("http") or "://" in target:
            continue

        tgt2 = prefixed_target(target)
        new_rel.set("Target", tgt2)

        src_part = (src_root / "word" / target).resolve()
        out_part = (out_root / "word" / tgt2).resolve()
        out_part.parent.mkdir(parents=True, exist_ok=True)
        if src_part.exists() and not out_part.exists():
            shutil.copy2(src_part, out_part)

        ext = out_part.suffix.lower().lstrip(".")
        if ext == "emf":
            ensure_ct_default(out_ct_root, "emf", "image/x-emf")
        elif ext == "wmf":
            ensure_ct_default(out_ct_root, "wmf", "image/x-wmf")
        elif ext == "png":
            ensure_ct_default(out_ct_root, "png", "image/png")
        elif ext in {"jpg", "jpeg"}:
            ensure_ct_default(out_ct_root, ext, "image/jpeg")
        elif ext == "gif":
            ensure_ct_default(out_ct_root, "gif", "image/gif")
        else:
            src_part_name = "/word/" + target.replace("\\", "/")
            out_part_name = "/word/" + tgt2.replace("\\", "/")
            ctype = src_override.get(src_part_name)
            if ctype:
                ensure_ct_override(out_ct_root, out_part_name, ctype)

    write_xml(out_rels, out_rels_path)
    write_xml(out_ct, out_ct_path)
    return rid_map


def sanity_check_unpacked_docx(unpacked_dir: Path) -> List[str]:
    errs: List[str] = []
    doc_xml = unpacked_dir / "word/document.xml"
    rels_xml = unpacked_dir / "word/_rels/document.xml.rels"
    if not doc_xml.is_file():
        return [f"missing {doc_xml}"]
    if not rels_xml.is_file():
        return [f"missing {rels_xml}"]

    doc = parse_xml(doc_xml)
    used = collect_used_rids(doc.getroot())

    rels = parse_xml(rels_xml)
    rel_elems = rels.getroot().findall(f"{{{NS['rel']}}}Relationship")
    rel_ids = {r.get("Id") for r in rel_elems if r.get("Id")}
    missing = sorted(used - rel_ids)
    if missing:
        errs.append(f"document.xml 引用未定义关系: {', '.join(missing[:30])}")

    for r in rel_elems:
        target = r.get("Target") or ""
        mode = r.get("TargetMode") or ""
        if mode == "External" or target.startswith("http") or "://" in target:
            continue
        if not target:
            continue
        part = (unpacked_dir / "word" / target).resolve()
        if not part.exists():
            errs.append(f"关系目标缺失: {r.get('Id')} -> word/{target}")

    return errs


def find_first_para_idx_by_regex(
    body: etree._Element, regexes: Sequence[str]
) -> Optional[int]:
    children = list(body)
    content_children = children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
    pats = [re.compile(r) for r in regexes]
    for i, el in enumerate(content_children):
        if el.tag != f"{{{NS['w']}}}p":
            continue
        t = normalize_text(p_text(el))
        for pat in pats:
            if pat.search(t):
                return i
    return None


@dataclass(frozen=True)
class SectionInfo:
    start: int
    end: int
    cols_num: int
    sectpr_source: str  # "p" or "body"
    marker_idx: Optional[int]  # when sectpr_source == "p"


def sect_cols_num(sect: Optional[etree._Element]) -> int:
    if sect is None:
        return 1
    cols = sect.find("w:cols", namespaces=NS)
    if cols is None:
        return 1
    v = cols.get(f"{{{NS['w']}}}num")
    return int(v) if v and v.isdigit() else 1


def compute_sections(body: etree._Element) -> List[SectionInfo]:
    children = list(body)
    has_body_sect = bool(children and children[-1].tag == f"{{{NS['w']}}}sectPr")
    content_children = children[:-1] if has_body_sect else children

    markers: List[Tuple[int, etree._Element]] = []
    for i, el in enumerate(content_children):
        if el.tag != f"{{{NS['w']}}}p":
            continue
        sect = el.find("w:pPr/w:sectPr", namespaces=NS)
        if sect is not None:
            markers.append((i, sect))

    out: List[SectionInfo] = []
    start = 0
    for end_idx, sect in markers:
        out.append(
            SectionInfo(
                start=start,
                end=end_idx,
                cols_num=sect_cols_num(sect),
                sectpr_source="p",
                marker_idx=end_idx,
            )
        )
        start = end_idx + 1

    body_sect = body.find("w:sectPr", namespaces=NS)
    if body_sect is not None:
        last_end = len(content_children) - 1 if content_children else -1
        out.append(
            SectionInfo(
                start=start,
                end=last_end,
                cols_num=sect_cols_num(body_sect),
                sectpr_source="body",
                marker_idx=None,
            )
        )
    return out


def find_section_for_idx(sections: Sequence[SectionInfo], idx: int) -> Optional[SectionInfo]:
    for s in sections:
        if s.start <= idx <= s.end:
            return s
    return None


def make_empty_para_from_para(p: etree._Element, *, drop_sectpr: bool) -> etree._Element:
    cp = copy.deepcopy(p)
    ppr = cp.find("w:pPr", namespaces=NS)
    if ppr is not None and drop_sectpr:
        sect = ppr.find("w:sectPr", namespaces=NS)
        if sect is not None:
            ppr.remove(sect)
    for ch in list(cp):
        if ch.tag != f"{{{NS['w']}}}pPr":
            cp.remove(ch)
    return cp


def extract_body_section_end_marker(
    body: etree._Element, body_start_idx: int
) -> Optional[Tuple[etree._Element, etree._Element, SectionInfo]]:
    sections = compute_sections(body)
    sec = find_section_for_idx(sections, body_start_idx)
    if sec is None:
        return None
    if sec.sectpr_source != "p" or sec.marker_idx is None:
        return None

    children = list(body)
    content_children = children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
    marker_p = content_children[sec.marker_idx]
    # 分节符段落本身属于该 section；用空段落保留其 pPr/sectPr，避免引入示例正文文本。
    break_p = make_empty_para_from_para(marker_p, drop_sectpr=False)
    # 在分节符后补一个空段落，作为下一 section 起点（否则部分渲染器会忽略分节切换）。
    post_p = make_empty_para_from_para(marker_p, drop_sectpr=True)
    return break_p, post_p, sec


def extract_doi(text: str) -> Optional[str]:
    m = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Z0-9]+\b", text, re.IGNORECASE)
    return m.group(0) if m else None


def extract_front_matter_from_source(
    doc: etree._ElementTree, *, body_start_idx: int
) -> Dict[str, str]:
    root = doc.getroot()
    body = root.find("w:body", namespaces=NS)
    if body is None:
        return {}

    children = list(body)
    content_children = children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
    paras = [el for el in content_children[: max(0, body_start_idx)] if el.tag == f"{{{NS['w']}}}p"]
    texts = [p_text(p) for p in paras]
    joined = "\n".join(texts)

    fm: Dict[str, str] = {}
    doi = None
    for t in texts[:30]:
        if "doi" in t.lower():
            doi = extract_doi(t) or doi
    fm["doi"] = doi or extract_doi(joined) or ""

    def find_starts(label: str) -> str:
        for t in texts[:80]:
            s = t.strip()
            if s.startswith(label):
                s2 = re.sub(rf"^{re.escape(label)}\s*[:：]?\s*", "", s)
                return s2.strip()
        return ""

    fm["cn_abs"] = find_starts("摘要")
    fm["cn_kw"] = find_starts("关键词")
    fm["class_no"] = find_starts("中图分类号")

    # 英文摘要/关键词常见写法：Abstract / Keywords / Key words
    for t in texts[:120]:
        s = t.strip()
        if re.match(r"^abstract\b", s, re.IGNORECASE):
            fm["en_abs"] = re.sub(r"^abstract\s*[:：]?\s*", "", s, flags=re.IGNORECASE).strip()
            break
    else:
        fm["en_abs"] = ""

    for t in texts[:140]:
        s = t.strip()
        if re.match(r"^key\s*words\b", s, re.IGNORECASE) or re.match(
            r"^keywords\b", s, re.IGNORECASE
        ):
            fm["en_kw"] = re.sub(r"^key\s*words\s*[:：]?\s*", "", s, flags=re.IGNORECASE)
            fm["en_kw"] = re.sub(r"^keywords\s*[:：]?\s*", "", fm["en_kw"], flags=re.IGNORECASE).strip()
            break
    else:
        fm["en_kw"] = ""

    # 标题/作者/单位跨模板差异大：仅做“从文首按常见论文结构”的保守猜测
    blocked = (
        "文章编号",
        "文献标志码",
        "中图分类号",
        "摘要",
        "关键词",
        "abstract",
        "keywords",
        "doi",
    )

    def is_blocked_line(s: str) -> bool:
        ss = s.strip()
        low = ss.lower()
        if not ss:
            return True
        return any(b in ss for b in blocked if b.isupper() or b in ss) or any(b in low for b in blocked if b.islower())

    def is_cn_title_candidate(s: str) -> bool:
        if is_blocked_line(s):
            return False
        if is_englishish(s):
            return False
        # 题名通常较短且不含冒号
        return 6 <= len(s.strip()) <= 60 and "：" not in s and ":" not in s

    cn_title = ""
    cn_title_idx = None
    for i, t in enumerate(texts[:30]):
        if is_cn_title_candidate(t):
            cn_title = t.strip()
            cn_title_idx = i
            break
    fm["cn_title"] = cn_title

    cn_authors = ""
    cn_affil = ""
    if cn_title_idx is not None:
        # 作者：题名后第一段，常含逗号/顿号/上标数字
        for t in texts[cn_title_idx + 1 : cn_title_idx + 6]:
            s = t.strip()
            if not s or is_blocked_line(s) or is_englishish(s):
                continue
            if len(s) <= 80 and ("，" in s or "、" in s or re.search(r"\d", s)):
                cn_authors = s
                break
        # 单位：作者后第一段，常含括号/分号/单位关键词
        start = (cn_title_idx + 1) if not cn_authors else (cn_title_idx + 2)
        for t in texts[start : start + 8]:
            s = t.strip()
            if not s or is_blocked_line(s) or is_englishish(s):
                continue
            if any(k in s for k in ("大学", "学院", "公司", "研究所", "（", "(", ";", "；")):
                cn_affil = s
                break
    fm["cn_authors"] = cn_authors
    fm["cn_affil"] = cn_affil

    # 英文题名/作者/单位：中文单位后连续三段英文占比高的行
    en_title = ""
    en_authors = ""
    en_affil = ""
    search_from = 0
    if cn_affil:
        try:
            search_from = texts.index(cn_affil)
        except ValueError:
            search_from = 0
    for t in texts[search_from : search_from + 40]:
        s = t.strip()
        if not s or is_blocked_line(s):
            continue
        if is_englishish(s) and len(s) <= 180:
            en_title = s
            break
    if en_title:
        try:
            idx = texts.index(en_title)
        except ValueError:
            idx = None
        if idx is not None:
            for t in texts[idx + 1 : idx + 6]:
                s = t.strip()
                if not s or is_blocked_line(s):
                    continue
                if is_englishish(s) and len(s) <= 120:
                    en_authors = s
                    break
            start = (idx + 1) if not en_authors else (idx + 2)
            for t in texts[start : start + 8]:
                s = t.strip()
                if not s or is_blocked_line(s):
                    continue
                if is_englishish(s) and len(s) <= 200:
                    en_affil = s
                    break
    fm["en_title"] = en_title
    fm["en_authors"] = en_authors
    fm["en_affil"] = en_affil
    return fm


def update_template_front_matter(
    out_doc: etree._ElementTree,
    fm: Dict[str, str],
    *,
    tpl_body_start_idx: int,
    overrides: Dict[str, str],
) -> None:
    body = out_doc.getroot().find("w:body", namespaces=NS)
    if body is None:
        return

    children = list(body)
    content_children = children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
    fm_range = content_children[: max(0, tpl_body_start_idx)]

    def val(key: str) -> str:
        v = overrides.get(key)
        if v is not None:
            return v
        return fm.get(key, "")

    doi = val("doi")
    cn_abs = val("cn_abs")
    cn_kw = val("cn_kw")
    class_no = val("class_no")
    en_abs = val("en_abs")
    en_kw = val("en_kw")

    # DOI
    if doi:
        for p in fm_range:
            if p.tag != f"{{{NS['w']}}}p":
                continue
            if "doi" in p_text(p).lower():
                replace_para_text(p, f"DOI:{doi}")
                break

    # 摘要 / 关键词 / 中图分类号
    for p in fm_range:
        if p.tag != f"{{{NS['w']}}}p":
            continue
        t = p_text(p).strip()
        if cn_abs and t.startswith("摘要"):
            replace_para_text(p, f"摘要{cn_abs}")
        elif cn_kw and t.startswith("关键词"):
            replace_para_text(p, f"关键词：{cn_kw}")
        elif class_no and t.startswith("中图分类号"):
            replace_para_text(p, f"中图分类号：{class_no}")

    # 英文 Abstract 可能位于文本框内：在 front matter 范围内扫描 w:txbxContent//w:p
    if en_abs:
        for host_p in fm_range:
            if host_p.tag != f"{{{NS['w']}}}p":
                continue
            for p in host_p.xpath(".//w:txbxContent//w:p", namespaces=NS):
                if re.search(r"\babstract\b", p_text(p), re.IGNORECASE):
                    replace_para_text(p, f"Abstract {en_abs}".strip())
                    break

    if en_kw:
        en_kw2 = re.sub(r"[；;]\s*", ", ", en_kw).strip()
        for p in fm_range:
            if p.tag != f"{{{NS['w']}}}p":
                continue
            t = p_text(p).strip()
            if re.match(r"^keywords\b", t, re.IGNORECASE) or re.match(
                r"^key\s*words\b", t, re.IGNORECASE
            ):
                replace_para_text(p, f"keywords：{en_kw2}")
                break
            for pp in p.xpath(".//w:txbxContent//w:p", namespaces=NS):
                t2 = p_text(pp).strip()
                if re.match(r"^keywords\b", t2, re.IGNORECASE) or re.match(
                    r"^key\s*words\b", t2, re.IGNORECASE
                ):
                    replace_para_text(pp, f"keywords：{en_kw2}")
                    break

    # 中文/英文题名作者单位在不同模板差异较大：仅在 override 或抽取到“明显合理”的值时尝试替换
    cn_title = val("cn_title")
    cn_authors = val("cn_authors")
    cn_affil = val("cn_affil")
    en_title = val("en_title")
    en_authors = val("en_authors")
    en_affil = val("en_affil")

    def ok(v: str) -> bool:
        vv = v.strip()
        return bool(vv) and len(vv) <= 200 and not re.match(r"^0引言$", normalize_text(vv))

    if any(map(ok, [cn_title, cn_authors, cn_affil, en_title, en_authors, en_affil])):
        # 经验规则：DOI 行后 3 段分别为中文题名/作者/单位；英文题名在更靠后、英文占比高的一段
        doi_p_idx = None
        for i, p in enumerate(fm_range):
            if p.tag != f"{{{NS['w']}}}p":
                continue
            if "doi" in p_text(p).lower():
                doi_p_idx = i
                break
        if doi_p_idx is not None:
            seq = [cn_title, cn_authors, cn_affil]
            for off, v in enumerate(seq, start=1):
                if not ok(v):
                    continue
                if doi_p_idx + off < len(fm_range):
                    p = fm_range[doi_p_idx + off]
                    if p.tag == f"{{{NS['w']}}}p":
                        replace_para_text(p, v)

        if ok(en_title):
            en_title_idx = None
            for i, p in enumerate(fm_range):
                if p.tag != f"{{{NS['w']}}}p":
                    continue
                t = p_text(p).strip()
                if is_englishish(t) and len(t) <= 180 and not re.match(
                    r"^(abstract|key\s*words|keywords)\b", t, re.IGNORECASE
                ):
                    replace_para_text(p, en_title)
                    en_title_idx = i
                    break

            # 英文作者与单位：紧随英文题名之后的两段英文行（若能定位到）
            if en_title_idx is not None:
                if ok(en_authors):
                    # 优先替换占位符（如 XXXX）
                    replaced = False
                    for j in range(en_title_idx + 1, min(len(fm_range), en_title_idx + 6)):
                        p = fm_range[j]
                        if p.tag != f"{{{NS['w']}}}p":
                            continue
                        t = p_text(p).strip()
                        nt = normalize_text(t)
                        if re.fullmatch(r"X{2,}", nt, flags=re.IGNORECASE) or "XXXX" in t:
                            replace_para_text(p, en_authors)
                            replaced = True
                            break
                    if not replaced:
                        for j in range(en_title_idx + 1, min(len(fm_range), en_title_idx + 6)):
                            p = fm_range[j]
                            if p.tag != f"{{{NS['w']}}}p":
                                continue
                            t = p_text(p).strip()
                            if is_englishish(t) and len(t) <= 120 and "University" not in t:
                                replace_para_text(p, en_authors)
                                break
                if ok(en_affil):
                    for j in range(en_title_idx + 1, min(len(fm_range), en_title_idx + 8)):
                        p = fm_range[j]
                        if p.tag != f"{{{NS['w']}}}p":
                            continue
                        t = p_text(p).strip()
                        # 单位行往往更长且包含括号/China/University 等
                        if is_englishish(t) and len(t) <= 220:
                            if any(k in t for k in ("University", "College", "School", "China", "(", "）", ")")):
                                replace_para_text(p, en_affil)
                                break


def discover_template_style_ids(
    body: etree._Element,
    *,
    tpl_body_start_idx: int,
    style_name_by_id: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    children = list(body)
    content_children = children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
    out: Dict[str, str] = {}

    # h1：正文起点标题样式（如 0引言）
    if 0 <= tpl_body_start_idx < len(content_children):
        p = content_children[tpl_body_start_idx]
        if p.tag == f"{{{NS['w']}}}p":
            sid = get_p_style_id(p)
            if sid:
                out["h1"] = sid

    # h2：形如 1.1 的标题样式
    for el in content_children[tpl_body_start_idx : tpl_body_start_idx + 200]:
        if el.tag != f"{{{NS['w']}}}p":
            continue
        t = normalize_text(p_text(el))
        if re.match(r"^\d+\.\d+", t):
            sid = get_p_style_id(el)
            if sid:
                out["h2"] = sid
            break

    # equation_number：形如（1）
    for el in content_children[tpl_body_start_idx : tpl_body_start_idx + 400]:
        if el.tag != f"{{{NS['w']}}}p":
            continue
        t = normalize_text(p_text(el))
        if re.match(r"^（\d+）$", t) or re.match(r"^\(\d+\)$", t):
            sid = get_p_style_id(el)
            if sid:
                out["equation_number"] = sid
            break

    # fig_caption：图/表题（若模板包含样例）
    for el in content_children[tpl_body_start_idx : tpl_body_start_idx + 500]:
        if el.tag != f"{{{NS['w']}}}p":
            continue
        t = normalize_text(p_text(el))
        if re.match(r"^图\d+", t) or re.match(r"^Fig\.?\d+", t, re.IGNORECASE):
            sid = get_p_style_id(el)
            if sid:
                out["fig_caption"] = sid
            break

    # ref_item：参考文献条目（若模板包含样例）
    for el in content_children:
        if el.tag != f"{{{NS['w']}}}p":
            continue
        t = normalize_text(p_text(el))
        if re.match(r"^\[\d+\]", t):
            sid = get_p_style_id(el)
            if sid:
                out["ref_item"] = sid
            break

    # Fallback：从 styles.xml 的样式 name 猜测（仅在唯一命中时生效）
    style_name_by_id = style_name_by_id or {}
    if "equation_number" not in out:
        sid = guess_style_id_by_name(
            style_name_by_id,
            prefer_exact=["公式", "equation"],
            contains_any=["公式", "equation"],
        )
        if sid:
            out["equation_number"] = sid
    if "fig_caption" not in out:
        sid = guess_style_id_by_name(
            style_name_by_id,
            prefer_exact=["图名", "图题", "caption"],
            contains_any=["图名", "图题", "caption", "figure"],
        )
        if sid:
            out["fig_caption"] = sid
    if "ref_item" not in out:
        sid = guess_style_id_by_name(
            style_name_by_id,
            prefer_exact=["参文", "reference"],
            contains_any=["参文", "reference"],
        )
        if sid:
            out["ref_item"] = sid
    if "h2" not in out:
        sid = guess_style_id_by_name(
            style_name_by_id,
            prefer_exact=["heading 4", "标题 2", "二级标题"],
            contains_any=["heading 4", "标题 2", "二级标题", "subheading"],
        )
        if sid:
            out["h2"] = sid

    return out


def apply_body_styles(
    body: etree._Element, *, start_idx: int, style_ids: Dict[str, str]
) -> None:
    children = list(body)
    content_children = children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
    end_idx = len(content_children)
    for el in content_children[start_idx:end_idx]:
        if el.tag != f"{{{NS['w']}}}p":
            continue
        raw = p_text(el).strip()
        if not raw:
            continue
        t = normalize_text(raw)

        if "equation_number" in style_ids and (
            re.match(r"^（\d+）$", t) or re.match(r"^\(\d+\)$", t)
        ):
            apply_para_style(el, style_ids["equation_number"], strip_numpr=True)
            continue

        if "fig_caption" in style_ids and (
            re.match(r"^图\d+", t) or re.match(r"^Fig\.?\d+", t, re.IGNORECASE)
        ):
            apply_para_style(el, style_ids["fig_caption"], strip_numpr=True)
            continue

        # 标题层级：保守处理，仅对明显编号段落应用
        if "h2" in style_ids and re.match(r"^\d+\.\d+", t):
            apply_para_style(el, style_ids["h2"], strip_numpr=True)
            continue
        if (
            "h1" in style_ids
            and not re.match(r"^\d+\.\d+", t)
            and re.match(r"^\d{1,2}(?!\d)", t)
            and not re.match(r"^\d{1,2}[)）]", t)
        ):
            # 仅对“1~2 位数字”开头的段落应用，避免误伤年份/数据行；同时排除列表项 1)/1）
            apply_para_style(el, style_ids["h1"], strip_numpr=True)
            continue

        if "ref_item" in style_ids and re.match(r"^\[\d+\]", t):
            apply_para_style(el, style_ids["ref_item"], strip_numpr=True)
            continue


def count_styles(doc_xml: Path) -> Counter:
    doc = parse_xml(doc_xml)
    body = doc.getroot().find("w:body", namespaces=NS)
    c: Counter = Counter()
    if body is None:
        return c
    for p in body.xpath(".//w:p", namespaces=NS):
        ps = p.find("w:pPr/w:pStyle", namespaces=NS)
        c[ps.get(f"{{{NS['w']}}}val") if ps is not None else None] += 1
    return c


def inspect_doc(docx: Path) -> Dict[str, Any]:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        u = td / "doc"
        unzip_docx(docx, u)
        doc_xml = u / "word/document.xml"
        doc = parse_xml(doc_xml)
        body = doc.getroot().find("w:body", namespaces=NS)
        if body is None:
            raise SystemExit("docx 缺少 word/document.xml 或 w:body")

        sections = compute_sections(body)
        styles = count_styles(doc_xml)
        style_name_by_id = load_paragraph_style_name_map(u / "word/styles.xml")

        # 统计模板/文档中出现的 styleId（不展开 styles.xml，保持 KISS）
        style_counts = [
            {
                "styleId": k,
                "styleName": style_name_by_id.get(k) if k is not None else None,
                "count": v,
            }
            for k, v in styles.most_common()
        ]

        # 常见锚点候选
        anchors: Dict[str, List[Dict[str, Any]]] = {"body_start": [], "references": [], "author_bio": []}
        children = list(body)
        content_children = (
            children[:-1] if children and children[-1].tag == f"{{{NS['w']}}}sectPr" else children
        )
        for i, el in enumerate(content_children):
            if el.tag != f"{{{NS['w']}}}p":
                continue
            t = p_text(el).strip()
            nt = normalize_text(t)
            if re.match(r"^0引言$", nt) or re.match(r"^0引言", nt) or nt == "引言":
                anchors["body_start"].append({"idx": i, "text": t[:60], "styleId": get_p_style_id(el)})
            if nt in {"参考文献", "references"}:
                anchors["references"].append({"idx": i, "text": t[:60], "styleId": get_p_style_id(el)})
            if nt in {"作者简介", "authorbiography", "authorbio"}:
                anchors["author_bio"].append({"idx": i, "text": t[:60], "styleId": get_p_style_id(el)})

        for group in anchors.values():
            for item in group:
                sid = item.get("styleId")
                item["styleName"] = style_name_by_id.get(sid) if sid else None

        return {
            "docx": str(docx),
            "sections": [s.__dict__ for s in sections],
            "styleCounts": style_counts[:80],
            "anchorCandidates": anchors,
        }


def load_json_config(path: Optional[Path]) -> Dict[str, Any]:
    if path is None:
        return {}
    if not path.is_file():
        raise SystemExit(f"config not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


DEFAULT_BODY_START_REGEXES = [
    r"^0引言$",
    r"^0引言",
    r"^引言$",
    r"^0introduction$",
    r"^1introduction$",
    r"^introduction$",
]


def reformat(
    *,
    source: Path,
    template: Path,
    output: Path,
    report: Optional[Path],
    config: Dict[str, Any],
    tpl_body_start_regexes: Sequence[str],
    src_body_start_regexes: Sequence[str],
    skip_front_matter: bool,
) -> None:
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        src_u = td / "src"
        tpl_u = td / "tpl"
        out_u = td / "out"
        unzip_docx(source, src_u)
        unzip_docx(template, tpl_u)
        shutil.copytree(tpl_u, out_u, dirs_exist_ok=True)

        src_doc = parse_xml(src_u / "word/document.xml")
        out_doc = parse_xml(out_u / "word/document.xml")

        out_body = out_doc.getroot().find("w:body", namespaces=NS)
        src_body = src_doc.getroot().find("w:body", namespaces=NS)
        if out_body is None or src_body is None:
            raise SystemExit("missing w:body")

        tpl_body_start = find_first_para_idx_by_regex(out_body, tpl_body_start_regexes)
        if tpl_body_start is None:
            raise SystemExit(
                "未能在模板中定位正文起点。建议先运行 inspect-template 获取候选索引，并通过 --tpl-body-start-regex 指定。"
            )

        src_body_start = find_first_para_idx_by_regex(src_body, src_body_start_regexes)
        if src_body_start is None:
            raise SystemExit(
                "未能在源文档中定位正文起点。建议先运行 inspect-doc 获取候选索引，并通过 --src-body-start-regex 指定。"
            )

        # 记录模板正文 section 的结束分节段落（用于复刻双栏等版式）
        tpl_marker = extract_body_section_end_marker(out_body, tpl_body_start)

        # 发现模板样式（用于后处理）
        style_name_by_id = load_paragraph_style_name_map(out_u / "word/styles.xml")
        tpl_style_ids = discover_template_style_ids(
            out_body, tpl_body_start_idx=tpl_body_start, style_name_by_id=style_name_by_id
        )
        style_overrides = (
            config.get("style_overrides") if isinstance(config.get("style_overrides"), dict) else {}
        ) or {}
        style_ids = {**tpl_style_ids, **{k: str(v) for k, v in style_overrides.items()}}

        # front matter 更新（可跳过）
        overrides = (config.get("front_matter_overrides") or {}) if isinstance(config.get("front_matter_overrides"), dict) else {}
        if not skip_front_matter:
            fm = extract_front_matter_from_source(src_doc, body_start_idx=src_body_start)
            update_template_front_matter(
                out_doc, fm, tpl_body_start_idx=tpl_body_start, overrides=overrides
            )

        # 读取 body children，定位 final sectPr
        out_children = list(out_body)
        if not out_children or out_children[-1].tag != f"{{{NS['w']}}}sectPr":
            raise SystemExit("template missing final w:sectPr")
        final_sect = out_children[-1]

        # 删除模板正文示例内容（从正文起点到 final_sect 之前）
        for el in out_children[tpl_body_start:-1]:
            out_body.remove(el)

        # 准备插入源正文内容：从正文起点开始，跳过 sectPr 并剥离所有 sectPr 后代
        src_children = list(src_body)
        to_insert: List[etree._Element] = []
        for el in src_children[src_body_start:]:
            if el.tag == f"{{{NS['w']}}}sectPr":
                continue
            c = copy.deepcopy(el)
            strip_descendants(c, ".//w:sectPr")
            strip_p_styles(c)
            to_insert.append(c)

        # 合并关系与部件，并重写 rId
        rid_start = max_rid_num(out_u / "word/_rels/document.xml.rels") + 1
        rid_map = merge_relationships_and_parts(
            src_root=src_u, out_root=out_u, inserted=to_insert, rid_start=rid_start
        )
        for el in to_insert:
            rewrite_rids(el, rid_map)

        # 插入正文内容
        for el in to_insert:
            out_body.insert(out_body.index(final_sect), el)

        # 复刻模板“正文 section”的结束分节段落（例如 cols=2），确保从正文起点起双栏生效
        if tpl_marker is not None:
            break_p, post_p, _sec = tpl_marker
            out_body.insert(out_body.index(final_sect), break_p)
            out_body.insert(out_body.index(final_sect), post_p)

        # 后处理：标题/图题/公式编号等样式（保守）
        apply_body_styles(out_body, start_idx=tpl_body_start, style_ids=style_ids)

        write_xml(out_doc, out_u / "word/document.xml")
        zip_docx(out_u, output)

        # 自检 + 报告
        out_check = td / "out_check"
        unzip_docx(output, out_check)
        errs = sanity_check_unpacked_docx(out_check)
        if errs:
            raise SystemExit("输出文档自检失败：\n- " + "\n- ".join(errs))

        if report is not None:
            styles = count_styles(out_check / "word/document.xml")
            doc = parse_xml(out_check / "word/document.xml")
            body = doc.getroot().find("w:body", namespaces=NS)
            sections = compute_sections(body) if body is not None else []

            # 尝试定位正文起点在输出中的 section（以 src 的正文起点标题为参照）
            out_body_start = None
            if body is not None:
                out_body_start = find_first_para_idx_by_regex(body, src_body_start_regexes)

            lines: List[str] = [
                "# 重排报告",
                "",
                f"- 源文档：`{source}`",
                f"- 模板：`{template}`",
                f"- 输出：`{output}`",
                "",
                "## 样式映射（用于后处理）",
                "",
                f"- 自动识别：`{json.dumps(tpl_style_ids, ensure_ascii=False)}`",
                f"- 覆盖配置：`{json.dumps(style_overrides, ensure_ascii=False)}`",
                f"- 生效映射：`{json.dumps(style_ids, ensure_ascii=False)}`",
                "",
                "## 分节（section）摘要",
                "",
            ]
            for i, s in enumerate(sections, start=1):
                lines.append(f"- section{i}: paras {s.start}-{s.end}, cols_num={s.cols_num}")
            if out_body_start is not None:
                sec = find_section_for_idx(sections, out_body_start) if sections else None
                if sec is not None:
                    lines += [
                        "",
                        "## 正文起点检查",
                        "",
                        f"- 正文起点段落索引：{out_body_start}",
                        f"- 所在 section cols_num：{sec.cols_num}",
                    ]

            lines += ["", "## 段落样式计数", ""]
            for k, v in styles.most_common():
                lines.append(f"- `{k}`: {v}")
            report.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[Sequence[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="reformat.py", description="将论文内容套用目标期刊 Word 模板（OOXML 级重排）")
    sub = ap.add_subparsers(dest="cmd", required=True)

    ap_ins_tpl = sub.add_parser("inspect-template", help="生成模板画像（sections/style/锚点候选）")
    ap_ins_tpl.add_argument("--template", required=True, help="模板 .docx")
    ap_ins_tpl.add_argument("--out", required=True, help="输出 JSON")

    ap_ins = sub.add_parser("inspect-doc", help="生成 docx 画像（sections/style/锚点候选）")
    ap_ins.add_argument("--docx", required=True, help="输入 .docx")
    ap_ins.add_argument("--out", required=True, help="输出 JSON")

    ap_ref = sub.add_parser("reformat", help="执行重排（模板为母版）")
    ap_ref.add_argument("--source", required=True, help="源论文 .docx")
    ap_ref.add_argument("--template", required=True, help="期刊模板 .docx")
    ap_ref.add_argument("--output", required=True, help="输出 .docx")
    ap_ref.add_argument("--report", default="reformat_report.md", help="输出报告 (md)")
    ap_ref.add_argument("--config", default=None, help="可选 JSON 配置（front_matter_overrides 等）")
    ap_ref.add_argument(
        "--tpl-body-start-regex",
        action="append",
        default=[],
        help="模板正文起点匹配正则（作用于去空白后的段落文本），可多次指定",
    )
    ap_ref.add_argument(
        "--src-body-start-regex",
        action="append",
        default=[],
        help="源文档正文起点匹配正则（作用于去空白后的段落文本），可多次指定",
    )
    ap_ref.add_argument("--skip-front-matter", action="store_true", help="跳过 front matter 替换（仅做正文注入与分节复刻）")

    args = ap.parse_args(argv)

    if args.cmd in {"inspect-template", "inspect-doc"}:
        docx = Path(args.template if args.cmd == "inspect-template" else args.docx).expanduser().resolve()
        out = Path(args.out).expanduser().resolve()
        prof = inspect_doc(docx)
        out.write_text(json.dumps(prof, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    if args.cmd == "reformat":
        src = Path(args.source).expanduser().resolve()
        tpl = Path(args.template).expanduser().resolve()
        out = Path(args.output).expanduser().resolve()
        report = Path(args.report).expanduser().resolve() if args.report else None
        cfg = load_json_config(Path(args.config).expanduser().resolve()) if args.config else {}

        tpl_regexes = args.tpl_body_start_regex or cfg.get("tpl_body_start_regexes") or DEFAULT_BODY_START_REGEXES
        src_regexes = args.src_body_start_regex or cfg.get("src_body_start_regexes") or DEFAULT_BODY_START_REGEXES

        if not src.is_file():
            raise SystemExit(f"source not found: {src}")
        if not tpl.is_file():
            raise SystemExit(f"template not found: {tpl}")

        reformat(
            source=src,
            template=tpl,
            output=out,
            report=report,
            config=cfg,
            tpl_body_start_regexes=tpl_regexes,
            src_body_start_regexes=src_regexes,
            skip_front_matter=bool(args.skip_front_matter),
        )
        return 0

    raise SystemExit("unknown command")


if __name__ == "__main__":
    raise SystemExit(main())
