import os, sys
from os import path as osp
import logging
import re
import shutil

DEBUG = False

def get_logger(filename, verb_level='info', name=None, method=None):
    """filename: 保存log的文件名
        name：log对象的名字，可以不填
    """
    level_dict = {'debug': logging.DEBUG, 'info': logging.INFO, 'warn': logging.WARNING}
    formatter = logging.Formatter(
            "[%(asctime)s][%(filename)s][line:%(lineno)d][%(levelname)s] %(message)s"
        )
    logger = logging.getLogger(name)
    logger.setLevel(level_dict[verb_level])

    if method == 'w2file':
        fh = logging.FileHandler(filename, mode='w', encoding='utf-8')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    sh = logging.StreamHandler()
    sh.setFormatter(formatter)
    logger.addHandler(sh)

    return logger


class typora_parser:
    """this parser will take a typora markdown file as input and operate on it:
    0. take path of markdown file and recursively get all paths in markdown files dir
    1. extract all "![]()" patterns in md file
    2. filter out all hyper-links, e.g.: ![xxx](https://github.com/typora/typora-issues)
        notice: there are some hyper-links rendered as image or contents, it needs to be classified
        either manually or automatically for further conversion
    3. extract all local path from patterns and loop through them to classify is absolute or relative path
    4. for absolute path, print them out if any
    5. for relative path, match them with all paths list in the markdown's dir
    6. check if there is any unmatched relative path (potential broken img link)
    7. print out the all-paths list if it is not empty (potential removable duplicates)
    """
    
    def __init__(self, path) -> None:
        # self.mdpath = osp.abspath(path)
        self.root = osp.abspath(path)
        self.all_files = []
        self.ext_all_files(self.root)
        logger.info(f"Total file counts in this folder: {len(self.all_files)}")
        if logging.DEBUG >= logger.root.level:
            logger.debug("All files in this folder:")
            for a in self.all_files:
                logger.debug(a)
        self.ext_mds()
        self.check_files()
    
    def ext_mds(self):
        self.mdpaths = []
        for f in self.all_files:
            if '.md' in f:
                self.mdpaths.append(f)
        for f in self.mdpaths:
            self.all_files.remove(f)
        logger.info(f"All mds in this folder: {self.mdpaths}")
    
    def check_files(self, warn_fmt = ['.md', '.pdf']):
        for f in self.all_files:
            for fmt in warn_fmt:
                if fmt in f:
                    logger.warn(f"Warnning format({fmt}) detected: {f}")
    
    def ext_all_files(self, dir):
        ps = os.listdir(dir)
        ps = [osp.join(dir,p) for p in ps]
        try:
            ps.remove(self.mdpath)
        except:
            pass
        fs = [p for p in ps if osp.isfile(p)]
        self.all_files.extend(fs)
        for f in fs:
            ps.remove(f)
        for d in ps:
            self.ext_all_files(d)
    
    def img_path_extractor(self, remove=True):
        """所有插入图片的格式是：![]()，这里loop md文档，然后把所有()里的路径抓出来,
        注意：
        因为可能有hyperlink图片和absolute path的图片，默认都要把这两种去掉
        因为可能有多个图片引用同一地址的情况，所以要做一下set处理
        """
        # txt = "test ![fdajk fda ](media/a/bfds.png) testse ![fdajfdsk](meddifds a/b/bfds.png) test"
        logger.info(f"\nImg path extracting... check for hyper-link & abs path, remove method=={remove}")
        
        x = re.compile("\!\[.*?\]\((.*?)\)")
        
        def ext_path(txt):
            return re.findall(x, txt)

        def check_path(fp, md):
            """check if the img path is
            1. hyper link, 2. absolute path
            then print them out and remove from path if remove==True
            """
            hps = [r"https://", r"http://"]
            # self.all_imgs.append(r"http://img.freepik.com/free-photo/abstract-")
            # self.all_imgs.append(r"https://img.freepik.com/free-photo/abstract-grunge-decorative-relief-navy-blue-stucco-wall-texture-wide-angle-rough-colored-background_1258-28311.jpg?w=2000")
            # self.all_imgs.append(r"C:/fdsjl/fd.png")
            for hp in hps:
                if hp in fp:
                    logger.warn(f"HyperLink detected in md imgpath: \n{fp}\n{md}")
                    return True
            if osp.isabs(fp):
                logger.warn(f"AbsolutePath detected in md imgpath: \n{fp}\n{md}")
                return True
            return False

        self.all_imgs = []
        for md in self.mdpaths:
            dir = osp.dirname(md)
            with open(md, 'r', encoding='utf8') as fp:
                line = fp.readline()
                while line:
                    ps = ext_path(line)
                    if len(ps) != 0:
                        rs = []
                        # check if its hyperlink or abs path, then remove it from img_path
                        for p in ps:
                            if remove and check_path(p, md):
                                rs.append(p)
                        for r in rs:
                            ps.remove(r)
                        # convert relative path to abs path
                        ps = [osp.join(dir, p) for p in ps]
                        self.all_imgs.extend(ps)
                    line = fp.readline()
        self.all_imgs = list(set(self.all_imgs))
    
    def get_red_paths(self):
        self.red_paths = self.all_files.copy()
        self.all_imgs = [osp.abspath(osp.join(self.root,i)) for i in self.all_imgs]
        for i in self.all_imgs:
            try:
                self.red_paths.remove(i)
                logger.debug(f"{i} in dir")
            except Exception as e:
                logger.error(f"Img path ({i}) is not in the dir!")
        if len(self.red_paths) != 0:
            logger.info("\nAll redundant paths are:")
            for i in self.red_paths:
                logger.info(f"{i}")
        else:
            logger.info("There is no redundant path!")

    def remove_red_paths(self, method='manual_veri'):
        if method == 'manual_veri':
            tar = osp.join(self.root, 'red_files')
            os.makedirs(tar, exist_ok=True)
            for i in self.red_paths:
                # i = osp.basename(i)
                o = i.replace(self.root, tar)
                d = osp.dirname(o)
                if not osp.exists(d):
                    os.makedirs(d)
                shutil.move(i, o)
            logger.info(f"All redundant files are moved to {tar} waiting for manual verification")

   
if __name__=='__main__':
    
    logger = get_logger(filename='./log.log', verb_level='info', method='w2file')
    
    tp = typora_parser(path=r'C:\Users\Administrator\Desktop\test\tmp')
    
    tp.img_path_extractor()
    
    tp.get_red_paths()
    if len(tp.red_paths) != 0:
        tp.remove_red_paths(method='manual_veri')
    