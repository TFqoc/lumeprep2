# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

import logging
_logger = logging.getLogger(__name__)


class IrLogging(models.Model):
    _inherit = 'ir.logging'

    account_id = fields.Many2one(comodel_name='metrc.account', string='Metrc Account', index=1, ondelete='set null')
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def _cron_archive_metrc_logs(self, batch_size=1000, level=['info', 'error', 'warning'], use_new_cursor=True):
        _logger.info('metrc.logging.archive - cron started')
        logging_fields = self.fields_get_keys()
        logging_noprefetch = self.with_context(prefetch_fields=False).search([
                        ('account_id', '!=', False),
                        ('level', 'in', level),
                    ])
        logging_count = len(logging_noprefetch)
        _logger.info('metrc.logging.archive: found %d logs.' % (logging_count))
        IrAttachment = self.env['ir.attachment'].sudo()
        logging_noprefetch = logging_noprefetch.ids
        if use_new_cursor:
            cr = registry(self._cr.dbname).cursor()
            self = self.with_env(self.env(cr=cr))
        while logging_noprefetch:
            log_batch = logging_noprefetch[:batch_size]
            loggings_batch = self.browse(log_batch)
            logging_rows = loggings_batch.export_data(logging_fields, True)['datas']
            _logger.info('metrc.logging.archive: attempting archive %d of %d remaining logs out of %d total logs.' % (len(log_batch), len(logging_noprefetch),logging_count))
            logging_noprefetch = logging_noprefetch[batch_size:]
            query = "DELETE FROM ir_logging WHERE id in %s" % (tuple(log_batch),)
            try:
                with tempdir() as zip_dir:
                    output = io.BytesIO()
                    writer = pycompat.csv_writer(output, quoting=1)
                    writer.writerow(logging_fields)
                    writer.writerows(logging_rows)
                    dt_str = datetime.now().strftime("%Y%m%d-%H%M%S")
                    csv_file_name = 'Metrc Transaction Logs %s.csv' % (dt_str)
                    zip_file_name = 'Metrc Transaction Logs %s.zip' % (dt_str)
                    with zipfile.ZipFile(os.path.join(zip_dir, zip_file_name), 'w', compression=zipfile.ZIP_DEFLATED) as myzip:
                        myzip.writestr(csv_file_name, output.getvalue())
                        myzip.close()
                    z_file = Path(os.path.join(zip_dir, zip_file_name))
                    file_data = z_file.read_bytes()
                    IrAttachment.create({'name': zip_file_name, 'datas': base64.b64encode(file_data), 'type': 'binary', 'datas_fname': zip_file_name})
                    # removing the file from the directory after attachment creation.
                    z_file.unlink()
                    with cr.savepoint():
                        cr.execute(query)
                    if use_new_cursor:
                        cr.commit()
            except OperationalError:
                _logger.info('metrc.logging.archive: Exception : %s !', exception_to_unicode(e))
                if use_new_cursor:
                    logging_noprefetch += log_batch
                    cr.rollback()
                    continue
                else:
                    raise

        if use_new_cursor:
            cr.commit()
            cr.close()
        _logger.info('metrc.logging.archive: cron ended')
        return {}