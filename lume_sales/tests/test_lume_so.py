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

        cls.order_rec = SO.create({
            'partner_id': cls.customer_care.id,
            'order_type': 'medical', #We don't know what this is going to be yet.
            'task': cls.task_care.id
        })

@tagged('lume')
class TestLumeSalesOrder(TestLumeOrderCommon):
    def test_add_sales_order_line(self):
        # self.assertTrue(
        #     False,
        #     "This test should always fail."
        # )
        pass

    def test_so_confirm(self):
        pass


@tagged('lume')
class TestLPC(TestLumeOrderCommon):
    def test_lpc_add_quantity(self):
        record_ids = [self.product_rec.product_variant_ids[0].id]
        active_id = self.lumestore_one.id
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
    
    def test_lpc_subtract_quantity(self):
        pass

    def test_lpc_remove_line(self):
        pass

