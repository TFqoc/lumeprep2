from odoo import models, fields, api, tools
import logging
from PIL import Image
# import dlib
# import face_recognition

_logger = logging.getLogger(__name__)

class project_tasks_inherit(models.Model):
    _inherit = 'project.task'

    DL_or_med_image = fields.Image("Upload DL or Medical ID Image", max_width=600,
                                   max_height=300, verify_resolution=True)
    DL_or_med_image_adjusted = fields.Image("Adjusted Image", compute='_adjust_image')

    @api.onchange('DL_or_med_image')
    def _adjust_image(self):
        for record in self:
            _logger.info("In _adjust_image")

            if str(record.DL_or_med_image) == "False":
                # Bypass if no image exists when entering "edit" mode
                _logger.info("Image has not been loaded yet.")
                record.DL_or_med_image_adjusted = record.DL_or_med_image
            else:
                # If image exists and is vertically oriented, set correct
                # orientation by rotation by 90 degrees
                image = tools.base64_to_image(record.DL_or_med_image)
                _logger.info("Image type:" + str(type(image)))
                _logger.info("Image size:" + str(image.size))
                image_width = image.width
                image_height = image.height
                if image_width < image_height:
                    image = image.transpose(Image.ROTATE_90)
                # If image exists and is horizontally oriented but flipped,
                # set correct orientation by rotation by 180 degrees.
                # This probably won't work with images that are right justified.
                left_side_end = image_width/3
                right_side_start = (left_side_end*2) + 1
                left_box = (0, 0, left_side_end, image_height)
                right_box = (right_side_start, 0, image_width, image_height)
                left_cropped_image = image.crop(left_box)
                right_cropped_image = image.crop(right_box)
                left_cropped_image = left_cropped_image.convert("L")
                right_cropped_image = right_cropped_image.convert("L")
                left_pixels = left_cropped_image.getdata()
                right_pixels = right_cropped_image.getdata()
                black_thresh = 60
                left_black = 0
                for left_pixel in left_pixels:
                    if left_pixel < black_thresh:
                        left_black += 1
                ln = len(left_pixels)
                right_black = 0
                for right_pixel in right_pixels:
                    if right_pixel < black_thresh:
                        right_black += 1
                rn = len(left_pixels)
                left_blackness = left_black/float(ln)
                right_blackness = right_black/float(rn)
                _logger.info("left_blackness:" + str(left_blackness))
                _logger.info("right_blackness:" + str(right_blackness))
                if right_blackness > left_blackness:
                    image = image.transpose(Image.ROTATE_180)
                # Save the correctly oriented image
                record.DL_or_med_image_adjusted = tools.image_to_base64(image, 'PNG')
                record.DL_or_med_image = record.DL_or_med_image_adjusted
                # Find the image on the Driver's License to save as customer logo image
                # face_locations = face_recognition.face_locations(image)
                # _logger.info("Faces found" + str(face_locations))
# MEO End
