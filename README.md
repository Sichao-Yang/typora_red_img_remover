# typora_red_img_remover

It works with typora markdown file, its function is: collect all redundant image files into a folder for manual removal.

Details:
    1. folder path extracting:
        1. recursively get all paths in target folder
        2. extract md files from all paths, all paths include only img paths
        3. check img_paths and warn user if there is any pdf files
    2. extract using imgpaths from md files:
        1. recursively extract all "![]()" & "<img src=''...>" patterns in md filelist
        2. filter out all hyper-links and absolute paths e.g.: ![xxx](https://github.com/typora/typora-issues)
            notice: there maybe some hyper-links rendered as image or contents, it needs to be
            either manually or automatically checked & converted.
    3. redundant path removing:
        1. remove used_img_paths from all_src_imgs to get red_imgs
        2. move red_imgs to a redundant folder
    4. manual postprocess:
        1. manual verification of those red_imgs in red folder
        2. check if there is any unmatched relative path in md files (potential broken img link)
   
It runs with python 3.x, no dependent libs needed.