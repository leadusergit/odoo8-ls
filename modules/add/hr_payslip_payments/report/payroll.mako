<p>
	<strong>
	<p>
	<span style="font-family:arial,helvetica,sans-serif;font-size: 14px;">${o.employee_id.company_id.name}</span></p>
	<p>
	<span style="font-family:arial,helvetica,sans-serif;font-size: 12px;">${name}</span><br/></p>
	</strong>
</p>
<p><span style="font-family: arial, helvetica, sans-serif;font-size:11px;"> <br/>
	</span></p>
<table cellpadding="1" cellspacing="1" style="width: 600px;">
	<tr>
	<p>
		<td style="text-align: left";">
		<strong><span style="font-family:arial,helvetica,sans-serif;font-size: 12px;">Detalle Ingresos/Egresos</span></strong></td>
		<td style="text-align: right";">
		<strong><span style="font-family:arial,helvetica,sans-serif;font-size: 12px;"></span></strong></td>
	</p>
	</tr>
	<tr>
		<td>
			<table border="1" cellpadding="1" cellspacing="1" style="width: 450px;">
			% for row in o.line_ids:
				<tr>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;"><span style="font-size: 12px;">${row.name}</span></span></td>
					<td>
						<span style="font-family:arial,helvetica,sans-serif;"><span style="font-size: 12px;">$${round(row.total, 2)}</span></span></td>
				</tr>
			% endfor
	    	</table>
		</td>
	</tr>
</table>
<p>
<br/><br/><br/><br/><br/>
<hr align="LEFT" size="1" width="30%">
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">RECIBI CONFORME</span></strong></p>
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">${o.employee_id.name}</span></strong></p>
<p>
	<strong><span style="font-family: arial, helvetica, sans-serif;font-size:11px;">CI: ${o.employee_id.identification_id}</span></strong></p>
