"""Original, deterministic SVG sprites. AI replacements never remove the fallback."""
import hashlib
import html
import io
from pathlib import Path

from contracts import canonical, identifier, number
from persistence import atomic_write

STYLE='emberglass-sovereign-v1'


class AssetForge:
    def __init__(self,directory):
        self.directory=Path(directory)

    def fallback(self,node,variant=0):
        identifier(node['id']); number(variant,'VARIANT',0,1000000,True)
        spec=dict(id=node['id'],kind=node['kind'],style=STYLE,size=[128,160],variant=variant)
        key=hashlib.sha256(canonical(spec).encode()).hexdigest()
        path=self.directory/(key+'.svg')
        if not path.is_file():
            palette=['#d3e7aa','#d4ad77','#87c2be','#b1a9dc']
            glow=palette[int(key[:8],16)%len(palette)]
            height=50 if node['kind']=='mine' else 88 if node['kind']=='tower' else 65
            top=120-height
            label=html.escape(node['title'][:1].upper())
            svg=f'''<svg xmlns="http://www.w3.org/2000/svg" width="128" height="160" viewBox="0 0 128 160">
<path d="M8 128 64 100 120 128 64 156Z" fill="#102321" opacity=".7"/>
<path d="M24 {top+16} 64 {top+36} 64 132 24 112Z" fill="#3f6159" stroke="#83a38b"/>
<path d="M64 {top+36} 104 {top+16} 104 112 64 132Z" fill="#233e39" stroke="#547d6a"/>
<path d="M24 {top+16} 64 {top-4} 104 {top+16} 64 {top+36}Z" fill="#78947a" stroke="{glow}"/>
<path d="M34 99 54 109 M75 109 94 99 M34 89 54 99 M75 99 94 89" stroke="{glow}" stroke-width="4"/>
<path d="M64 {top+16}V{max(4,top-20)}" stroke="{glow}" stroke-width="2"/>
<circle cx="64" cy="{max(4,top-20)}" r="4" fill="{glow}"/>
<text x="64" y="{top+64}" fill="{glow}" text-anchor="middle" font-size="14" font-family="sans-serif">{label}</text></svg>'''
            atomic_write(path,svg.encode('utf-8'))
        data=path.read_bytes()
        return dict(key=key,sha256=hashlib.sha256(data).hexdigest(),format='svg',origin='offline-template',
                    style=STYLE,variant=variant,status='READY',url='/api/assets/'+key+'.svg')

    def accept_image(self,node,data,variant=0):
        if len(data)>8*1024*1024: raise ValueError('IMAGE_TOO_LARGE')
        from PIL import Image
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in {'PNG','WEBP'} or not (32<=image.width<=2048 and 32<=image.height<=2048):
                raise ValueError('UNSUPPORTED_IMAGE')
            image.load()
            if 'A' not in image.getbands() or image.getextrema()[image.getbands().index('A')][0]==255:
                raise ValueError('TRANSPARENT_SPRITE_REQUIRED')
            ext='png' if image.format=='PNG' else 'webp'
        checksum=hashlib.sha256(data).hexdigest()
        atomic_write(self.directory/(checksum+'.'+ext),data)
        return dict(key=checksum,sha256=checksum,format=ext,origin='ai-provider',style=STYLE,
                    variant=variant,status='READY',url='/api/assets/'+checksum+'.'+ext)

    def prompt(self,node):
        return f'Original {node["kind"]} sprite for {node["title"]}. Dark sci-fi Emberglass RTS isometric style, 2:1 isometry, muted green metal, warm emissive details, single centered object, transparent background, no text, no logos, no copied game art.'
