import sys, pypdfium2 as pdfium
pdf = pdfium.PdfDocument(sys.argv[1])
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 1.25
for spec in sys.argv[2].split(','):
    a, _, b = spec.partition('-')
    a = int(a); b = int(b) if b else a
    for i in range(a, b + 1):
        pdf[i-1].render(scale=scale).to_pil().convert('RGB').save(f'out/pv_{i:03d}.png')
        print(f'out/pv_{i:03d}.png')
