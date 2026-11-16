import codecs, io, re, sys, zipfile

zip_path = sys.argv[1] if len(sys.argv) > 1 else "35e0e2c898cc0035a1595e5a3a7c9558.zip"
apk = zipfile.ZipFile(io.BytesIO(zipfile.ZipFile(zip_path).read("Zoom.apk")))
dex = apk.read("classes.dex")
enc = re.search(rb"VQC\{[^}]+\}", dex).group().decode()  # BuildConfig.FLAG_ROT13
print(enc, "->", codecs.encode(enc, "rot13"))
