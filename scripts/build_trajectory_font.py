"""Embed a licensed CJK subset for reviewed trace text; no external font fetch."""
import base64
import hashlib
from pathlib import Path
import re
from fontTools import subset
from fontTools.ttLib import TTFont

site=Path(__file__).resolve().parents[1]
source=site.parent/'cache/report_fonts/NotoSansCJKsc-Regular.otf'
text=(site/'research/trajectory-example.json').read_text()
characters={c for c in text if ord(c)>=0x2e80}
font=TTFont(source,recalcTimestamp=False)
options=subset.Options()
options.flavor='woff2'
options.hinting=False
options.name_IDs=[0,1,2,3,4,5,6,13,14]
subsetter=subset.Subsetter(options=options)
subsetter.populate(text=''.join(sorted(characters)))
subsetter.subset(font)
for record in font['name'].names:
    if record.nameID in (1,3,4,6):
        record.string='DuplexTraceCJK'.encode(record.getEncoding())
font.flavor='woff2'
destination=source.parent/'trajectory-cjk.woff2'
font.save(destination)
data=base64.b64encode(destination.read_bytes()).decode()
block=('/* BEGIN EMBEDDED NATIVE CJK — Noto subset, SIL OFL 1.1; see Noto-font-LICENSE */\n'
       '@font-face{font-family:DuplexTraceCJK;font-style:normal;font-weight:400 800;font-display:swap;'
       'src:url(data:font/woff2;base64,'+data+') format("woff2");}\n'
       'body{font-family:DuplexTraceCJK,ui-sans-serif,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;}\n'
       '#timeline text{font-family:DuplexTraceCJK,ui-sans-serif,sans-serif;}\n'
       'pre{font-family:DuplexTraceCJK,ui-monospace,SFMono-Regular,monospace;}\n'
       '/* END EMBEDDED NATIVE CJK */\n')
css=site/'assets/trajectory/viewer.css'
existing=re.sub(r'/\* BEGIN EMBEDDED NATIVE CJK.*?/\* END EMBEDDED NATIVE CJK \*/\n?','',css.read_text(),flags=re.S)
css.write_text(existing+'\n'+block)
(site/'assets/trajectory/Noto-font-LICENSE').write_text((source.parent/'LICENSE').read_text())
print(f'Embedded {len(characters)} reviewed CJK characters, {destination.stat().st_size} bytes; source SHA256 {hashlib.sha256(source.read_bytes()).hexdigest()}')
