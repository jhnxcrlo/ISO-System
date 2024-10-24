from flask import Flask, render_template, request, send_file, redirect, flash
from docxtpl import DocxTemplate
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed to use flash for form validation messages


@app.route('/')
def form():
    # Renders the HTML form
    return render_template('FM-QMS-010-page-1.html')


@app.route('/submit', methods=['POST'])
def submit():
    try:
        # Capture the form data
        rfa_ref_no = request.form['rfa_ref_no']
        rfa_date_issued = request.form['rfa_date_issued']
        originators_name_id_no = request.form['originators_name_id_no']
        unit_department = request.form['unit_department']
        phone = request.form['phone']
        email = request.form['email']
        rfa_intended_to = request.form['rfa_intended_to']
        department_nc_exists = request.form['department_nc_exists']
        description_of_nonconformance = request.form['description_of_nonconformance']
        description_of_nonconformance_category = request.form['description_of_nonconformance_category']
        iso_clause_ref = request.form['iso_clause_ref']
        category = request.form['category']
        immediate_action_correction = request.form['immediate_action_correction']
        acknowledged_by = request.form['acknowledged_by']
        acknowledged_date = request.form['acknowledged_date']
        cause_of_nonconformance = request.form['cause_of_nonconformance']
        con_date = request.form['con_date']
        responsible_officer = request.form['responsible_officer']
        estimated_close_out_date = request.form['estimated_close_out_date']
        step_1_by_step_act = request.form['step_1_by_step_act']
        step_1_responsible_person_unit = request.form['step_1_responsible_person_unit']
        step_1_time_frame = request.form['step_1_time_frame']
        step_1_resources_needed = request.form['step_1_resources_needed']
        step_1_result = request.form['step_1_result']

        step_2_by_step_act = request.form['step_2_by_step_act']
        step_2_responsible_person_unit = request.form['step_2_responsible_person_unit']
        step_2_time_frame = request.form['step_2_time_frame']
        step_2_resources_needed = request.form['step_2_resources_needed']
        step_2_result = request.form['step_2_result']

        step_3_by_step_act = request.form['step_3_by_step_act']
        step_3_responsible_person_unit = request.form['step_3_responsible_person_unit']
        step_3_time_frame = request.form['step_3_time_frame']
        step_3_resources_needed = request.form['step_3_resources_needed']
        step_3_result = request.form['step_3_result']

        p1_effectivity = request.form['p1_effectivity']
        p1_rev_no = request.form['p1_rev_no']

        # Load the DOCX template
        doc = DocxTemplate("FM-QMS-010-page-1.docx")

        # Define the context with the form data
        context = {
            'rfa_ref_no': rfa_ref_no,
            'rfa_date_issued': rfa_date_issued,
            'originators_name_id_no': originators_name_id_no,
            'unit_department': unit_department,
            'phone': phone,
            'email': email,
            'rfa_intended_to': rfa_intended_to,
            'department_nc_exists': department_nc_exists,
            'description_of_nonconformance_category': description_of_nonconformance_category,
            'cause_of_nonconformance': cause_of_nonconformance,
            'con_date': con_date,
            'description_of_nonconformance': description_of_nonconformance,
            'iso_clause_ref': iso_clause_ref,
            'category': category,
            'immediate_action_correction': immediate_action_correction,
            'acknowledged_by': acknowledged_by,
            'acknowledged_date': acknowledged_date,
            'responsible_officer': responsible_officer,
            'estimated_close_out_date': estimated_close_out_date,
            'p1_effectivity': p1_effectivity,
            'p1_rev_no': p1_rev_no,
            'step_1_by_step_act': step_1_by_step_act,
            'step_1_rpu': step_1_responsible_person_unit,
            'step_1_tf': step_1_time_frame,
            'step_1_rn': step_1_resources_needed,
            'step_1_result': step_1_result,
            'step_2_by_step_act': step_2_by_step_act,
            'step_2_rpu': step_2_responsible_person_unit,
            'step_2_tf': step_2_time_frame,
            'step_2_rn': step_2_resources_needed,
            'step_2_result': step_2_result,
            'step_3_by_step_act': step_3_by_step_act,
            'step_3_rpu': step_3_responsible_person_unit,
            'step_3_tf': step_3_time_frame,
            'step_3_rn': step_3_resources_needed,
            'step_3_result': step_3_result,
        }

        # Render the context into the template
        doc.render(context)

        # Save the rendered document to a BytesIO object
        output = BytesIO()
        doc.save(output)
        output.seek(0)

        # Send the file as a response, offering it as a download
        return send_file(output, as_attachment=True, download_name="generated_doc.docx")

    except KeyError as e:
        # If any key is missing from the form data, flash a message and redirect back
        flash(f'Missing form field: {str(e)}')
        return redirect('/')


if __name__ == "__main__":
    app.run(debug=True)
