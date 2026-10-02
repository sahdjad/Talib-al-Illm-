import pypdfium2 as pdfium, sys
pdf = pdfium.PdfDocument(sys.argv[1])
n=len(pdf)
res=[]
for i in range(n):
    bm = pdf[i].render(scale=0.4, grayscale=True)
    W,H = bm.width, bm.height
    buf = bytes(bm.buffer)
    stride = len(buf)//H
    last = 0
    for y in range(int(H*0.93)):
        row = buf[y*stride:y*stride+W]
        if min(row) < 235: last = y
    res.append((i+1, round(last/H,2)))
low=[r for r in res if r[1]<0.80]
print(n,'pages; low-fill:',low)
