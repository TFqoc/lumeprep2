import os
import sys
import re
import Image
import ImageDraw
import ImageStat
import tempfile
import subprocess
from numpy import matrix
from numpy import linalg

import logging
log = logging.getLogger("scan")

ZBAR_LIB_PATH = "/opt/local/lib/python2.6/site-packages/"
sys.path.insert(0, ZBAR_LIB_PATH) # XXX check if 0 is OK for openerp

try:
    import zbar
except ImportError, e:
    message = "Module zbar not found in %s" % ZBAR_LIB_PATH
    e.args = (message, )
    raise e


import checkboxes

HORZ=0
VERT=1

class ScannerException(Exception):
    pass

class Scanner(object):
    """Scans QR code and checkboxes values from training questionnaire.
    The scanner object has states: first, set the image_path (set_image_path), then extract QR code data (get_qrcode_data), and
    finally read form values (detect_checkboxes_values).

    Actual QR code bottom-left location is (18cm, 2.4cm), that is approximately (510.24, 68.03) at 72dpi.
    QR code is 58 dots large at 72 dpi.

    float:in_res: input resolution (rml2pdf default is 72 dpi), the reference resolution for checkboxes position
    float:out_res: output resolution of an image (determined by calibration)
    config:list containing in that order:
        checked_threshold: checkbox is considered checked below this histogram mean value (determined by calibration)
        deviance_threshold: checkbox is considered checked above this histogram stddev value (determined by calibration)
        deviance_max: interval size in which we will consider using deviance
    bool:debug: used to draw on images for calibration
    """

    def __init__(self, in_res=72, out_res=200, checked_threshold=200, deviance_threshold=20, deviance_max=65, auto_resolution=False, debug=False):
        self.in_res = in_res
        self.out_res = out_res
        self.checked_threshold = checked_threshold
        self.deviance_threshold = deviance_threshold
        self.auto_resolution = auto_resolution
        self.deviance_max = deviance_max
        self.debug = debug

        self.scanner = zbar.ImageScanner()
        self.qrcode_pattern_gtype = [str, int, int]
        self.qrcode_pattern = re.compile(r"^([a-z.]+)-(\d+)-(\d+)$") # model-dataID-pageNum
        self.qrcode_region = lambda w, h: [3*w/4, 0, w, h/7] # top_right_corner
        self._image = None
        self._image_name = None
        self._image_path = None
        self._debug_image = None

    def set_image_path(self, path, name="Unknown"):
        self._image_path = path
        self._image = Image.open(self._image_path).convert('L')
        self._image_name = name

    def get_image(self):
        return self._image

    # quick debug facility
    def display(self, image):
        fp, tempname = tempfile.mkstemp(suffix='.jpg')
        try:
            image.save(tempname)
            sp = subprocess.Popen(["eog", tempname])
            sp.wait()
        finally:
            os.unlink(tempname)

    def extract_qrcode(self):
        """Returns list of QR codes embedded in an 8-bit grayscale image."""

        cropped = self._image.crop(self.qrcode_region(*self._image.size))
        width, height = cropped.size
        raw = cropped.tostring()
        zimage = zbar.Image(width, height, 'Y800', raw)
        self.scanner.scan(zimage)
        try:
            symbs = zimage.symbols
            return list(zimage.symbols)
        except AttributeError:
            return [] # no barcode found!

    def parse_qrcode_data(self, zbar_symbol):
        """Should return embedded data (participation_id, page_num)."""

        raw_data = zbar_symbol.data.strip()
        match = self.qrcode_pattern.match(raw_data)
        if not match:
            log.error("QR code data %s do not match pattern %s" % (raw_data, self.qrcode_pattern))
            data = ('', 0, 0)
        else:
            data = [ self.qrcode_pattern_gtype[i](g) for i, g in enumerate(match.groups()) ] # FIXME int could raise exception

        return data

    def guess_deformation(self, qrcode_location, qrcode_offset):
        l = qrcode_location
#        log.debug("QR code location: %s", l)
        size = float(l[3][0]-l[0][0]+l[2][0]-l[1][0]+l[2][1]-l[3][1]+l[1][1]-l[0][1]) / 4
#        size += .5 # zbar underestimates the bounding box
#        log.debug("QR code size: %s", size)
        guessed_dpi = size / 58. * 72
        x = 17.79 / 2.54 * guessed_dpi # hardcoded qrcode X location
        y = (29.7-27.3) / 2.54 * guessed_dpi # hardcoded qrcode Y location
        qrcode_target_location = [(x, y-size), (x, y), (x+size, y), (x+size, y-size)]
#        log.debug("QR code translated target location: %s", qrcode_target_location)
        qrcode_target_location = [(x-qrcode_offset[0], y-qrcode_offset[1]) for (x, y) in qrcode_target_location]
#        log.debug("QR code target location: %s", qrcode_target_location)

        qtl = qrcode_target_location
        A = matrix([[qtl[0][0], qtl[0][1], 1], [qtl[1][0], qtl[1][1], 1], [qtl[2][0], qtl[2][1], 1]])
        target_x = matrix([[l[0][0]], [l[1][0]], [l[2][0]]])
        target_y = matrix([[l[0][1]], [l[1][1]], [l[2][1]]])
        Ainv = A.I
        v = Ainv * target_x
        [[a,b,c]] = v.transpose().tolist()
        w = Ainv * target_y
        [[d,e,f]] = w.transpose().tolist()

        return a,b,c,d,e,f, guessed_dpi

    def tune_symbol_location(self,loc):
        """Tunes it, since zbar is not that accurate.
        Only works if no rotation."""

        min_x = min(loc[0][0], loc[1][0])
        min_y = min(loc[0][1], loc[3][1])
        max_x = max(loc[2][0], loc[3][0])
        max_y = max(loc[1][1], loc[2][1])
        return ((min_x, min_y), (min_x, max_y), (max_x, max_y), (max_x, min_y))

    def get_qrcode_data(self):
        qrcode_list = self.extract_qrcode()
        if not qrcode_list:
            msg = "No QR code found in image %s." % self._image_name
            raise ScannerException(msg)
        self._symbol = qrcode_list[0]
        (self._model, self._participation_id, self._page_num) = self.parse_qrcode_data(self._symbol)
        return (self._model, self._participation_id, self._page_num), self._symbol.location

    def _affine_transform(self):
        # manages translation/rotation/shear/scaling of the image
        symbol_location = self.tune_symbol_location(self._symbol.location)
        (a,b,c,d,e,f, self._guessed_dpi) = self.guess_deformation(symbol_location, self.qrcode_region(*self._image.size))
#        log.debug("Affine transform coefficients: %s", (a,b,c,d,e,f))

        if (float(self.out_res) - self._guessed_dpi) / self.out_res != 1.0:#> 1.05:
            msg = "Page %s from participation %s might have been scaled from %d dpi to %f dpi."
            log.warning(msg, self._page_num, self._participation_id, self.out_res, self._guessed_dpi)

        B = matrix([[a,b],[d,e]])
        rotascale_threshold = linalg.det(B*B.T)
#        log.debug("rotascale threshold: %f", rotascale_threshold)
        if abs(1 - rotascale_threshold) > .025:
            msg = "Page %s from participation %s might have been rotated and/or scaled too much."
            log.warning(msg, self._participation_id, self._page_num)

        # only translates image, as rotation/scale/shear might not be accurate enough
        self._image = self._image.transform(self._image.size, Image.AFFINE, (1,0,c,0,1,f), Image.NEAREST)

    def detect_crop(self, image, box, ori, start, step, limit):
       """image = image
          box = bouding box
          ori = orientation (0 = horizontal, 1 = vertical)
          start = start offset
          step = step
       """
       #print(" ---- DETECT CROOOOOP ----")
       if box[3] - box[1] < 0:
           return []
       crop_list = []
       box = [ b for b in box ]
       if ori == 0:
           max = int(box[2] - box[0])
       else:
           max = int(box[3] - box[1])
       last_good = False
       for k in xrange(start, max, step):
           if ori == 0:
               dbox = [box[0]+k, box[1], box[0]+k+1, box[3]]
           else:
               dbox = [box[0], box[1]+k, box[2], box[1]+k+1]
           c = image.crop(dbox)
           s = ImageStat.Stat(c).mean[0]
#           print("S: %s" % (s))
           if s and s < limit:
               l = len(crop_list)
               if not l:
                   crop_list.append(k)
               elif l == 1:
                   if not last_good:
                       crop_list.append(k)
               elif l >= 2:
                   crop_list.pop()
                   crop_list.append(k)
           else:
               last_good = False
       return crop_list

    def scan_line(self, image, box, ori):
        c = image.crop(box)
        (c_w, c_h) = c.size
        c_data = list(c.getdata())
        crop_list = []

        if ori == HORZ:
            i = int(int(c_h/2) * c_w)
            j = int(c_w)
            k = lambda x, y, i, j, c_w, c_h: i + x
            m = j
        elif ori == VERT:
            # Vertical
            i = int(c_h)
            j = int(c_w/2)
            k = lambda x, y, i, j, c_w, c_h: x * int(c_w) + j
            m = i

        last_good = False
        for x in xrange(m):
            if not c_data[k(x, 0, i, j, c_w, c_h)]:
                l = len(crop_list)
                if not l:
                    crop_list.append(x)
                elif l == 1:
                    crop_list.append(x)
                elif l >= 2:
                    crop_list.pop()
                    crop_list.append(x)
            else:
                last_good = False

        if len(crop_list) != 2:
            return None
        return crop_list

    def try_crop_x(self, box, w_list):
        crop_region = [0, 0]
        if len(w_list) == 2:
            crop_region[0] = w_list[0]
            crop_region[1] = box[2] - (box[0] + w_list[1])

            box[2] = box[0] + w_list[1]
            box[0] = box[0] + w_list[0]
        return crop_region

    def try_crop_y(self, box, h_list):
        crop_region = [0, 0]
        if len(h_list) == 2:
            crop_region[0] = h_list[0]
            crop_region[1] = box[3] - (box[1] + h_list[1])

            box[3] = box[1] + h_list[1]
            box[1] = box[1] + h_list[0]
        return crop_region

    def reduce_box(self, box, pixels):
       cc = [ b for b in box ]
       if cc[3] - pixels > cc[1] + pixels:
           cc[1] += pixels
           cc[3] -= pixels
       if cc[2] - pixels > cc[0] + pixels:
           cc[0] += pixels
           cc[2] -= pixels
       return cc

    def detect_checkboxes_values(self, checkboxes_position):
        self._affine_transform()

        # builds cropping windows to detect checkboxes
        translate_vector = (0, -0) # reference translation needed for perfect image
        if self.auto_resolution:
            scale_factor = self._guessed_dpi / self.in_res
        else:
            scale_factor = float(self.out_res) / self.in_res # overrides guessed resolution
        enlarge_factor = .3 # TODO this impacts on the true value of checked_threshold
        checkboxes.transform(checkboxes_position, translate_vector, scale_factor, enlarge_factor)

        results = []
        h_factor = 0 # dynamic vertical scaling adjustment factor
        w_factor = 0 # dynamic horizontal scaling adjustment factor

        if self.debug:
            self._debug_image = self._image.convert('RGB')
            vertical_mode = len(checkboxes_position) > 1 and checkboxes_position[0][0] == checkboxes_position[1][0]

        point_list = [ x > 140 and 255 or 0 for x in xrange(256) ]
        self._image = self._image.point(point_list).convert('1')

        for i, bb in enumerate(checkboxes_position):
            cc = [ b for b in bb ]
            bb[0] += w_factor
            bb[2] += w_factor
            bb[1] += h_factor
            bb[3] += h_factor

            z = self._image.crop(cc)
            (z_w, z_h) = z.size
            z_d = list(z.getdata())
#            print("-------------------------------------------------------------------")
#            for zz in xrange(z_h):
#                print("%02d: %s" % (zz, z_d[zz*z_w:(zz+1)*z_w]))

            if self.debug:
                draw = ImageDraw.Draw(self._debug_image)
                coord = [(bb[0],bb[1]), (bb[0],bb[3]), (bb[2],bb[3]), (bb[2],bb[1])]
                draw.polygon(coord, outline='blue')

            # detect horizontal region to crop
            w_list = self.scan_line(self._image, bb, HORZ)
            if not w_list:
                w_list = self.detect_crop(self._image, bb, HORZ, 0, 1, 100)
            w_crop_reg = self.try_crop_x(bb, w_list)
            # if horizontal scalling occur, re-adjust dynamically the
            # checkbox position to maintain coordinate position around
            # checkbox
            crop_factor = 10
            if w_crop_reg[0] > crop_factor or w_crop_reg[1] > crop_factor:
                w_factor += (w_crop_reg[0] - w_crop_reg[1]) / 2


            # detect vertical region to crop
            h_list = self.scan_line(self._image, bb, VERT)
            if not h_list:
                h_list = self.detect_crop(self._image, bb, VERT, 0, 1, 100)
            if len(h_list) > 1 and (h_list[1] - h_list[0] <= 4):
                # We only have detected one border
                # Try to determine the direction to look to find the checkbox
                dd = bb[:]
                dd[3] = dd[1] + h_list[0]
                dd_c = self._image.crop(dd)
                dd_stat_before = ImageStat.Stat(dd_c).mean[0]

                dd = bb[:]
                dd[1] = dd[1] + h_list[1]
                dd_c = self._image.crop(dd)
                dd_stat_after = ImageStat.Stat(dd_c).mean[0]

                if dd_stat_before > dd_stat_after:
                    # 'before' is more white than 'after'
                    force_move = (h_list[0] / 2) + (h_list[1] - h_list[0])
                    bb[1] += force_move
                    bb[3] += force_move
                    h_factor += force_move
                else:
                    # 'after' is more white than 'before'
                    force_move = ((bb[3] - (bb[1] + h_list[1])) / 2) + (h_list[1] - h_list[0])
                    bb[1] -= force_move
                    bb[3] -= force_move
                    h_factor -= force_move

                if self.debug:
                    draw = ImageDraw.Draw(self._debug_image)
                    coord = [(bb[0],bb[1]), (bb[0],bb[3]), (bb[2],bb[3]), (bb[2],bb[1])]
                    draw.polygon(coord, outline='orange')

                h_list = self.detect_crop(self._image, bb, 1, 0, 1, 150)

            h_crop_reg = self.try_crop_y(bb, h_list)
            # if vertical scalling occur, re-adjust dynamically the
            # checkbox position to maintain coordinate position around
            # checkbox
            crop_factor = 2
            if h_crop_reg[0] > crop_factor or h_crop_reg[1] > crop_factor:
                h_factor += (h_crop_reg[0] - h_crop_reg[1]) / 2

            # skip checkbox border (~3 pixels)
            bb = self.reduce_box(bb, 3)

            checkbox = self._image.crop(bb)
            stat = ImageStat.Stat(checkbox)
            results.append((stat.mean[0], stat.stddev[0]))

            if self.debug:
                msg = "NUM: %02d MEAN: %.1f DEV: %.1f" % (i, stat.mean[0], stat.stddev[0])
#                log.debug(msg)

                draw = ImageDraw.Draw(self._debug_image)
                coord = [(bb[0],bb[1]), (bb[0],bb[3]), (bb[2],bb[3]), (bb[2],bb[1])]
                draw.polygon(coord, outline="red")

                coord_origin = [(cc[0],cc[1]), (cc[0],cc[3]), (cc[2],cc[3]), (cc[2],cc[1])]
                if vertical_mode:
                    x = cc[2]
                    y = cc[1]
                else:
                    x = cc[0]
                    y = cc[3] if i%2 else cc[1] - 10

                draw.text((x - 10, y), msg, fill="red")

                if self.is_checked(stat.mean[0], stat.stddev[0]):
                    draw.text((x - 10, y + 10), "x", fill="green")
                else:
                    draw.text((x - 10, y + 10), "x", fill="red")
            # self._image now displays checkboxes precinct and stats
#        if self.debug:
#            self.display(self._image)

        results = [ self.is_checked(val, dev) for val, dev in results ]
        return results

    def is_checked(self, val, dev):
        t = self.checked_threshold
        e = self.deviance_max
        d = self.deviance_threshold

        # really dark => checked
        if val <= t-e:
            return True
        # lighty => not checked
        if val >= t+e:
            return False
        # deviance high, checkbox content should be a little cross
        # deviance low, checkbox content have been erased
        return (dev > d)

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

