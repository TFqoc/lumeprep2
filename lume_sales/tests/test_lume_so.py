import logging
from . test_lumesales_base import TestLumeSaleCommon
from odoo.tests.common import tagged

_logger = logging.getLogger(__name__)

@tagged('lume')
class TestLumeOrderCommon(TestLumeSaleCommon): 

    @classmethod
    def setUpClass(cls):
        super(TestLumeOrderCommon, cls).setUpClass()
        Task = cls.env['project.task'].with_context({'tracking_disable': True})
        SO = cls.env['sale.order']

        cls.task_rec = Task.create({
            'name': cls.customer_rec.name,
            'project_id': cls.lumestore_one.id,
            'partner_id': cls.customer_rec.id,
            'stage_id': cls.env.ref('lume_sales.lume_stage_1').id #This needs to have .id to return an int rather than an object reference.
        })

        cls.task_med = Task.create({
            'name': cls.customer_med.name,
            'project_id': cls.lumestore_one.id,
            'partner_id': cls.customer_med.id,
            'stage_id': cls.env.ref('lume_sales.lume_stage_1').id
        })

        cls.task_care = Task.create({
            'name': cls.customer_care.name,
            'project_id': cls.lumestore_one.id,
            'partner_id': cls.customer_care.id,
            'stage_id': cls.env.ref('lume_sales.lume_stage_1').id
        })

        cls.order_rec = SO.create({
            'partner_id': cls.customer_rec.id,
            'order_type': 'adult',
            'warehouse_id':cls.lumestore_one.warehouse_id.id,
            'task': cls.task_rec.id
        })

        cls.order_med = SO.create({
            'partner_id': cls.customer_med.id,
            'order_type': 'medical',
            'warehouse_id': cls.lumestore_one.warehouse_id.id,
            'task': cls.task_med.id
        })

        cls.order_care = SO.create({
            'partner_id': cls.customer_care.id,
            'order_type': 'medical', #We don't know what this is going to be yet.
            'task': cls.task_care.id
        })

        cls.task_rec.sales_order = cls.order_rec.id
        cls.task_med.sales_order = cls.order_med.id
        cls.task_care.sales_order = cls.order_care.id

@tagged('lume')
class TestLumeSalesOrder(TestLumeOrderCommon):
    def test_rec_add_sales_order_line(self):
        record_ids = [self.order_rec.id]
        uid = self.env.ref('base.user_admin').id
        self.env['sale.order'].browse(record_ids).with_context({
            'allowed_company_ids': [1],
            'form_view_initial_mode': 'edit',
            'lang': 'en_US',
            'tz': 'Europe/Brussels',
            'uid': uid
        }).with_user(uid).write({
            'order_line': 
            [[0, 'virtual_1018', {
                'sequence': 10, 
                'display_type': False, 
                'product_id': self.product_rec.product_variant_ids[0].id, 
                'product_template_id': self.product_rec.id, 
                'name': 'Jenny Kush 3.5G', 
                'analytic_tag_ids': [[6, False, []]], 
                'route_id': False, 
                'product_uom_qty': 1, 
                'qty_delivered_manual': 0, 
                'product_uom': 1, 
                'customer_lead': 0, 
                'product_packaging': False, 
                'price_unit': 45.0, 
                'tax_id': [[6, False, []]], 
                'discount': 0
                }]]})

    def test_rec_so_confirm(self):
        uid = self.env.ref('base.user_admin').id
        Task = self.env['project.task'].with_context({'tracking_disable': True})
        self.order_rec.order_line = [(0, 0, {
            'product_id': self.product_rec.product_variant_ids[0].id,
            'product_uom_qty': 1.00
        })]
        record_ids = [self.order_rec.id]
        self.env['sale.order'].browse(record_ids).with_context({
            'allowed_company_ids': [1],
            'form_view_initial_mode': 'edit',
            'lang': 'en_US',
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).action_confirm()

        self.assertEqual(
            self.task_rec.stage_id.sequence,
            20,
            "Error in Confirm Cart: Tile did not move to the proper tile."
        )

        self.assertEqual(
            self.order_rec.state,
            'sale',
            "Error in Confirm Cart: Sales Order was not set to the state of sale."
        )

        self.assertTrue(
            self.order_rec.picking_ids,
            "Pick Ticket was not created."
        )

    def test_rec_abandon_cart(self):
        pass


@tagged('lume')
class TestLPC(TestLumeOrderCommon):
    def test_lpc_add_quantity_rec(self):
        record_ids = [self.product_rec.product_variant_ids[0].id]
        active_id = self.lumestore_one.id
        active_ids = [self.lumestore_one.id]
        uid = self.env.ref('base.user_admin').id
        self.env['product.product'].browse(record_ids).with_context({
            'active_id': active_id,
            'active_ids': active_ids,
            'active_model': 'sale.order',
            'allowed_company_ids': [1],
            'type': self.order_rec.order_type,   #Added due to error in code
            'form_view_initial_mode': 'edit',
            'lang': 'en_US',
            'lpc_sale_order_id': self.order_rec.id,
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).lpc_add_quantity()

        product_ids = [line["product_id"] for line in self.order_rec.order_line]

        self.assertTrue(
            self.order_rec.order_line,
            "Error in Product Catologue: Line was not created."
        )

        self.assertEqual(
            product_ids[0].id,
            self.product_rec.product_variant_ids[0].id,
            "Error in Product Category: Incorrect Product Added."
        )

        self.assertEqual(
            self.order_rec.order_line.product_uom_qty,
            1.00,
            "Error in Product Category: Incorrect Quantity Added."
        )
    
    def test_lpc_remove_quantity_rec(self):
        self.order_rec.order_line = [(0, 0, {
            'product_id': self.product_rec.product_variant_ids[0].id,
            'product_uom_qty': 2.00
        })]
        record_ids = [self.product_rec.product_variant_ids[0].id]
        # TODO: Check or Find active_id link (external id or otherwise)
        active_id = self.lumestore_one.id
        # TODO: Check or Find active_ids link (external id or otherwise)
        active_ids = [self.lumestore_one.id]
        uid = self.env.ref('base.user_admin').id
        self.env['product.product'].browse(record_ids).with_context({
            'active_id': active_id,
            'active_ids': active_ids,
            'active_model': 'sale.order',
            'allowed_company_ids': [1],
            'form_view_initial_mode': 'edit',
            'lang': 'en_US',
            'lpc_sale_order_id': self.order_rec.id,
            'type': 'adult',
            'tz': 'Europe/Brussels',
            'uid': uid}).with_user(uid).lpc_remove_quantity()
        
        self.assertTrue(
            self.order_rec.order_line,
            "Sales Order line should not have been deleted."
        )

        self.assertEqual(
            self.order_rec.order_line.product_uom_qty,
            1.00,
            "Error in Product Category: Incorrect Quantity Subtracted."
        )


    def test_lpc_remove_line_rec(self):
        pass

