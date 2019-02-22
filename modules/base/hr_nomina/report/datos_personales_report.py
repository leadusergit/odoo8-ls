from openerp.report import report_sxw
import time

class datos_personales_report(report_sxw.rml_parse):

    def primero(self,relacion):
        lista=[]
        nombre=''
        parentezco=''
        if relacion:
            for i in relacion:
                nombre = i.name
                parentezco= i.parentezco
                if i.parentezco == 'son':
                    parentezco='HIJO'
                if i.parentezco == 'hb_wife':
                    parentezco='CONYUGUE'
                if i.parentezco== 'ulibre':
                    parentezco='UNION LIBRE'
                if i.parentezco == 'otro':
                    parentezco='OTRO'
                    
                break
        lista=[nombre,parentezco]
        return lista
    
    def __init__(self, cr, uid, name, context):
        super(datos_personales_report, self).__init__(cr, uid, name, context)
        self.localcontext.update({
                'time': time,
                'primero':self.primero,
                })
        self.context = context

report_sxw.report_sxw('report.nomina.datos', 'hr.employee', 'hr_employee/report/datos_personales_report.rml',parser = datos_personales_report , header = False)

