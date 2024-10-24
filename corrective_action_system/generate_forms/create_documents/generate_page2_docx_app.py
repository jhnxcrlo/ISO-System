from flask import Flask, render_template, request, send_file, flash, redirect
from docxtpl import DocxTemplate
from io import BytesIO

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Required for flashing messages


@app.route('/')
def form():
    # Renders the HTML form
    return render_template('FM-QMS-010-page-2.html')


@app.route('/submit', methods=['POST'])
def submit():
    # Capture the form data
    reviewed_by = request.form['reviewed_by']
    reviewed_date = request.form['reviewed_date']
    accepted_not_accepted = request.form['accepted_not_accepted']  # Radio buttons: Accepted or Not Accepted
    state_reason = request.form.get('state_reason', '')  # Reason textarea (optional)
    action_taken_effective = request.form.get('action_taken_effective', '')  # "Yes" or "No"
    new_rfa_no = request.form.get('new_rfa_no', '')  # New RFA # field

    # Optional fields (use .get())
    status = request.form.get('status', '')
    initials_resp = request.form.get('initials_resp', '')
    status_date = request.form.get('status_date', '')
    nvisits = request.form.get('nvisits', '')
    vdate = request.form.get('vdate', '')
    follow_up_audit_result = request.form.get('follow_up_audit_result', '')
    ntdate = request.form.get('ntdate', '')
    auditor_name = request.form['auditor_name']
    a_date = request.form['a_date']
    processowner_name = request.form['processowner_name']
    po_date = request.form['po_date']
    p2_effectivity = request.form.get('p2_effectivity', '')
    p2_rev_no = request.form.get('p2_rev_no', '')

    # Validation: If "Not Accepted" is selected, ensure the reason is provided
    if accepted_not_accepted == "Not Accepted" and not state_reason.strip():
        flash("Please provide a reason for 'Not Accepted' decisions.")
        return redirect('/')  # Redirect back to form

    # Validation: If action taken is "No", ensure "New RFA #" is provided
    if action_taken_effective == "No" and not new_rfa_no.strip():
        flash("Please provide the 'New RFA #' when the action is not effective.")
        return redirect('/')  # Redirect back to form

    # Load the DOCX template
    doc = DocxTemplate("docs/FM-QMS-010-RFA-Form-2.docx")

    # Define the context with the form data
    context = {
        'accepted_not_accepted': accepted_not_accepted,  # "Accepted" or "Not Accepted"
        'state_reason': state_reason,   # Reason field if not accepted
        'reviewed_by': reviewed_by,
        'reviewed_date': reviewed_date,
        'status': status,
        'initials_resp': initials_resp,
        'status_date': status_date,
        'nvisits': nvisits,
        'vdate': vdate,
        'follow_up_audit_result': follow_up_audit_result,
        'ntdate': ntdate,
        'action_taken_effective': action_taken_effective,  # "Yes" or "No"
        'new_rfa_no': new_rfa_no,  # Capture "New RFA #"
        'auditor_name': auditor_name,
        'a_date': a_date,
        'processowner_name': processowner_name,
        'po_date': po_date,
        'p2_effectivity': p2_effectivity,
        'p2_rev_no': p2_rev_no,
    }

    # Render the context into the template
    doc.render(context)

    # Save the rendered document to a BytesIO object
    output = BytesIO()
    doc.save(output)
    output.seek(0)

    # Send the file as a response, offering it as a download
    return send_file(output, as_attachment=True, download_name="generated_doc.docx")


if __name__ == "__main__":
    app.run(debug=True)
