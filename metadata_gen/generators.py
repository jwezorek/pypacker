class metadata_gen:
    def __init__(self):
        pass
    def write_head(self, f, nodes, sz):
        raise Exception("no write_head")
    def write_node(self, f, node, index):
        raise Exception("no write_node")
    def write_tail(self, f, nodes, sz ):
        raise Exception("no write_tail")
    def get_extension(self):
        raise Exception("no get_extension")
    def write_metadata(self, filename, nodes, sz):
        index = 0
        f = open(filename, 'w')
        self.write_head(f, nodes, sz)
        for node in nodes:
            self.write_node(f, node, index)
            index == 1
        self.write_tail(f, nodes, sz)
        f.close()

#----------------------------------------------------------------------------------------------------------------------

class plist_generator(metadata_gen):
    def __init__(self):
        metadata_gen.__init__(self)

    def write_head(self, f, nodes, sz):
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n' \
                '<!DOCTYPE plist PUBLIC "-//Apple Computer//DTD PLIST 1.0//EN" ' \
                '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n' \
                '<plist version="1.0">\n<dict>\n<key>frames</key>\n<dict>\n')

    def write_node(self, f, node, index):
        (wd, hgt) = node.sprite.image.size
        pad = node.sprite.padding
        f.write("<key>%s</key>\n" % (node.sprite.sprite_name))
        f.write("<dict>\n")
        f.write("    <key>frame</key>\n")
        f.write("    <string>{{%d,%d},{%d,%d}}</string>\n" % (node.rect.x + pad, node.rect.y + pad, wd, hgt))
        f.write("    <key>offset</key>\n")
        f.write("    <string>{0,0}</string>\n")
        f.write("    <key>rotated</key>\n")
        f.write("    <false/>\n")
        f.write("    <key>sourceColorRect</key>\n")
        f.write("    <string>{{0,0},{%d,%d}}</string>\n" % (wd, hgt))
        f.write("    <key>sourceSize</key>\n")
        f.write("    <string>{%d,%d}</string>\n" % (wd, hgt))
        f.write("</dict>\n")

    def write_tail(self, f, nodes, sz ):
        f.write("</dict>\n<key>metadata</key>\n<dict>\n")
        f.write("    <key>format</key>\n" \
                "    <integer>2</integer>\n" \
                "    <key>size</key>\n" \
                "    <string>{%d,%d}</string>\n" % sz)
        f.write("</dict>\n</dict>\n</plist>")

    def get_extension(self):
        return "plist"

#----------------------------------------------------------------------------------------------------------------------

class json_generator(metadata_gen):
    def __init__(self):
        metadata_gen.__init__(self)

    def write_head(self, f, nodes, sz):
        f.write("{\n")

    def write_node(self, f, node, index):
        (wd, hgt) = node.sprite.image.size
        pad = node.sprite.padding
        f.write('    "%s" : ' % (node.sprite.sprite_name))
        f.write('[ %d, %d, %d, %d ], ' % (node.rect.x + pad, node.rect.y + pad, wd, hgt))
        f.write('"index" : %d },\n' % (index))

    def write_tail(self, f, nodes, sz ):
        f.write("}\n")

    def get_extension(self):
        return "json"

