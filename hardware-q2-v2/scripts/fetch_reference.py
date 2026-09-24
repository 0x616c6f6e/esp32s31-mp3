from pathlib import Path
import urllib.request,zipfile,io,re
p=Path(__file__).resolve().parents[1]/'reference'
base='https://docs.espressif.com/projects/esp-hardware-design-guidelines/en/latest/esp32s31/'
u=base+'_downloads/2eaf1465f6c0a2c053dd3860663fe0e2/esp32-s31-wroom-3-n8r16v_v1.2_reference_design.zip'
b=urllib.request.urlopen(u,timeout=45).read();(p/'s31-module-reference.zip').write_bytes(b)
z=zipfile.ZipFile(io.BytesIO(b));print(z.namelist());z.extractall(p/'s31-module')
s=urllib.request.urlopen(base+'schematic-checklist.html',timeout=45).read().decode();(p/'schematic-checklist.html').write_text(s,encoding='utf8')
from urllib.parse import urljoin
for path in re.findall(r'(?:src|href)="([^"]+\.(?:pdf|png|svg))"',s):
 if 'schematic' in path.lower():
  try:
   data=urllib.request.urlopen(urljoin(base,path),timeout=45).read();(p/Path(path).name).write_bytes(data);print(path)
  except Exception as e:print(type(e).__name__,path)
