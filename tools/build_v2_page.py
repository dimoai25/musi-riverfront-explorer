"""Assemble the v2 explorer page. Usage: python3 -I build_v2_page.py app_dir data.json out_artifact.html out_site.html site_url"""
import sys, json
app, data, out_a, out_s, url = sys.argv[1:6]
css = open(f'{app}/base.css', encoding='utf-8').read() + open(f'{app}/extra.css', encoding='utf-8').read()
body = open(f'{app}/body.html', encoding='utf-8').read()
D = json.load(open(data, encoding='utf-8'))
body = body.replace('/*DATA*/null', json.dumps(D, ensure_ascii=False, separators=(',', ':')))
fonts = ('<link rel="preconnect" href="https://fonts.googleapis.com">\n<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
         '<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Archivo:wght@500;650;750&family=Source+Sans+3:wght@400;600&family=IBM+Plex+Mono:wght@400;500&display=swap">\n')
art = ('<title>Musi Riverfront Explorer</title>\n<meta name="claude:viewport-fit-sides" content="cover">\n' + fonts +
       '<style>' + css + '</style>\n' + body)
open(out_a, 'w', encoding='utf-8').write(art)
desc = 'Swipe between today and the proposed Musi Riverfront plan across Zone 1A and 1B, from Osman Sagar and Himayat Sagar to Bapu Ghat, with the tender documents behind it.'
head = f'''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Musi Riverfront Explorer</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:url" content="{url}">
<meta property="og:title" content="Musi Riverfront: today vs the plan">
<meta property="og:description" content="{desc}">
<meta property="og:image" content="{url}og.png">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:creator" content="@Vamsidhar_t">
<meta name="twitter:title" content="Musi Riverfront: today vs the plan">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{url}og.png">
<link rel="icon" href="favicon.svg" type="image/svg+xml">
{fonts}<style>
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px/1.4 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
</style>
<style>{css}</style>
</head>
<body>
{body}
</body>
</html>
'''
open(out_s, 'w', encoding='utf-8').write(head)
print(len(art), len(head))
