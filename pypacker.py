#----------------------------------------------------
#- pypacker: written by Joe Wezorek
#- license:  WTFPL
#- If you use this code and/or have suggestions, etc.,
#- email me at jwezorek@gmail.com

import os, os.path
import sys
import copy
from PIL import Image, ImageDraw
from optparse import OptionParser
from math import log, ceil
from metadata_gen import *

def sort_images_by_size(image_files):
    #sort by area (secondary key)
    #sorted_images = sorted(image_files, \
    #        key=lambda sprite: sprite.get_size()[0] * sprite.get_size()[1])
    #sort by max dimension (primary key)
    sorted_images = sorted(image_files, \
           key=lambda img_pair: max(img_pair.get_size()[0], img_pair.get_size()[1]))
    return sorted_images

#----------------------------------------------------------------------

class sprite_info:
    def __init__(self, name, img, padding):
        self.sprite_name = os.path.splitext(name)[0] #strip the extension...
        self.image = img
        self.padding = padding
    def get_size(self):
        (wd,hgt) = self.image.size;
        return (wd + 2*self.padding, hgt + 2*self.padding)


#----------------------------------------------------------------------

class rectangle:
    def __init__(self, x=0, y=0, wd=0, hgt=0):
        self.x = x
        self.y = y
        self.wd = wd
        self.hgt = hgt
    def split_vert(self,y):
        top = rectangle(self.x, self.y, self.wd, y)
        bottom = rectangle(self.x, self.y+y, self.wd, self.hgt-y)
        return (top, bottom)
    def split_horz(self,x):
        left = rectangle(self.x, self.y, x, self.hgt)
        right = rectangle(self.x+x, self.y, self.wd-x, self.hgt)
        return (left,right)
    def area(self):
        return self.wd * self.hgt
    def max_side(self):
        return max(self.wd, self.hgt)
    def can_contain(self, wd, hgt):
        return self.wd >= wd and self.hgt >=hgt
    def is_congruent_with(self, wd, hgt):
        return self.wd == wd and self.hgt ==hgt
    def to_string(self):
        return "<(%d, %d) - (%d, %d)>" % (self.x, self.y, self.wd, self.hgt)
    def should_split_vertically(self, wd, hgt):
        if (self.wd == wd):
            return True
        elif (self.hgt == hgt):
            return False
        #TODO: come up with a better heuristic
        vert_rects = self.split_vert(hgt)
        horz_rects = self.split_horz(wd)
        return vert_rects[1].area() > horz_rects[1].area()
    def should_grow_vertically(self, wd, hgt):
        can_grow_vert = self.wd >= wd
        can_grow_horz = self.hgt >= hgt
        if (not can_grow_vert and not can_grow_horz):
            raise Exception("Unable to grow!")
        if (can_grow_vert and not can_grow_horz):
            return True
        if (can_grow_horz and not can_grow_vert):
            return False
        return (self.hgt + hgt < self.wd + wd)


#----------------------------------------------------------------------
class rect_node:
    def __init__(self, sprite, rect=(), children=()):
        self.rect = rect
        self.sprite = sprite;
        self.children = children

    def clone(self):
        if (self.is_leaf()):
            return rect_node(copy.copy(self.sprite), copy.copy(self.rect))
        else:
            return rect_node(copy.copy(self.sprite), copy.copy(self.rect),\
                            (self.children[0].clone(), self.children[1].clone()))

    def is_leaf(self):
        return not self.children

    def is_empty_leaf(self):
        return (self.is_leaf() and not self.sprite)

    def split_node(self, sprite):
        if (not self.is_leaf):
            raise Exception("Attempted to split non-leaf")

        (img_wd, img_hgt) = sprite.get_size()
        if (not self.rect.can_contain(img_wd, img_hgt)):
            raise Exception("Attempted to place an img in a node it doesn't fit")

        #if it fits exactly then we are done...
        if (self.rect.is_congruent_with(img_wd, img_hgt)):
            self.sprite = sprite
        else:
            if (self.rect.should_split_vertically(img_wd, img_hgt)):
                vert_rects = self.rect.split_vert(img_hgt)
                top_child = rect_node((), vert_rects[0])
                bottom_child = rect_node((), vert_rects[1])
                self.children = (top_child, bottom_child)
            else:
                horz_rects = self.rect.split_horz(img_wd)
                left_child = rect_node((), horz_rects[0])
                right_child = rect_node((), horz_rects[1])
                self.children = (left_child, right_child)
            self.children[0].split_node(sprite)

    def grow_node(self, sprite):
        if (self.is_empty_leaf()):
            raise Exception("Attempted to grow an empty leaf")
        (img_wd, img_hgt) = sprite.get_size()
        new_child = self.clone()
        self.img=()
        self.img_name=()
        if self.rect.should_grow_vertically(img_wd,img_hgt):
            self.children = (new_child,\
                rect_node((), rectangle(self.rect.x, self.rect.y+self.rect.hgt, self.rect.wd, img_hgt)))
            self.rect.hgt += img_hgt
        else:
            self.children= (new_child,\
                rect_node((), rectangle(self.rect.x+self.rect.wd, self.rect.y, img_wd, self.rect.hgt)))
            self.rect.wd += img_wd
        self.children[1].split_node(sprite)

    def to_string(self):
        if (self.is_leaf()):
            return "[ %s: %s ]" % (self.img_name, self.rect.to_string())
        else:
            return "[ %s: %s | %s %s]" % \
                    (self.img_name, self.rect.to_string(), self.children[0].to_string(), self.children[1].to_string())

    def render(self, img):
        if (self.is_leaf()):
            if (self.sprite):
                pad = self.sprite.padding
                img.paste(self.sprite.image, (self.rect.x + pad, self.rect.y + pad))
        else:
            self.children[0].render(img)
            self.children[1].render(img)

#----------------------------------------------------------------------

def find_empty_leaf(node, sprite):
    (img_wd, img_hgt) = sprite.get_size()
    if (node.is_empty_leaf()):
        return node if node.rect.can_contain(img_wd, img_hgt) else ()
    else:
        if (node.is_leaf()):
            return ()
        leaf = find_empty_leaf(node.children[0], sprite)
        if (leaf):
            return leaf
        else:
            return find_empty_leaf(node.children[1], sprite)

def pack_images( sprites, grow_mode, max_dim):
    root=()
    while sprites:
        sprite = sprites.pop()
        if not root:
            if (grow_mode):
                (wd,hgt) = sprite.get_size()
                root = rect_node((), rectangle(0, 0, wd, hgt))
            else:
                root = rect_node((), rectangle(0, 0, max_dim[0], max_dim[1]))
            root.split_node(sprite)
            continue
        leaf = find_empty_leaf(root, sprite)
        if (leaf):
            leaf.split_node(sprite)
        else:
            if (grow_mode):
                root.grow_node(sprite)
            else:
                raise Exception("Can't pack images into a %d by %d rectangle." % max_dim)
    return root

def nearest_power_of_two(n):
    #there's probably some cleverer way to do this... but take the log base-2,
    #and raise 2 to the power of the next integer...
    log_2 = log(n) / log(2)
    return int(2**(ceil(log_2)))

def flatten_nodes(node):
    if (node.is_leaf()):
        if (node.sprite):
            return [node]
        else:
            return ()
    else:
        left = flatten_nodes(node.children[0])
        right = flatten_nodes(node.children[1])
        if (left and not right):
            return left
        if (right and not left):
            return right
        if (left and right):
            return left + right
        else:
            return ()

def generate_sprite_sheet_img(packing, image_filename, should_make_power_of_two):
    sz = ()
    if (not should_make_power_of_two):
        sz = (packing.rect.wd, packing.rect.hgt)
    else:
        padded_dim = nearest_power_of_two(max(packing.rect.wd, packing.rect.hgt))
        sz = (padded_dim, padded_dim)

    sprite_sheet = Image.new('RGBA', sz )
    packing.render(sprite_sheet)
    sprite_sheet.save(image_filename, 'PNG')
    return sprite_sheet

def generate_sprite_sheet_metadata(packing, filename_prefix, sz, ss_format):
    nodes = flatten_nodes(packing)
    metadata_generator = get_spritesheet_format(ss_format, nodes, sz)
    if (metadata_generator == None):
        raise Exception("unknown sprite sheet format")
    filename = filename_prefix + "." + metadata_generator.get_extension()
    metadata_generator.write_metadata(filename)

def generate_sprite_sheet(packing, dest_file_prefix, should_make_power_of_two, ss_format):
    image_filename = dest_file_prefix + ".png"
    img = generate_sprite_sheet_img(packing, image_filename, should_make_power_of_two)
    generate_sprite_sheet_metadata(packing, dest_file_prefix, img.size, ss_format)

def get_images(image_dir, padding):
    images = []
    for file in os.listdir(image_dir):
        img = ()
        try:
            img = Image.open(image_dir + os.sep + file)
        except:
            continue
        if (not images):
            images = [sprite_info(file, img, padding)]
        else:
            images.append(sprite_info(file, img, padding))
    return images

def get_spritesheet_format(format_option, nodes, sz):
    dict_formats = {
        'plist' : plist_generator(nodes, sz),
        'json' : json_generator(nodes, sz)
    }
    return dict_formats[format_option] if (format_option in dict_formats) else None

#----------------------------------------------------------------------


def main():

    parser = OptionParser(usage="usage: %prog [options]",
                          version="%prog 1.0")

    parser.add_option("-o", "--output_filename",
                      action="store",
                      default="pypack_output",
                      help="filename (minus extensions) of the two output files")

    parser.add_option("-i", "--input_dir",
                      action="store",
                      default="",
                      help="input directory")

    parser.add_option("-m", "--mode",
                      action="store",
                      default="grow",
                      help="packingmode")

    parser.add_option("-p", "--padding",
                      action="store_true",
                      default=0,
                      help="padding")

    parser.add_option("-x", "--power_of_two",
                      action="store_true",
                      default=False,
                      help="pad to nearest power of two")

    parser.add_option("-f", "--format",
                      action="store",
                      default="plist",
                      help="format of spritesheet metadata (currently must be plist or json)")

    try:
        (options, args) = parser.parse_args()

        images = get_images(options.input_dir, options.padding)
        sorted_images = sort_images_by_size( images )

        max_dim=()
        if (options.mode != "grow"):
            dim_strings = options.mode.split("x")
            if (len(dim_strings) != 2):
                raise Exception("Invalid packing mode")
            try:
                max_dim = (int(dim_strings[0]), int(dim_strings[1]))
            except ValueError:
                raise Exception("Invalid packing mode")

        image_packing = pack_images(sorted_images, not max_dim, max_dim )
        generate_sprite_sheet(image_packing, options.output_filename, options.power_of_two, options.format)
    except Exception as e:
        print "\nError: %s" % e
        return

    print "\nPacking %s successful.\nGenerated:\n   %s\n" % \
            ( options.input_dir, options.output_filename + ".png + " + options.format + " metadata")

if __name__ == '__main__':
    main()