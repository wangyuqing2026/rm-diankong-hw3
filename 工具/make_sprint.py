# -*- coding: utf-8 -*-
"""生成《一天冲刺清单.docx》"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from manual_kit import new_document, H
import sec_sprint

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   '一天冲刺清单.docx')


def main():
    doc = new_document()
    h = H(doc)
    sec_sprint.build(h)
    doc.save(OUT)
    print('saved:', OUT)
    print('paragraphs:', len(doc.paragraphs), 'tables:', len(doc.tables))


if __name__ == '__main__':
    main()
