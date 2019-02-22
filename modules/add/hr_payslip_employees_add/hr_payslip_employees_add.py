# -*- coding: utf-8 -*-

from openerp.osv import osv
from openerp.tools.translate import _

class hr_payslip_employees(osv.osv_memory):

    _inherit ='hr.payslip.employees'
    
  
    def compute_sheet(self, cr, uid, ids, context=None):
        emp_pool = self.pool.get('hr.employee')
        slip_pool = self.pool.get('hr.payslip')
        slip_line_pool = self.pool.get('hr.payslip.line')
        run_pool = self.pool.get('hr.payslip.run')
        slip_ids = []
        if context is None:
            context = {}
        data = self.read(cr, uid, ids, context=context)[0]
        run_data = {}
        if context and context.get('active_id', False):
            """lectura de campos de la cabecera del payslip(Rol Empleado)"""
            run_data = run_pool.read(cr, uid, [context['active_id']], ['date_start', 'date_end', 'credit_note','journal_id'])[0]
        """se obtiene la fecha inicial"""
        from_date =  run_data.get('date_start', False)
        """se obtiene la fecha final"""
        to_date = run_data.get('date_end', False)
        credit_note = run_data.get('credit_note', False)
        """se obtiene el id del diario"""
        journal_id = run_data.get('journal_id')
        journal_id = journal_id and journal_id[0] or False
        if journal_id:
            context = dict(context, journal_id=journal_id) 
            
        if not data['employee_ids']:
            raise osv.except_osv(_("Warning!"), _("You must select employee(s) to generate payslip(s)."))
        for emp in emp_pool.browse(cr, uid, data['employee_ids'], context=context):
            slip_data = slip_pool.onchange_employee_id(cr, uid, [], from_date, to_date, emp.id, contract_id=False, context=context)
            res = {
                'employee_id': emp.id,
                'name': slip_data['value'].get('name', False),
                'struct_id': slip_data['value'].get('struct_id', False),
                'contract_id': slip_data['value'].get('contract_id', False),
                'payslip_run_id': context.get('active_id', False),
                'input_line_ids': [(0, 0, x) for x in slip_data['value'].get('input_line_ids', False)],
                'worked_days_line_ids': [(0, 0, x) for x in slip_data['value'].get('worked_days_line_ids', False)],
                'date_from': from_date,
                'date_to': to_date,
                'credit_note': credit_note,
            }
            slip_ids.append(slip_pool.create(cr, uid, res, context=context))
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        """Se llama al método load_info para cargar las entradas(inputs) de cada payslip"""
        slip_pool.load_info(cr, uid, slip_ids, context={})
        """Se llama al método compute_sheet del objeto hr_payslip para ejecutar el cálculo del rol con los datos añadidos"""
        slip_pool.compute_sheet(cr, uid, slip_ids, context=context)
        
        for payslip in slip_ids:
            print"payslip=%s"% payslip
            cr.execute("UPDATE hr_payslip_line SET create_date =%s WHERE slip_id=%s", (to_date,payslip))
        
        return {'type': 'ir.actions.act_window_close'}

    
class hr_payslip_run(osv.osv):

    _inherit = 'hr.payslip.run'
    
    
    def _get_payslip_ids(self, cr, uid, id):
        return self.pool.get('hr.payslip').search(cr, uid, [], order='payslip_run_id')    
    
    def close_payslip_run(self, cr, uid, ids, context=None): 
        """Recorre los registros de la relacion entre objetos hr_payslip_run - hr_payslip"""
        for obj_run in self.browse(cr, uid, ids):
            for payslip in self.pool.get('hr.payslip').browse(cr, uid, self._get_payslip_ids(cr, uid, obj_run.slip_ids)):
               """Se verifica que los payslips entan en estado borrador y se modifica el estado a Realizado(done)"""
               if payslip.state=='draft':
                   #print"payslip.state=%s"%payslip.state
                   #payslip.state='done'
                   #payslip.hr_verify_sheet()
                   payslip.process_sheet()
            
        return self.write(cr, uid, ids, {'state': 'close'}, context=context)


