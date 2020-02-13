import os
import re
import sys

refpat = re.compile(r'<span class="ref">\s*\[\s*<a\s+((?:id|href)=[^>]+)>([^<]+)</a>\s*\]\s*</span>')
endpat = re.compile(r'<p id="note([a-z0-9]+)"><span class="ref">\[<a href="#ref([a-z0-9]+)">\s*([a-z0-9]+)\s*</a>\]</span>')
idpat = re.compile(r'(?:^|\W)id="([^"]+)"')
hrefpat = re.compile(r'(?:^|\W)href="([^"]+)"')

class RefOrNote:
    def __init__(self, match):
        self.match = match

def find_all_refs(txt, first_note):
    return [RefOrNote(x) for x in refpat.finditer(txt) if x.start() < first_note]


def find_all_notes(txt):
    return [RefOrNote(x) for x in endpat.finditer(txt)]


def check_matches(refs, notes):
    refs_by_frag = {}
    for r in refs:
        ok = True
        attribs = r.match.group(1)
        try:
            r.id = idpat.search(attribs).group(1)
            r.href = hrefpat.search(attribs).group(1)
            r.inner = r.match.group(2).strip()
            r.frag = r.id[3:]
        except:
            ok = False
            raise
        if not ok or (r.href != '#note' + r.frag or r.inner != r.frag):
            raise Exception("Bad endnote reference: %s" % r.match.group(0))
        if ok:
            refs_by_frag[r.frag] = r
    notes_by_frag = {}
    for n in notes:
        frag = n.match.group(1)
        if n.match.group(2) != frag or n.match.group(3) != frag:
            raise Exception("Bad endnote: %s" % n.match.group(0))
        notes_by_frag[frag] = n
    for key in refs_by_frag:
        if key not in notes_by_frag:
            raise Exception("Missing an endnote for ref to #note%s" % key)
    for key in notes_by_frag:
        if key not in refs_by_frag:
            raise Exception("Missing a ref for endnote note%s" % key)
    return notes_by_frag


def fix(txt):
    notes = find_all_notes(txt)
    refs = find_all_refs(txt, notes[0].match.start())
    notes_by_frag = check_matches(refs, notes)
    i = 1
    for r in refs:
        r.ex = str(i)
        notes_by_frag[r.frag].ex = str(i)
        i += 1
    fixed = txt
    for n in reversed(notes):
        fixed = fixed[:n.match.start()] + '<p id="note%s"><span class="ref">[<a href="#ref%s">%s</a>]</span>' % (
            n.ex, n.ex, n.ex) + fixed[n.match.end():]
    for r in reversed(refs):
        fixed = fixed[:r.match.start()] + '<span class="ref">[<a id="ref%s" href="#note%s">%s</a>]</span>' % (
            r.ex, r.ex, r.ex) + fixed[r.match.end():]
    return fixed

def fixend(fname):
    with open(fname, 'rt') as f:
        txt = f.read()
    fixed = fix(txt)
    print(fixed)
    if False:
        os.rename(fname, fname + '.bak')
        with open(fname, 'wt') as f:
            f.write(txt)

if __name__ == '__main__':
    fname = "trust-paradox-rebuttal.html" if len(sys.argv) == 1 else sys.argv[1]
    fixend(fname)