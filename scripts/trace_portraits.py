#!/usr/bin/env python3
"""Trace the supplied photographs into editable, animated vector strokes.

ImageMagick supplies the edge map. The rest is a pixel-graph to SVG conversion:
subject clipping, short-fragment removal, path simplification and curve fitting.
Hand traced contours restore dark hair and sideburn boundaries lost in the photos.
The originals are only read. No generated face or replacement photograph is used.
"""
import json
import math
import subprocess
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

PORTRAITS = [
    dict(id='03-stage', number=3, file='772725955_2315786472590446_335888140933700927_n.jpg',
         width=647, height=1024, crop=[45, 15, 565, 1009], min_length=14,
         polygon=[(209,68),(231,36),(281,19),(330,22),(365,47),(382,100),
                  (360,149),(396,171),(445,186),(460,181),(436,151),(439,126),
                  (470,128),(500,140),(543,140),(563,161),(581,209),(592,290),
                  (578,340),(538,355),(473,348),(439,314),(425,394),(415,489),
                  (444,580),(473,750),(514,818),(564,882),(608,929),(597,1024),
                  (407,1024),(398,914),(368,826),(327,684),(308,630),(284,682),
                  (258,791),(246,901),(251,1024),(130,1024),(145,894),(163,767),
                  (175,639),(188,547),(172,448),(147,502),(124,570),(107,609),
                  (105,658),(82,654),(67,616),(64,558),(84,472),(109,380),
                  (133,291),(148,209),(173,191),(219,180),(222,137),(213,117)],
         manual=[
             'M 255,233 C 245,263 254,303 279,334 M 323,229 C 311,268 307,313 301,341',
             'M 146,909 C 144,946 140,986 136,1021 M 248,914 C 245,948 249,987 249,1021',
             'M 398,918 C 405,951 415,987 422,1021',
             'M 174,449 C 183,473 190,487 199,502 M 188,551 C 180,604 175,659 168,711 C 165,761 158,815 154,855',
             'M 307,629 C 291,672 280,708 268,750 C 257,791 250,847 246,897',
             'M 83,576 C 78,592 80,612 89,624 L 91,646 M 111,587 C 115,606 107,614 108,632',
         ],
         face_region=[(198,10),(381,10),(381,121),(356,149),(346,177),
                      (330,218),(308,239),(270,243),(245,220),(233,178),(220,147),(198,142)],
         face_strokes=[
             ('M 217,145 C 208,134 201,120 203,107 L 200,102 C 201,86 213,72 224,63 L 220,61 C 234,47 247,41 260,37 L 257,34 C 272,28 280,29 293,26 C 307,20 322,23 332,29 L 339,30 C 353,39 357,46 362,56 C 370,68 372,79 374,91 C 373,108 368,121 362,135 L 354,153', 1.5),
             ('M 221,133 C 231,136 239,136 247,138 L 255,135 C 260,134 262,128 266,128 L 273,130', 1.15),
             ('M 263,125 L 269,123 L 274,114 L 278,118 L 281,116 L 287,123 L 284,113 L 290,117 L 289,109 L 294,114 L 296,109 C 305,116 309,124 311,132 C 314,137 317,143 318,147 C 320,155 315,165 315,172 L 313,182 C 320,179 327,172 333,168 C 341,157 345,143 347,134', 1.4),
             ('M 255,138 C 255,149 255,154 252,161 C 250,165 252,168 257,169 C 264,170 271,166 276,166', 1.5),
             ('M 272,156 C 278,157 281,162 280,165 M 259,170 C 264,167 270,168 272,169', 1.0),
             ('M 271,129 C 279,125 289,126 297,129 L 302,128 M 272,132 C 280,129 288,130 296,132', 1.45),
             ('M 270,138 C 279,142 287,143 294,137 M 276,143 C 281,145 286,144 289,142', 1.5),
             ('M 255,176 C 261,173 264,175 269,175 C 274,175 277,178 282,178', 1.15),
             ('M 255,181 C 263,181 266,183 273,181 C 278,180 282,181 285,183', 1.7),
             ('M 261,188 C 269,184 278,185 284,183 M 262,192 C 268,196 278,192 283,190', 1.2),
             ('M 276,159 C 284,164 287,178 294,186', 1.05),
             ('M 248,165 C 248,180 253,196 261,208 C 268,216 280,216 291,212 C 309,205 325,190 332,178', 1.4),
             ('M 266,201 C 274,199 282,201 289,198', 0.9),
             ('M 271,221 C 279,225 284,226 290,223 M 310,210 C 306,223 301,233 298,241', 1.0),
             ('M 332,187 C 330,200 330,214 335,223', 1.25),
             ('M 213,93 C 220,78 226,72 236,66 M 226,68 C 239,53 250,49 264,45 M 276,38 C 290,33 308,31 320,35', 0.85),
             ('M 324,40 C 343,48 356,66 358,81 M 336,60 C 349,71 354,82 355,93 M 335,88 C 349,95 356,98 360,105 M 332,105 C 341,110 351,111 357,109', 0.9),
             ('M 343,117 C 343,131 338,146 331,158', 0.8),
         ]),
    dict(id='02-microphone', number=2, file='703861528_17997792578956004_3653670580096013406_n.jpeg',
         width=640, height=853, crop=[60, 15, 580, 838], min_length=11,
         polygon=[(160,106),(182,54),(236,20),(298,18),(370,38),(421,67),
                  (452,116),(471,176),(479,253),(465,285),(493,324),(533,351),
                  (575,370),(612,425),(633,514),(631,592),(640,674),(640,853),
                  (153,853),(165,730),(187,660),(118,640),(71,618),(92,604),
                  (121,584),(120,532),(99,511),(91,481),(82,450),(85,425),
                  (112,411),(163,411),(187,383),(210,347),(204,324),(212,300),
                  (220,286),(195,280),(179,255),(174,203)],
         manual=[
             'M 195,272 C 176,260 174,233 183,205 C 174,173 173,142 181,113 C 186,84 201,61 230,43 C 249,25 279,26 300,33 C 336,30 371,44 394,64 C 424,76 443,99 451,127 C 469,160 469,198 466,220 C 480,247 472,275 455,294',
             'M 216,121 C 217,101 230,74 251,65 M 249,118 C 238,98 250,74 268,66 M 289,123 C 270,103 269,79 291,65',
             'M 296,96 C 324,98 350,122 376,134 M 322,76 C 351,82 377,98 398,118',
             'M 393,184 C 404,202 405,231 397,255 L 390,288 C 405,301 421,297 438,289 C 447,261 448,229 442,213',
             'M 348,289 C 365,279 375,260 379,244',
             'M 219,228 C 220,247 226,269 233,280',
         ]),
    dict(id='01-profile', number=1, file='775020719_18010620785956004_8913760364555554077_n.jpeg',
         width=640, height=852, crop=[0, 15, 640, 837], min_length=12,
         polygon=[(73,94),(83,65),(164,27),(254,19),(359,29),(443,58),
                  (493,112),(529,185),(555,253),(559,310),(581,423),(640,432),
                  (640,852),(0,852),(0,805),(41,746),(56,690),(77,629),
                  (85,575),(121,544),(158,529),(176,486),(183,457),(183,435),
                  (165,412),(173,388),(161,370),(157,340),(154,320),(130,317),
                  (125,303),(133,278),(143,251),(129,231),(130,198),(149,144),
                  (103,150),(82,129)],
         # The microphone is a separate subject region.
         extra_polygon=[(0,419),(18,405),(17,383),(32,360),(65,346),(94,347),
                        (119,367),(124,388),(114,417),(94,435),(55,442),(0,469)],
         manual=[
             'M 91,128 C 75,112 79,89 96,75 C 128,48 172,36 211,31 C 264,20 313,24 354,34 C 411,43 458,65 489,107 C 519,147 533,189 544,235 C 551,260 553,284 548,305',
             'M 103,97 C 141,64 186,50 231,45 M 121,106 C 166,70 211,60 253,58 M 292,44 C 336,43 375,53 411,71',
             'M 263,116 C 283,129 296,155 303,182 C 309,202 318,216 329,226',
             'M 294,207 C 287,229 280,252 276,278 L 271,339 C 298,348 345,327 376,309 C 388,296 391,282 389,266',
             'M 377,247 C 389,242 399,251 396,264 M 372,267 C 382,260 389,263 389,273 C 389,284 383,292 375,294',
             'M 224,422 C 245,414 260,399 271,378 M 262,438 C 264,469 272,494 290,514',
         ]),
]


def inside(x, y, polygon):
    hit = False
    for (ax, ay), (bx, by) in zip(polygon, polygon[1:] + polygon[:1]):
        if (ay > y) != (by > y) and x < (bx-ax) * (y-ay) / (by-ay) + ax:
            hit = not hit
    return hit


def simplify(points, tolerance=0.9):
    if len(points) < 3:
        return points
    ax, ay = points[0]
    bx, by = points[-1]
    dx, dy = bx-ax, by-ay
    denom = dx*dx + dy*dy
    distances = []
    for x, y in points[1:-1]:
        t = min(1, max(0, ((x-ax)*dx+(y-ay)*dy)/denom)) if denom else 0
        distances.append(math.hypot(x-ax-t*dx, y-ay-t*dy))
    maximum = max(distances)
    if maximum <= tolerance:
        return [points[0], points[-1]]
    index = distances.index(maximum) + 1
    return simplify(points[:index+1], tolerance)[:-1] + simplify(points[index:], tolerance)


def curve(points):
    points = simplify(points)
    if len(points) < 3:
        return 'M %.1f,%.1f L %.1f,%.1f' % (*points[0], *points[-1])
    result = ['M %.1f,%.1f' % points[0]]
    for a, b in zip(points[1:-1], points[2:]):
        result.append('Q %.1f,%.1f %.1f,%.1f' % (*a, (a[0]+b[0])/2, (a[1]+b[1])/2))
    result.append('L %.1f,%.1f' % points[-1])
    return ' '.join(result)


def trace(config, photos):
    width, height = config['width'], config['height']
    raw = subprocess.check_output([
        'magick', str(photos / config['file']), '-colorspace', 'Gray',
        '-blur', '0x1.1', '-canny', '0x1+8%+22%', '-depth', '8', 'gray:-'
    ])
    assert len(raw) == width * height
    pixels = set()
    for i, value in enumerate(raw):
        if value < 128:
            continue
        x, y = i % width, i // width
        if inside(x, y, config.get('face_region', [])):
            continue
        if config['number'] == 3 and y > 915 and x < 418:
            # Credit overlay and stage furniture are not subject contours.
            continue
        if inside(x, y, config['polygon']) or inside(x, y, config.get('extra_polygon', [])):
            pixels.add((x, y))

    graph = {}
    for x, y in sorted(pixels):
        neighbors = []
        for dx, dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
            p = (x+dx, y+dy)
            if p not in pixels:
                continue
            if dx and dy and ((x+dx,y) in pixels or (x,y+dy) in pixels):
                continue
            neighbors.append(p)
        graph[(x,y)] = neighbors

    visited = set()
    lines = []
    starts = [p for p in graph if len(graph[p]) != 2] + list(graph)
    for start in starts:
        for neighbor in graph[start]:
            edge = tuple(sorted((start, neighbor)))
            if edge in visited:
                continue
            visited.add(edge)
            points = [start, neighbor]
            while len(graph[points[-1]]) == 2:
                options = [p for p in graph[points[-1]] if p != points[-2]]
                nxt = options[0]
                edge = tuple(sorted((points[-1], nxt)))
                if edge in visited:
                    break
                visited.add(edge)
                points.append(nxt)
            length = sum(math.dist(a,b) for a,b in zip(points, points[1:]))
            # Preserve small eye details while removing specks from costumes.
            cx = sum(p[0] for p in points)/len(points)
            cy = sum(p[1] for p in points)/len(points)
            face = 200 < cx < 400 and cy < (240 if config['number'] == 3 else 315)
            if length < (7 if face else config['min_length']):
                continue
            lines.append(dict(d=curve(points), length=round(length,1), cy=cy,
                              width=1.4 if face or length > 130 else 1.0, role='detail'))
    # Face and hair arrive first; longer structural contours precede costume detail.
    lines.sort(key=lambda p: (int(p['cy']/120), -p['length']))
    strokes = [dict(d=d, width=w, role='contour') for d,w in config.get('face_strokes', [])]
    strokes += [dict(d=d, width=1.6, role='contour') for d in config['manual']]
    contour_count = len(strokes)
    for i, p in enumerate(lines):
        p.pop('cy')
        strokes.append(p)
    for i, p in enumerate(strokes):
        p['delay'] = round(0.0 if i < contour_count else 0.13+0.36*(i-contour_count)/max(1,len(lines)-1), 4)
        p['duration'] = 0.52 if p['role'] == 'contour' else 0.22
    return dict(id=config['id'], number=config['number'], viewBox=config['crop'], strokes=strokes)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--photos-dir', type=Path, default=ROOT/'source-photos',
                        help='Directory containing the three original photos (only needed to retrace)')
    args = parser.parse_args()
    missing = [p['file'] for p in PORTRAITS if not (args.photos_dir/p['file']).is_file()]
    if missing:
        parser.error('Original photos missing from %s: %s. The bundled vectors work without them.'
                     % (args.photos_dir, ', '.join(missing)))
    assets = ROOT/'assets'
    assets.mkdir(exist_ok=True)
    portraits = [trace(config, args.photos_dir) for config in PORTRAITS]
    for portrait in portraits:
        svg = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="%s">' % ' '.join(map(str, portrait['viewBox'])),
               '<title>Elvis Presley — traced from photograph #%d</title>' % portrait['number'],
               '<g fill="none" stroke="#fff0d5" stroke-linecap="round" stroke-linejoin="round">']
        svg.extend('<path stroke-width="%s" d="%s"/>' % (p['width'],p['d']) for p in portrait['strokes'])
        svg.append('</g></svg>')
        (assets/(portrait['id']+'.svg')).write_text('\n'.join(svg)+'\n')
    data = json.dumps(portraits, separators=(',',':'))
    (assets/'portraits.json').write_text(data+'\n')
    # Bound scene-graph cost: about 40 animated paths per portrait, grouping
    # similarly timed short strokes into compound SVG paths.
    grouped = []
    for portrait in portraits:
        contours = [p for p in portrait['strokes'] if p['role'] == 'contour']
        detail = [p for p in portrait['strokes'] if p['role'] == 'detail']
        batch_size = max(1, math.ceil(len(detail)/32))
        groups = list(contours)
        for i in range(0, len(detail), batch_size):
            batch = detail[i:i+batch_size]
            groups.append(dict(d=' '.join(p['d'] for p in batch), width=1.2,
                               delay=batch[0]['delay'], duration=0.25, role='detail'))
        grouped.append({**portrait, 'strokes':groups})
    (ROOT/'plugin/nextg.elvis-unlock/Portraits.js').write_text('.pragma library\nvar portraits = '+json.dumps(grouped,separators=(',',':'))+';\n')
    print('\n'.join('%s: %d SVG strokes' % (p['id'],len(p['strokes'])) for p in portraits))


if __name__ == '__main__':
    main()
