a script that given a directory of images generates a spritesheet image and the metadata expected by cocos2d.

Usage is like

           pypacker -i [input] -o [output] -m [mode] -p [padding]

where

[input] = a path to a directory containing image files. (In any format supported by the python PIL module.)

[output] = a path + filename prefix for the two output files e.g. given C:\foo\bar the script will generate C:\foo\bar.png and c:\foo\bar.plist

[mode] = the packing mode. Can be either “grow” or fixed dimensions such as “256×256”. “grow” tells the algorithm to begin packing rectangles from a blank slate expanding the packing as necessary. “256×256” et. al. tell the algorithm to start with the given image size and pack sprites into it by subdivision, throwing an error if they all won’t fit.

[padding] = number of pixels to pad each sprite by, usually you want 1.

-x = optional flag indicating you want the output image file dimensions padded to the nearest power-of-two-sized square.

The algorithm I used is a recursive bin packing algorithm in which sprites are placed one-by-one into a binary tree. 

See here: 
http://jwezorek.com/2013/01/sprite-packing-in-python/

