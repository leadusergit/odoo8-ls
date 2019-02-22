<p>
	<strong><span style="font-family:arial,helvetica,sans-serif;font-size: 22px;">${name}</span><br/>
	<span style="font-family:arial,helvetica,sans-serif;font-size: 14px;">${o.employee_id.company_id.name}</span></strong></p>
<p>
	<span style="font-family: arial, helvetica, sans-serif;font-size:11px;">${o.employee_id.name}<br/>
	</span></p>
<table cellpadding="1" cellspacing="1" style="width: 600px;">
	<tr>
		<td style="text-align: center;">
			<strong><span style="font-family:arial,helvetica,sans-serif;font-size: 14px;">Ingresos</span></strong></td>
		<td style="text-align: center;">
			<strong><span style="font-family:arial,helvetica,sans-serif;font-size: 14px;">Egresos</span></strong></td>
	</tr>
	<tr>
		<td>
			<table border="1" cellpadding="1" cellspacing="1" style="width: 300px;">
			% for row in o.incomes_ids:
				<tr>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;"><span style="font-size: 11px;">${row.name}</span></span></td>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;"><span style="font-size: 11px;">$${round(row.value, 2)}</span></span></td>
				</tr>
			% endfor
				<tr>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;font-size: 11px;"><strong>TOTAL</strong></span></td>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;font-size: 11px;"><strong>$${round(o.total_ingresos, 2)}</strong></span></td>
				</tr>
			</table>
		</td>
		<td>
			<table border="1" cellpadding="1" cellspacing="1" style="width: 300px;">
			% for row in o.expenses_ids:
				<tr>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;font-size: 11px;">${row.name}</span></td>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;font-size: 11px;">$${round(row.value, 2)}</span></td>
				</tr>
			% endfor
				<tr>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;font-size: 11px;"><strong>TOTAL</strong></span></td>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;font-size: 11px;"><strong>$${round(o.total_egresos, 2)}</strong></span></td>
				</tr>
			</table>
		</td>	
	</tr>
</table>
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">Valor Neto Pagado: $${round(o.total,2)}</span></strong></p>
<br/><br/><br/><br/><br/>
<hr align="LEFT" size="1" width="30%">
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">RECIBI CONFORME</span></strong></p>
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">${o.employee_id.name}</span></strong></p>
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">${o.employee_id.bank_account_id and ('BCO. ' + o.employee_id.bank_account_id.bank_name + o.employee_id.bank_account_id.name)}</span></strong></p>
