#!/usr/bin/env python
# -*- coding: utf8 -*-
import sys
import os
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement
from lxml import etree
import codecs
from libs.constants import DEFAULT_ENCODING

TXT_EXT = '.txt'
ENCODE_METHOD = DEFAULT_ENCODING

class YOLOWriter:

    def __init__(self, folder_name, filename, img_size, database_src='Unknown', local_img_path=None):
        self.folder_name = folder_name
        self.filename = filename
        self.database_src = database_src
        self.img_size = img_size
        self.box_list = []
        self.local_img_path = local_img_path
        self.verified = False

    def add_bnd_box(self, x_min, y_min, x_max, y_max, name, difficult, ocr_text=None):
        print("inside add_bnd_box : ocr_text - ", ocr_text)
        bnd_box = {'xmin': x_min, 'ymin': y_min, 'xmax': x_max, 'ymax': y_max,
                   'name': name, 'difficult': difficult, 'ocr_text': ocr_text}
        self.box_list.append(bnd_box)

    def bnd_box_to_yolo_line(self, box, class_list=[]):
        x_min = box['xmin']
        x_max = box['xmax']
        y_min = box['ymin']
        y_max = box['ymax']

        x_center = float((x_min + x_max)) / 2 / self.img_size[1]
        y_center = float((y_min + y_max)) / 2 / self.img_size[0]

        w = float((x_max - x_min)) / self.img_size[1]
        h = float((y_max - y_min)) / self.img_size[0]

        # PR387
        box_name = box['name']
        if box_name not in class_list:
            class_list.append(box_name)

        class_index = class_list.index(box_name)

        return class_index, x_center, y_center, w, h

    def save(self, class_list=[], target_file=None):
        if target_file is None:
            base_path = self.filename
            out_file = open(base_path + TXT_EXT, 'w', encoding=ENCODE_METHOD)
            ocr_file = open(base_path + '.ocr', 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(base_path)), "classes.txt")
            out_class_file = open(classes_file, 'w')
        else:
            base_path = target_file
            out_file = codecs.open(base_path, 'w', encoding=ENCODE_METHOD)
            ocr_file = codecs.open(base_path.replace('.txt', '.ocr'), 'w', encoding=ENCODE_METHOD)
            classes_file = os.path.join(os.path.dirname(os.path.abspath(base_path)), "classes.txt")
            out_class_file = open(classes_file, 'w')

        for box in self.box_list:
            class_index, x_center, y_center, w, h = self.bnd_box_to_yolo_line(box, class_list)
            if 'ocr_text' in box.keys():
                out_file.write("%d %.6f %.6f %.6f %.6f | %s\n" % (class_index, x_center, y_center, w, h, box['ocr_text']))
            else:
                out_file.write("%d %.6f %.6f %.6f %.6f\n" % (class_index, x_center, y_center, w, h))
            ocr_text = box.get('ocr_text', '')
            ocr_file.write((ocr_text if ocr_text else '') + '\n')

        for c in class_list:
            out_class_file.write(c + '\n')

        out_class_file.close()
        out_file.close()
        ocr_file.close()



class YoloReader:

    def __init__(self, file_path, image, class_list_path=None):
        # shapes type:
        # [labbel, [(x1,y1), (x2,y2), (x3,y3), (x4,y4)], color, color, difficult]
        self.shapes = []
        self.file_path = file_path

        if class_list_path is None:
            dir_path = os.path.dirname(os.path.realpath(self.file_path))
            self.class_list_path = os.path.join(dir_path, "classes.txt")
        else:
            self.class_list_path = class_list_path

        # print (file_path, self.class_list_path)

        classes_file = open(self.class_list_path, 'r')
        self.classes = classes_file.read().strip('\n').split('\n')

        # print (self.classes)

        img_size = [image.height(), image.width(),
                    1 if image.isGrayscale() else 3]

        self.img_size = img_size

        self.verified = False
        # try:
        self.parse_yolo_format()
        # except:
        #     pass

    def get_shapes(self):
        return self.shapes

    def add_shape(self, label, x_min, y_min, x_max, y_max, difficult, ocr_text=None):
        print("yolo_io.py add_shape ocr_text = ", ocr_text)
        points = [(x_min, y_min), (x_max, y_min), (x_max, y_max), (x_min, y_max)]
        # OCR text added as 5th element in tuple
        self.shapes.append((label, points, None, None, difficult, ocr_text))

    def yolo_line_to_shape(self, class_index, x_center, y_center, w, h):
        label = self.classes[int(class_index)]

        x_min = max(float(x_center) - float(w) / 2, 0)
        x_max = min(float(x_center) + float(w) / 2, 1)
        y_min = max(float(y_center) - float(h) / 2, 0)
        y_max = min(float(y_center) + float(h) / 2, 1)

        x_min = round(self.img_size[1] * x_min)
        x_max = round(self.img_size[1] * x_max)
        y_min = round(self.img_size[0] * y_min)
        y_max = round(self.img_size[0] * y_max)

        return label, x_min, y_min, x_max, y_max

    def parse_yolo_format(self):
        ocr_path = self.file_path.replace('.txt', '.ocr')
        ocr_texts = []
        if os.path.exists(ocr_path):
            with open(ocr_path, 'r', encoding=ENCODE_METHOD) as f:
                ocr_texts = [line.strip() for line in f.readlines()]

        with open(self.file_path, 'r') as bnd_box_file:
            for i, bndBox in enumerate(bnd_box_file):
                print("bndbox = ", bndBox, " from file ", bnd_box_file)
                class_index, x_center, y_center, w, h = bndBox.strip().split(' ')
                label, x_min, y_min, x_max, y_max = self.yolo_line_to_shape(class_index, x_center, y_center, w, h)

                ocr_text = ocr_texts[i] if i < len(ocr_texts) else None
                # difficult flag not in YOLO format, so False by default
                print("inside parse_yolo_format in yolo_io.py: ocr_text = ", ocr_text)
                self.add_shape(label, x_min, y_min, x_max, y_max, False, ocr_text)