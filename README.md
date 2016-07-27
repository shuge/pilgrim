# About

A Python imaging library extensions for dds, blp, ftex and icon image format processing.

This package is not create from scratch, original is here,
http://nullege.com/codes/show/src%40p%40i%40pilgrim-HEAD%40pilgrim .


## Installation

    pip install pilgrim
    pip install helper_string
    

## Usage

    import pilgrim.utils
    import helper_string
    import os
       
    full_path = '/path/to/a.dds'
    full_path = helper_string.HelperString.to_uni(full_path)
    
    filename = os.path.basename(full_path)
    fn, ext = os.path.splitext(filename)
    
    decoder =  pilgrim.utils.getDecoder(full_path)
    im = decoder(full_path)
    print(im.size)
    im.save(fn + ".png")



## See also

https://github.com/python-pillow/Pillow/issues/252  

http://directpython11.sourceforge.net/docs/dds.html
