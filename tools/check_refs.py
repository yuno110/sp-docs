# -*- coding: utf-8 -*-
"""정본 전 문서의 상호 참조를 검증한다.

    python tools/check_refs.py

검사하는 것 둘.

1. **링크 대상 파일이 있는가** — `[...](other.md)` 의 `other.md` 가 실제로 있는가
2. **라벨의 절 번호가 대상 문서에 있는가** — `[tech-stack.md §5.3](tech-stack.md)` 에서
   `tech-stack.md` 에 `## 5.3` 또는 그 하위 제목이 있는가

깨진 참조가 있으면 **종료 코드 1** 이다. 정본을 개정한 뒤 반드시 돌린다
(process/review-policy.md §8).

절 번호는 제목에서 수집하며 상위 번호를 함께 등록한다 — `### 5.3` 이 있으면
`§5` 도 유효한 참조로 본다. 문서 안에서 자기 절을 가리키는 `§N` 은 검사하지
않는다(링크가 없으므로 대상이 자기 자신이고, 오타를 잡을 이득이 작다).
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))).replace('\\', '/')

HEADING = re.compile(r'^#{2,4}\s+([0-9]+(?:\.[0-9]+)*)[.\s]', re.M)
LINK = re.compile(r'\[([^\]]*?)\]\(([^)]+?\.md)\)')
SEC = re.compile(r'§\s*([0-9]+(?:\.[0-9]+)*)')

FENCE = re.compile(r'^```.*?^```', re.M | re.S)
CODESPAN = re.compile(r'`[^`\n]*`')


def strip_code(s):
    """코드 블록·인라인 코드를 지운다.

    그 안의 `[a.md §1](a.md)` 는 링크가 아니라 **예시**다. 지우지 않으면 링크
    문법을 설명하는 문서가 자기 예시 때문에 깨진 참조로 보고된다 — 이 파일의
    설명을 review-policy.md §8 에 옮겨 적었을 때 실제로 그랬다.
    """
    return CODESPAN.sub('', FENCE.sub('', s))


def collect():
    """문서마다 {경로: 그 문서가 가진 절 번호 집합} 을 만든다."""
    sections, files = {}, []
    for dirpath, _dirnames, filenames in os.walk(ROOT):
        if '.git' in dirpath.replace('\\', '/').split('/'):
            continue
        for fn in sorted(filenames):
            if not fn.endswith('.md'):
                continue
            full = os.path.join(dirpath, fn).replace('\\', '/')
            files.append(full)
            nums = set()
            text = strip_code(io.open(full, encoding='utf-8').read())
            for m in HEADING.finditer(text):
                n = m.group(1)
                nums.add(n)
                parts = n.split('.')
                for i in range(1, len(parts)):
                    nums.add('.'.join(parts[:i]))
            sections[full] = nums
    return sections, files


def main():
    sections, files = collect()
    bad, nolink = [], []

    for f in files:
        s = strip_code(io.open(f, encoding='utf-8').read())
        base = os.path.dirname(f)
        for m in LINK.finditer(s):
            label, target = m.group(1), m.group(2)
            secs = SEC.findall(label)
            if not secs:
                continue
            tgt = os.path.normpath(os.path.join(base, target)).replace('\\', '/')
            if tgt not in sections:
                nolink.append((f, target))
                continue
            for n in secs:
                if n not in sections[tgt]:
                    bad.append((f, target, n))

    def rel(p):
        return p.replace(ROOT + '/', '')

    out = sys.stdout
    out.write('document count: %d\n\n' % len(files))

    if bad:
        out.write('=== broken section refs (%d) ===\n' % len(bad))
        for f, t, n in bad:
            out.write('  %-38s -> %-28s section %s\n' % (rel(f), t, n))
    else:
        out.write('section refs: OK\n')

    out.write('\n')

    if nolink:
        out.write('=== missing link targets (%d) ===\n' % len(nolink))
        for f, t in nolink:
            out.write('  %-38s -> %s\n' % (rel(f), t))
    else:
        out.write('link targets: OK\n')

    return 1 if (bad or nolink) else 0


if __name__ == '__main__':
    sys.exit(main())
