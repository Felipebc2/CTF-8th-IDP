import codecs,sys
d=open(sys.argv[1] if len(sys.argv)>1 else 'extracted/programa','rb').read()
# .data/.rodata 'flag' at vaddr 0x2020 == file offset 0x2020 (rodata)
s=d[0x2020:d.index(b'\0',0x2020)].decode()
f=codecs.encode(s,'rot13')
print(s,'->',f)
assert f.startswith('IDP{') and f.endswith('}')
