# -*- coding: utf-8 -*-
"""生成《电控组第三次作业实施手册.docx》"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manual_kit import new_document, H
import sec_a
import sec_b

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   '电控组第三次作业实施手册.docx')


def main():
    doc = new_document()
    h = H(doc)
    sec_a.build(h)
    sec_b.build(h)
    doc.save(OUT)
    print('saved:', OUT)
    print('paragraphs:', len(doc.paragraphs), 'tables:', len(doc.tables))


if __name__ == '__main__':
    main()
