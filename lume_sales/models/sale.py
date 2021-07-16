from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.misc import formatLang
import math
import logging

logger = logging.getLogger(__name__)

ORDER_HISTORY_DOMAIN = [('state', 'not in', ('draft', 'sent'))]

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    task = fields.Many2one(comodel_name="project.task", readonly=True)
    caregiver_id = fields.Many2one('res.partner')
    is_delivered = fields.Boolean(compute='_compute_delivered', store=True)
    # For product validation
    # None state means they haven't selected any medical or adult products yet
    order_type = fields.Selection(selection=[('medical','Medical'),('adult','Adult'),('caregiver','Caregiver'),('none','None'),('merch','Merchandise')],compute="_compute_order_type")
    ordered_qty = fields.Float(compute='_compute_ordered_qty')
    fulfillment_type = fields.Selection(selection=[('store','In Store'),('delivery','Delivery'),('online','Website'),('curb','Curbside')], default='store')
    discount_ids = fields.Many2many('lume.discount')

    # Fields for the Order History Screen
    pos_terminal_id = fields.Many2one('pos.config')
    session_id = fields.Many2one('pos.session')
    fulfillment_partner_id = fields.Many2one('res.partner')
    cashier_partner_id = fields.Many2one('res.partner')
    payment_method = fields.Char()

    return_count = fields.Integer(compute="_compute_return_count")
    partner_sale_order_count = fields.Integer(related="partner_id.sale_order_count")
    partner_image = fields.Image(related='partner_id.image_1920',max_width=1920, max_height=1920,store=True)

    # Fields for Timer and colors
    timer_start = fields.Datetime(default=lambda self: fields.datetime.now())
    threshold1 = fields.Integer(related="task.project_id.so_threshold1")
    threshold2 = fields.Integer(related="task.project_id.so_threshold2")
    threshold3 = fields.Integer(related="task.project_id.so_threshold3")

    cancel_reason = fields.Selection([('no_stock','Product not in stock/unavailable'),('no_funds','Insufficient Funds'),('bad_price','Pricing Dissatisfaction'),('merge','Merged Order')])

    # Delivery Address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')

    # To show tax by group
    amount_by_group = fields.Binary(string="Tax amount by group",
        compute='_compute_taxes_by_group')

    def show_cancel_reason_wizard(self):
        return {
                'name': 'Cancel Sales Order',
                'view_mode': 'form',
                'res_model': 'sale.order.cancel.reason',
                'view_id': self.env.ref('lume_sales.sale_order_cancel_reason_view_form').id,
                'type': 'ir.actions.act_window',
                'context': {'default_order_id': self.id},
                'target': 'new'
            }

    # Override
    def action_cancel(self):
        cancel_warning = self._show_cancel_wizard()
        if cancel_warning:
            return super(SaleOrder, self).action_cancel()
        else:
            if self.task:
                self.task.write({'active':False})
            return super(SaleOrder, self).action_cancel()

    def open_notes(self):
        notes = []
        for note in self.env['lume.note'].search([('source_partner_id','=',self.partner_id.id)]):
            notes.append((4,note.id,0))
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer Notes',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(False, 'form')],
            'res_model': 'note.wizard',
            'target': 'new',
            # 'res_id': self.id,
            'context': {'default_partner_id': self.partner_id.id,'default_note_ids':notes},
        }

    def process_lot_group(self, group, batch_setting):
        group = group.sorted(key=lambda l: l.create_date)
        logger.info("SORTED GROUP: %s" % group)
        logger.info("FIRST ITEM: %s" % group[0])
        record = group[0]
        ids = []
        if record.with_context(warehouse_id=self.warehouse_id.id).stock_at_store <=  batch_setting and len(group) >= 2:
            ids.append(group[1].id)
        ids.append(record.id)
        return ids

    def open_catalog(self):
        self.ensure_one()
        # Do all the logic here, then domain is id in [ids]
        location_id = self.warehouse_id.lot_stock_id
        lots = self.env['stock.production.lot'].search([]).filtered(lambda l: location_id.id in l.quant_ids.location_id.ids).sorted(key=lambda l: l.product_id.id)
        group = False
        ids = []
        ICPSudo = self.env['ir.config_parameter'].sudo()
        batch_setting = int(ICPSudo.get_param('lume.batch_threshold'))
        logger.info("LOTS: %s" % lots)
        # This works because we sorted by product earlier
        for lot in lots:
            if not group:
                group = lot
            elif lot.product_id.id not in group.product_id.ids:
                logger.info("Lot Product ID: %s, Group IDS: %s" % (lot.product_id.id, group.product_id.ids))
                # Process group, then reset
                ids += self.process_lot_group(group, batch_setting)
                group = lot
            else:
                group |= lot
        # Catch the last group that was leftover after the loop
        ids += self.process_lot_group(group, batch_setting)
        # End logic
        domain = [('id','in',ids)]
        if self.caregiver_id:
            domain.append(('thc_type','!=','adult'))
        elif not self.partner_id.can_purchase_medical:
            domain.append(('thc_type','!=','medical'))
        elif not self.partner_id.is_over_21:
            domain.append(('thc_type','!=','adult'))
        logger.info("DOMAIN: %s" % domain)
        # Grab the first sale order line that isn't a merch product
        # show_medical = self.order_type
        return {
                'type': 'ir.actions.act_window',
                'name': 'Product Catalog',
                'view_type': 'kanban',
                'view_mode': 'kanban',
                'res_model': 'stock.production.lot',
                'view_id': self.env.ref('lume_sales.stock_log_kanban_catalog').id,
                'target': 'current',
                'res_id': self.id,
                'context': {'lpc_sale_order_id': self.id, 'type': self.order_type, 'warehouse_id':self.warehouse_id.id,'store_id':self.task.project_id.id,'pricelist_id':self.pricelist_id.id,'partner_id':self.partner_id.id},
                'domain': domain,
                # 'search_view_id': (id, name),
            }

    def open_catalog_product(self):
        self.ensure_one()
        domain = ["&","&",("type","!=","service"),("sale_ok","=",True),"|",("is_product_variant","=",False),"&",("is_product_variant","=",True),("quantity_at_warehouses","ilike",self.warehouse_id.name)]
        domain += [('type','!=','service'),('sale_ok','=',True)]
        if not self.partner_id.can_purchase_medical:
            domain.append(('thc_type','!=','medical'))
        if not self.partner_id.is_over_21:
            domain.append(('thc_type','=','adult'))
        # Grab the first sale order line that isn't a merch product
        # show_medical = self.order_type
        return {
                'type': 'ir.actions.act_window',
                'name': 'Product Catalog',
                'view_type': 'kanban',
                'view_mode': 'kanban',
                'res_model': 'product.product',
                'view_id': self.env.ref('lume_sales.product_product_kanban_catalog').id,
                'target': 'current',
                'res_id': self.id,
                'context': {'lpc_sale_order_id': self.id, 'type': self.order_type, 'warehouse_id':self.warehouse_id.id,'store_id':self.task.project_id.id,'pricelist_id':self.pricelist_id.id,'partner_id':self.partner_id.id},
                'domain': domain,
                # 'search_view_id': (id, name),
            }

    def open_order_history(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Order History',
            'view_type': 'kanban',
            'view_mode': 'kanban',
            'res_model': 'sale.order',
            'view_id': self.env.ref('lume_sales.view_sale_order_history_kanban').id,
            'target': 'current',
            'res_id': self.id,
            'context': {'search_default_partner_id': self.partner_id.id, 'default_partner_id': self.partner_id.id},
            'domain': ORDER_HISTORY_DOMAIN,
        }

    # def open_returns(self):
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Returns',
    #         'views': [[False, "tree"], [False, "form"]],
    #         'res_model': 'lume.return',
    #         # 'view_id': self.env.ref('lume_sales.view_sale_order_history_kanban').id,
    #         'target': 'current',
    #         # 'res_id': self.id,
    #         # 'context': {'search_default_partner_id': self.partner_id.id, 'default_partner_id': self.partner_id.id},
    #         'domain': [('sale_id','=',self.id)],
    #     }


    @api.depends('picking_ids.move_ids_without_package.state')
    def _compute_delivered(self):
        for record in self:
            res = len(record.picking_ids) > 0
            for delivery in record.env['stock.picking'].search([('sale_id','=',record.id)]):
                for line in delivery.move_ids_without_package:
                    if line.state != 'done':
                        res = False
                        break
            record.is_delivered = res
            if record.is_delivered:
                record.on_fulfillment()

    @api.depends('order_line')
    def _compute_ordered_qty(self):
        for record in self:
            qty = 0
            for line in record.order_line:
                qty += line.product_uom_qty
            record.ordered_qty = qty

    @api.depends('order_line')
    def _compute_order_type(self):
        for record in self:
            record.order_type = 'none'
            if record.caregiver_id:
                record.order_type = 'caregiver'
            elif self.order_line:
                for line in self.order_line:
                    type_order = line.product_id.thc_type
                    if type_order in ['medical','adult']:
                        record.order_type = type_order
                        break

    def _compute_return_count(self):
        for record in self:
            record.return_count = self.env['lume.return'].search_count([('sale_id','=',record.id)])
    
    @api.onchange('fulfillment_type')
    def change_fulfillment(self):
        if self.task:
            self.task.fulfillment_type = self.fulfillment_type

    # Onchange doesn't seem to trigger for calculated fields
    # @api.onchange('is_delivered')
    def on_fulfillment(self):
        if self.task.stage_id.name != 'Order Ready':
            self.task.change_stage(3)

    # @api.onchange('partner_id')
    # def check_order_lines(self):
    #     for order in self.order_line:
    #         if order.product_id.is_medical is not self.partner_id.is_medical:
    #             warning = {
    #             'warning': {'title': "Warning", 'message': "You can't set a " + ("medical" if self.partner_id.is_medical else "recreational") + " customer here because there is at least one " + ("medical" if order.product_id.is_medical else "recreational") + " product in the order!",}
    #             }
    #             self.partner_id = False
    #             return warning

    @api.model
    def get_cart_totals(self, id):
        record = self.browse(id)
        # FIXME Right now caregiver type (curently unused) will always be hidden
        hide_type = '' if record.order_type == 'none' else 'medical' if record.order_type == 'adult' else 'adult'
        return (record.amount_total, record.ordered_qty, hide_type)

    def action_confirm(self):
        if not self.order_line:
            raise ValidationError("You must have at least one sale order line in order to confirm this Sale Order!")
        for line in self.order_line:
            if self.order_type != line.product_id.thc_type and line.product_id.thc_type not in [False, 'merch']:
                raise ValidationError("You can't confirm a cart with both Medical and Recreational products!")
            if line.lot_id.product_qty <= 0:
                raise ValidationError("Cannot Confirm order. There is no more available inventory for %s - %s" % (line.product_id.name, line.lot_id.name))
        ret = super(SaleOrder, self).action_confirm()
        if ret and self.task:
            self.task.change_stage(2)
        # return ret
        return {
            "type":"ir.actions.act_window",
            "res_model":"project.task",
            "views":[[False, "kanban"]],
            "name": 'Tasks',
            "target": 'main',
            "res_id": self.task.project_id.id,
            "domain": [('project_id', '=', self.task.project_id.id)],
            "context": {'default_project_id': self.task.project_id.id},
        }
        # POS will now pick up the SO because it is in 'sale' state
 
    ######################
    # Promotion methods
    ######################
    
    # Override
    def _is_global_discount_already_applied(self):
        # Saying that a global discount is never applied allows us to stack as many as we want.
        # Stacking rules are applied elsewhere
        return False

    # Override
    def _create_new_no_code_promo_reward_lines(self):
        '''Apply new programs that are applicable'''
        self.ensure_one()
        order = self
        programs = order._get_applicable_no_code_promo_program()
        programs = programs._keep_only_most_interesting_auto_applied_global_discount_program()
        for program in programs:
            # VFE REF in master _get_applicable_no_code_programs already filters programs
            # why do we need to reapply this bunch of checks in _check_promo_code ????
            # We should only apply a little part of the checks in _check_promo_code...
            error_status = program._check_promo_code(order, False)
            if not error_status.get('error'):
                if program.promo_applicability == 'on_next_order':
                    order._create_reward_coupon(program)
                # elif program.discount_line_product_id.id not in self.order_line.mapped('product_id').ids:
                    # self.write({'order_line': [(0, False, value) for value in self._get_reward_line_values(program)]})
                else:
                    # Removes all current discounts
                    logger.info("STARTING MY FLOW")
                    # reapply discounts
                    self.apply_program(program)
                order.no_code_promo_program_ids |= program
    
    def apply_program(self, program):
        logger.info("CALLING APPLY_PROGRAM ON %s" % program)
        if program.reward_type == 'product':
            # Add line item and set it's price to 0.01
            self.write({"order_line":[(0,False,{
                'product_id': program.reward_product_id.id,
                'order_id': self.id,
                'product_uom_qty': program.reward_product_quantity,
                'product_uom': program.reward_product_id.uom_id.id,
                'is_reward': True,
                'price_unit': 0.01 if program.reward_product_id.thc_type != 'merch' else 0,
                # 'lot_id': lot.id, # Let Odoo pick whatever lot follows FIFO on this one
            })]})
            pass
        # Only dealing with discounts at this point
        else:
            # Find or create discount
            discount = self.env['lume.discount'].search([('discount_type','=',program.discount_type),('amount','in',[program.discount_percentage,program.discount_fixed_amount])],limit=1)
            if not discount:
                discount = self.sudo().env['lume.discount'].create({
                    'amount': program.discount_percentage if program.discount_type == 'percentage' else program.discount_fixed_amount,
                    'discount_type': program.discount_type,
                })
            if program.discount_apply_on == 'on_order' or program.discount_type == 'fixed_amount': # Fixed amount only applies on the whole order
                # Apply on all lines
                for line in self.order_line:
                    line.discount_ids = [(4,discount.id,0)]
            elif program.discount_apply_on == 'cheapest_product':
                # Apply on one line (cheapest)
                line = self.order_line.sorted(key=lambda l: l.price_subtotal)[0]
                line.discount_ids = [(4,discount.id,0)]
            elif program.discount_apply_on == 'specific_products':
                # Apply on all lines with specified product
                # (Could be multiple due to different lots of same product)
                for line in self.order_line:
                    if line.product_id in program.discount_specific_product_ids:
                        line.discount_ids = [(4,discount.id,0)]
    
    # Override
    def _get_reward_line_values(self, program):
        self.ensure_one()
        return []
    
    # Override
    def _update_existing_reward_lines(self):
        return

    # Override
    def recompute_coupon_lines(self):
        for order in self:
            # order._remove_invalid_reward_lines()
            for line in order.order_line.sudo():
                if line.is_reward:
                    line.unlink()
            order.order_line.write({'discount_ids':[(5,0,0)]})
            order.write({'no_code_promo_program_ids':[(5,0,0)]})
            order._create_new_no_code_promo_reward_lines()
            # order._update_existing_reward_lines()

    # Override
    @api.depends('order_line.price_subtotal', 'partner_id', 'currency_id')
    def _compute_taxes_by_group(self):
        for order in self:
            res={}
            done_taxes = set()
            lang_env = order.with_context(lang=order.partner_id.lang).env
            # Populate res
            for line in order.order_line:
                for tax in line.tax_id:
                    res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})

                    data = tax.compute_all(line.price_subtotal,line.currency_id,1)
                    price_tax = sum(t.get('amount',0.0) for t in data.get('taxes', []))

                    res[tax.tax_group_id]['amount'] += price_tax
                    
                    # taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                    # line.update({
                    #     'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    #     'price_total': taxes['total_included'],
                    #     'price_subtotal': taxes['total_excluded'],
                    # })

                    tax_key_add_base = tuple([tax.id])
                    if tax_key_add_base not in done_taxes:
                        amount = line.price_subtotal
                        res[tax.tax_group_id]['base'] += amount
                        # The base should be added ONCE
                        done_taxes.add(tax_key_add_base)

            # At this point we only want to keep the taxes with a zero amount since they do not
            # generate a tax line.
            # for line in order.order_line:
            #     for tax in line.tax_id.flatten_taxes_hierarchy():
            #         if tax.tax_group_id not in res:
            #             res.setdefault(tax.tax_group_id, {'base': 0.0, 'amount': 0.0})
            #             res[tax.tax_group_id]['base'] += line.price_subtotal
            res = sorted(res.items(), key=lambda l: l[0].sequence)
            order.amount_by_group = [(
                group.name, amounts['amount'],
                amounts['base'],
                formatLang(lang_env, amounts['amount'], currency_obj=order.currency_id),
                formatLang(lang_env, amounts['base'], currency_obj=order.currency_id),
                len(res),
                group.id
            ) for group, amounts in res]
            logger.info("Tax Group info: %s" % order.amount_by_group)

    def create_return(self):
        return_id = self.env['lume.return'].create({
            'sale_id': self.id,
            'currency_id': self.currency_id.id,
        })
        return_lines = []
        for line in self.order_line:
            data = {
                'return_id':return_id.id,
                'price': line.price_subtotal / line.product_uom_qty,
                'product_id': line.product_id.id,
                'lot_id': line.lot_id.id,
                'original_qty': line.product_uom_qty
            }
            return_lines.append((0,0,data))
        return_id.return_lines = return_lines
        # Open return in new action
        return {
                'type': 'ir.actions.act_window',
                'name': 'Return',
                'views': [[False,'form']],
                'res_model': 'lume.return',
                # 'view_id': self.env.ref('lume_sales.TBD').id,
                'target': 'current',
                'res_id': return_id.id,
                # 'context': {},
            }

class SaleLine(models.Model):
    _inherit = 'sale.order.line'

    order_type = fields.Selection(related="order_id.order_type")
    lot_id = fields.Many2one('stock.production.lot')
    discount_ids = fields.Many2many('lume.discount', column1='discount_id',column2='line_id')
    is_reward = fields.Boolean(default=False)
    product_categ_id = fields.Many2one('product.category',related='product_id.categ_id')
    thc_type = fields.Selection(related="product_id.thc_type",store=True)

    @api.onchange('product_uom_qty')
    def ensure_valid_quantity(self):
        if self.product_uom_qty <= 0:
            self.product_uom_qty = self._origin.product_uom_qty
            return {
                'warning': {'title': "Warning", 'message': "You can't set a quantity to a negative number!",}
                }

    @api.model
    def create(self, vals):
        if self.env.uid != 1 and self.order_id:
            order = self.env['sale.order'].browse(vals['order_id'])
            product = self.env['product.product'].browse(vals['product_id'])
            message = "Added %s" % (product.name)
            order.message_post(body=message)
        return super(SaleLine, self).create(vals)

    @api.model
    def unlink(self):
        if self.env.uid != 1 and self.order_id:
            message = "Removed %s" % (self.product_id.name)
            self.order_id.message_post(body=message)
        return super(SaleLine, self).unlink()

    # Override, no super
    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id','discount_ids')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            price_weight = 0
            # We have to loop here because not all lines in self will be on the same order
            for order_line in line.order_id.order_line:
                price_weight += order_line.product_uom_qty * order_line.price_unit
            discounts = line.discount_ids.filtered(lambda l: l.discount_type == 'percentage')
            discount_total = math.prod([d.amount / 100 for d in discounts])
            # math.prod will return 1 if list is empty (no discounts apply to this line)
            if discount_total == 1:
                discount_total = 0
            discount_flat = line.discount_ids.filtered(lambda l: l.discount_type == 'fixed_amount')
            discount_flat_total = sum([d.amount for d in discount_flat])
            discout_flat_share = discount_flat_total * ((line.product_uom_qty * line.price_unit) / price_weight) if price_weight > 0 else 0
            price = (line.price_unit - (discount_flat_total * discout_flat_share)) * (1 - discount_total)
            if price < line.product_uom_qty * 0.01 and line.product_id.thc_type != 'merch':
                # Ensure thc products don't go below 1 cent per item
                price = line.product_uom_qty * 0.01
            data = {"price_unit":line.price_unit,"flat_discount":discount_flat_total,"item_count":len(self),"percent_total":discount_total}
            logger.info("Price Computation: %s" % data)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
            if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

    # @api.onchange('product_id')
    # def check_order_line(self):
    #     if self.product_id and self.order_id.partner_id:
    #         if self.product_id.is_medical is not self.order_id.partner_id.is_medical:
    #             warning = {
    #                 'warning': {'title': "Warning", 'message': "You can't add a " + ("medical" if self.product_id.is_medical else "recreational") + " product to a " + ("medical" if self.order_id.partner_id.is_medical else "recreational") + " customer's order!",}
    #                 }
    #             self.product_id = False
    #             self.name = False
    #             self.price_unit = False
    #             return warning

