import re
import subprocess
from pathlib import Path

def count_pdf_pages(pdf_path: Path) -> int:
    try:
        content = pdf_path.read_bytes()
        count_match = re.search(rb'/Type\s*/Pages\s*/Count\s*(\d+)', content)
        if count_match:
            return int(count_match.group(1).decode())
        count_match2 = re.search(rb'/Count\s*(\d+)\s*/Type\s*/Pages', content)
        if count_match2:
            return int(count_match2.group(1).decode())
        return len(re.findall(rb'/Type\s*/Page\b', content))
    except Exception:
        return -1

def generate_pdf():
    base_dir = Path(__file__).resolve().parent.parent.parent
    md_path = base_dir / "docs" / "technical_report.md"
    html_path = base_dir / "docs" / "temp_report.html"
    pdf_path = base_dir / "docs" / "Safiri_Route_Intelligence_Technical_Report.pdf"

    if not md_path.exists():
        print(f"Error: {md_path} not found.")
        return False

    content = md_path.read_text(encoding="utf-8")

    # Divide content into 3 distinct pages using page break markers
    # Page 1: Title, Executive Summary, 1. Problem Definition, 2. Definition of Optimality, 3. Decision Framework, 4. Hard Constraints
    # Page 2: 5. Multi-Objective Scoring, 6. Pareto Analysis, 7. Sensitivity Analysis, 8. Explanation Architecture, 9. Dataset
    # Page 3: 10. Evaluation Methodology, 11. Evaluation Results, 12. Testing and Reliability, 13. Limitations and Future Work, 14. Conclusion

    # Remove raw markdown footer line if present
    content = re.sub(r"\n+---\n+\*.*Technical Report.*?\*\n*$", "", content.strip())

    # Markdown formatting
    html_body = content
    html_body = re.sub(r"^### (.*?)$", r"<h3>\1</h3>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^## (.*?)$", r"<h2>\1</h2>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"^# (.*?)$", r"<h1>\1</h1>", html_body, flags=re.MULTILINE)
    html_body = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", html_body)
    html_body = re.sub(r"\*(.*?)\*", r"<em>\1</em>", html_body)
    html_body = re.sub(r"`(.*?)`", r"<code>\1</code>", html_body)
    html_body = re.sub(r"^> (.*?)$", r"<blockquote>\1</blockquote>", html_body, flags=re.MULTILINE)

    # Tables conversion
    lines = html_body.split("\n")
    in_table = False
    new_lines = []
    for line in lines:
        sline = line.strip()
        if sline.startswith("|") and sline.endswith("|"):
            if "---" in sline:
                continue
            cells = [c.strip() for c in sline.split("|")[1:-1]]
            tag = "th" if not in_table else "td"
            if not in_table:
                new_lines.append("<table>")
                in_table = True
            row = "<tr>" + "".join(f"<{tag}>{c}</{tag}>" for c in cells) + "</tr>"
            new_lines.append(row)
        else:
            if in_table:
                new_lines.append("</table>")
                in_table = False
            new_lines.append(line)

    if in_table:
        new_lines.append("</table>")

    html_body = "\n".join(new_lines)
    html_body = re.sub(r"\n\n+", "</p><p>", html_body)
    html_body = "<p>" + html_body + "</p>"
    html_body = html_body.replace("<p><h", "<h").replace("</h1></p>", "</h1>").replace("</h2></p>", "</h2>").replace("</h3></p>", "</h3>")
    html_body = html_body.replace("<p><table", "<table").replace("</table></p>", "</table>")
    html_body = html_body.replace("<p><blockquote", "<blockquote").replace("</blockquote></p>", "</blockquote>")
    html_body = html_body.replace("<p>---</p>", "<hr/>")

    # Insert page breaks before section 5 and section 10
    html_body = html_body.replace(
        "<h3>5. Multi-Objective Scoring</h3>",
        "<div class='page-footer'>RouteStage — Technical Report | Page 1 of 3</div><div class='page-break'></div><h3>5. Multi-Objective Scoring</h3>"
    )
    html_body = html_body.replace(
        "<h3>10. Evaluation Methodology</h3>",
        "<div class='page-footer'>RouteStage — Technical Report | Page 2 of 3</div><div class='page-break'></div><h3>10. Evaluation Methodology</h3>"
    )

    # Append footer for page 3
    html_body += "<div class='page-footer'>RouteStage — Technical Report | Page 3 of 3</div>"

    style = """
    @page {
        size: A4 portrait;
        margin: 14mm 14mm 14mm 14mm;
    }
    body {
        font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        font-size: 8.7pt;
        line-height: 1.34;
        color: #24292f;
        margin: 0;
        padding: 0;
    }
    h1 {
        font-size: 15pt;
        margin: 0 0 2px 0;
        color: #0969da;
        letter-spacing: -0.2px;
    }
    h2 {
        font-size: 10.5pt;
        margin: 0 0 6px 0;
        color: #57606a;
        font-weight: 500;
    }
    h3 {
        font-size: 9.6pt;
        margin: 7px 0 2px 0;
        color: #1f2328;
        border-bottom: 1px solid #d0d7de;
        padding-bottom: 1px;
    }
    p {
        margin: 3px 0;
    }
    ol, ul {
        margin: 2px 0;
        padding-left: 18px;
    }
    li {
        margin: 1px 0;
    }
    table {
        border-collapse: collapse;
        width: 100%;
        margin: 5px 0;
        font-size: 8pt;
    }
    th, td {
        border: 1px solid #d0d7de;
        padding: 3.5px 6px;
        text-align: left;
    }
    th {
        background-color: #f6f8fa;
        font-weight: 600;
    }
    code {
        font-family: 'Consolas', 'Courier New', monospace;
        font-size: 8pt;
        background-color: #eff1f3;
        padding: 1px 3px;
        border-radius: 3px;
    }
    blockquote {
        border-left: 3px solid #0969da;
        margin: 4px 0;
        padding: 3px 8px;
        background: #f6f8fa;
        font-style: italic;
    }
    hr {
        border: none;
        border-top: 1px solid #d0d7de;
        margin: 6px 0;
    }
    .page-break {
        page-break-before: always;
        break-before: page;
    }
    .page-footer {
        position: relative;
        text-align: right;
        font-size: 7.5pt;
        color: #8c959f;
        margin-top: 8px;
        margin-bottom: 4px;
        border-top: 1px solid #eaeef2;
        padding-top: 2px;
    }
    """

    full_html = f"<!DOCTYPE html><html><head><meta charset='utf-8'><title>RouteStage</title><style>{style}</style></head><body>{html_body}</body></html>"
    html_path.write_text(full_html, encoding="utf-8")

    edge_exe = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    cmd = [
        edge_exe,
        "--headless",
        "--disable-gpu",
        "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path.resolve()}",
        str(html_path.resolve()),
    ]
    res = subprocess.run(cmd, capture_output=True)
    if html_path.exists():
        html_path.unlink()

    pages = count_pdf_pages(pdf_path)
    print(f"PDF Generated: Return code {res.returncode}, Pages: {pages}, Path: {pdf_path}")
    return pages == 3

if __name__ == "__main__":
    generate_pdf()
