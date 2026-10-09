"""Resumes and cover letters as .docx (standard library only) plus PDF through LibreOffice.

Resume content is JSON (see examples/profile/resume.json):
  {"name": "...", "contact": [{"text": "...", "url": "..."}],      # both optional: default from [identity]
   "sections": [{"title": "EXPERIENCE", "items": [
      {"type": "entry", "bold": "Role", "normal": ", Org", "right": "Jun 2025 – Present", "bullets": ["..."]},
      {"type": "line", "label": "Languages: ", "text": "Python, SQL"}]}]}

Cover letters are a JSON list (see examples/profile/letters.json):
  [{"key": "Acme", "company": "Acme", "role": "Software Engineer Intern", "paras": ["...", "..."]}]
"""
import datetime as dt
import pathlib
import re
import shutil
import subprocess
import tempfile
import zipfile
from xml.sax.saxutils import escape, quoteattr

W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
FONT = "Arial"


def rpr(bold=False, size=20, color=None, underline=False, spacing=None):
    return ("<w:rPr>" + f'<w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}"/>'
            + ("<w:b/><w:bCs/>" if bold else "") + (f'<w:color w:val="{color}"/>' if color else "")
            + (f'<w:spacing w:val="{spacing}"/>' if spacing else "")
            + f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>' + ('<w:u w:val="single"/>' if underline else "")
            + "</w:rPr>")


def run(text, **kw):
    return f'<w:r>{rpr(**kw)}<w:t xml:space="preserve">{escape(text)}</w:t></w:r>'


def para(*runs, align=None, before=0, after=0, line=None, tab=None, border=None, bullet=False):
    ppr = ""
    if bullet:
        ppr += '<w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr>'
    if border:
        ppr += f'<w:pBdr><w:bottom w:val="single" w:sz="6" w:space="{border[1]}" w:color="{border[0]}"/></w:pBdr>'
    if tab:
        ppr += f'<w:tabs><w:tab w:val="right" w:pos="{tab}"/></w:tabs>'
    ppr += f'<w:spacing w:before="{before}" w:after="{after}"' + (f' w:line="{line}" w:lineRule="auto"' if line else "") + "/>"
    if align:
        ppr += f'<w:jc w:val="{align}"/>'
    return f"<w:p><w:pPr>{ppr}</w:pPr>{''.join(runs)}</w:p>"


class Docx:
    """Collects body XML and hyperlinks, then writes a minimal valid .docx."""

    def __init__(self, margins=(720, 720, 720, 720), title="", author=""):
        self.body, self.links = [], []
        self.margins, self.title, self.author = margins, title, author

    def link(self, text, url, **kw):
        self.links.append(url)
        rid = f"rIdL{len(self.links)}"
        return f'<w:hyperlink r:id="{rid}">{run(text, **kw)}</w:hyperlink>'

    def add(self, xml):
        self.body.append(xml)

    def save(self, path):
        top, right, bottom, left = self.margins
        doc = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:document xmlns:w="{W}" xmlns:r="{R}"><w:body>'
               + "".join(self.body)
               + f'<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="{top}" w:right="{right}" w:bottom="{bottom}"'
               f' w:left="{left}" w:header="0" w:footer="0" w:gutter="0"/></w:sectPr></w:body></w:document>')
        rels = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                f'<Relationship Id="rIdS" Type="{R}/styles" Target="styles.xml"/>'
                f'<Relationship Id="rIdN" Type="{R}/numbering" Target="numbering.xml"/>'
                + "".join(f'<Relationship Id="rIdL{i}" Type="{R}/hyperlink" Target={quoteattr(u)} TargetMode="External"/>'
                          for i, u in enumerate(self.links, 1))
                + "</Relationships>")
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        core = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties '
                'xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" '
                'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                f"<dc:title>{escape(self.title)}</dc:title><dc:creator>{escape(self.author)}</dc:creator>"
                f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created></cp:coreProperties>')
        files = {
            "[Content_Types].xml": CONTENT_TYPES, "_rels/.rels": ROOT_RELS, "word/document.xml": doc,
            "word/_rels/document.xml.rels": rels, "word/styles.xml": STYLES, "word/numbering.xml": NUMBERING,
            "docProps/core.xml": core,
        }
        path = pathlib.Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
            for name, data in files.items():
                z.writestr(name, data)
        return path


CONTENT_TYPES = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
                 '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                 '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
                 '<Default Extension="xml" ContentType="application/xml"/>'
                 '<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
                 '<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>'
                 '<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>'
                 '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                 "</Types>")
ROOT_RELS = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
             '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
             f'<Relationship Id="rId1" Type="{R}/officeDocument" Target="word/document.xml"/>'
             '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
             "</Relationships>")
STYLES = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:styles xmlns:w="{W}">'
          f'<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}" w:cs="{FONT}" w:eastAsia="{FONT}"/>'
          '<w:sz w:val="20"/><w:szCs w:val="20"/><w:lang w:val="en-US"/></w:rPr></w:rPrDefault>'
          '<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
          '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>'
          "</w:styles>")
NUMBERING = (f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?><w:numbering xmlns:w="{W}">'
             '<w:abstractNum w:abstractNumId="0"><w:multiLevelType w:val="singleLevel"/>'
             '<w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="•"/><w:lvlJc w:val="left"/>'
             '<w:pPr><w:ind w:left="300" w:hanging="200"/></w:pPr>'
             f'<w:rPr><w:rFonts w:ascii="{FONT}" w:hAnsi="{FONT}"/></w:rPr></w:lvl></w:abstractNum>'
             '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num></w:numbering>')


# ---- PDF ---------------------------------------------------------------------
def to_pdf(docx):
    """Convert with LibreOffice (in a throwaway profile, so an open LibreOffice window doesn't block it)."""
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return None
    docx = pathlib.Path(docx)
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([soffice, f"-env:UserInstallation=file://{prof}", "--headless", "--convert-to", "pdf",
                        "--outdir", str(docx.parent), str(docx)], check=True, capture_output=True, timeout=180)
    pdf = docx.with_suffix(".pdf")
    return pdf if pdf.exists() else None


def pdf_pages(pdf):
    if shutil.which("pdfinfo"):
        out = subprocess.run(["pdfinfo", str(pdf)], capture_output=True, text=True).stdout
        m = re.search(r"Pages:\s+(\d+)", out)
        if m:
            return int(m.group(1))
    return len(re.findall(rb"/Type\s*/Page[^s]", pathlib.Path(pdf).read_bytes()))


# ---- shared header -----------------------------------------------------------
def contact_items(ident, override=None):
    if override:
        return override
    items = [{"text": ident.get("location", "")}, {"text": ident.get("phone", "")}]
    if ident.get("email"):
        items.append({"text": ident["email"], "url": f"mailto:{ident['email']}"})
    items += [{"text": l.get("label") or l["url"], "url": l["url"]} for l in ident.get("links", [])]
    return [i for i in items if i.get("text")]


def contact_line(doc, items, size, color=None):
    out = []
    for k, it in enumerate(items):
        if k:
            out.append(run(" | ", size=size))
        out.append(doc.link(it["text"], it["url"], size=size, color=color) if it.get("url") else run(it["text"], size=size))
    return out


def file_stem(name):
    return re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_") or "Applicant"


# ---- resume --------------------------------------------------------------------
def resume(spec, ident, out_dir, basename=None, max_pages=1, pdf=True):
    """Build <out_dir>/<basename>.docx (+ .pdf). Returns (docx, pdf or None, pages or None)."""
    name = spec.get("name") or ident.get("name", "").upper()
    basename = basename or f"{file_stem(ident.get('name') or name.title())}_Resume"
    doc = Docx(title=f"{name.title()} Resume", author=ident.get("name", ""))
    doc.add(para(run(name, bold=True, size=32), align="center", after=30))
    doc.add(para(*contact_line(doc, contact_items(ident, spec.get("contact")), 19), align="center", after=0))
    for sec in spec["sections"]:
        doc.add(para(run(sec["title"], bold=True, size=21, spacing=15), before=160, after=60, border=("000000", 1)))
        for it in sec["items"]:
            if it["type"] == "entry":
                right = run("\t" + it["right"], bold=it.get("right_bold", True)) if it.get("right") else ""
                doc.add(para(run(it["bold"], bold=True), run(it.get("normal", "")), right,
                             before=it.get("before", 70), after=10, tab=10800))
                for b in it.get("bullets", []):
                    doc.add(para(run(b), bullet=True, after=15))
            elif it["type"] == "line":
                doc.add(para(run(it["label"], bold=True), run(it["text"]), after=it.get("after", 15)))
            else:
                raise ValueError(f"unknown item type {it['type']!r}")
    path = doc.save(pathlib.Path(out_dir) / f"{basename}.docx")
    if not pdf:
        return path, None, None
    out = to_pdf(path)
    pages = pdf_pages(out) if out else None
    if out and max_pages and pages > max_pages:
        raise SystemExit(f"{out} is {pages} pages (limit {max_pages}): trim the content")
    return path, out, pages


# ---- cover letters ---------------------------------------------------------------
def letters(items, ident, out_dir, pdf=True, date=None):
    """One .docx (+ .pdf) per letter, with a header that matches the resume. Returns [(path, words)]."""
    if not date:
        d = dt.date.today()
        date = f"{d:%B} {d.day}, {d.year}"
    out = []
    for L in items:
        doc = Docx(margins=(1080, 1260, 1080, 1260), title=f"Cover Letter - {L['company']}", author=ident.get("name", ""))
        doc.add(para(run(ident.get("name", "").upper(), bold=True, size=32), align="center", after=30))
        doc.add(para(*contact_line(doc, contact_items(ident), 18, color="1F3A93"), align="center", after=360,
                     border=("999999", 8)))
        body = [p.replace("'", "’") for p in L["paras"]]
        team = L.get("team") or f"{L['company']} Hiring Team"
        for text, after in [(date, 240), (team, 0), (f"Re: {L['role']}", 240), (L.get("greeting") or f"Dear {team},", 200)]:
            doc.add(para(run(text, size=21), after=after, line=276))
        for p in body:
            doc.add(para(run(p, size=21), after=200, line=276))
        doc.add(para(run(L.get("closing", "Sincerely,"), size=21), after=60, line=276))
        doc.add(para(run(ident.get("name", ""), size=21), line=276))
        path = doc.save(pathlib.Path(out_dir) / f"{file_stem(ident.get('name', ''))}_Cover_Letter_{file_stem(L['key'])}.docx")
        made = to_pdf(path) if pdf else None
        if made and pdf_pages(made) > 1:
            print(f"warning: {made.name} runs past one page")
        out.append((made or path, len(" ".join(body).split())))
    return out
