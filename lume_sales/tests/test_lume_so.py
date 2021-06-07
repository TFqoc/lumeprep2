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
            'stage_id': cls.env.ref('lume_sales.lume_stage_1')
        })

        cls.task_med = Task.create({
            'name': cls.customer_med.name,
            'project_id': cls.lumestore_one.id,
            'partner_id': cls.customer_med.id,
            'stage_id': cls.env.ref('lume_sales.lume_stage_1')
        })

        cls.task_care = Task.create({
            'name': cls.customer_care.name,
            'project_id': cls.lumestore_one.id,
            'partner_id': cls.customer_care.id,
            'stage_id': cls.env.ref('lume_sales.lume_stage_1')
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
        self.assertTrue(
            False,
            "This test should always fail."
        )

@tagged('lume')
class TestLPC(TestLumeOrderCommon):
    def test_lpc_add_quantity(self):
        self.assertTrue(
            False,
            "This test should always fail."
        )
