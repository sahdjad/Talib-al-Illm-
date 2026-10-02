import sys, json, re
import pypdfium2 as pdfium

pdf_path, toc_path = sys.argv[1], sys.argv[2]
toc = json.load(open(toc_path))
pdf = pdfium.PdfDocument(pdf_path)
pages = []
for i in range(len(pdf)):
    t = pdf[i].get_textpage().get_text_range()
    t = t.replace('­', '')
    t = re.sub(r'\s+', ' ', t)
    pages.append(t)

def norm(s):
    s = re.sub(r'<[^>]+>', '', s)
    s = s.replace('­', '')
    return re.sub(r'\s+', ' ', s).strip()

res = {}
cursor = 0
for e in toc:
    title = norm(e['title'])
    needle = title[:40]
    found = None
    for p in range(cursor, len(pages)):
        if needle in pages[p]:
            found = p
            break
    if found is None:
        found = cursor
    res[e['id']] = found + 1
    cursor = found
print(json.dumps(res))
