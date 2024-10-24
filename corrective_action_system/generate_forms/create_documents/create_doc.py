import os
from docxtpl import DocxTemplate
from datetime import datetime

# Load the DOCX template
doc = DocxTemplate("docs/FM-QMS-010-RFA-Form-1.docx")

# Define the variables for the context
rfa_ref_no = "Frank Andrade"
rfa_date_issued = "2024-10-10"
originators_name_id_no = "frank@gmail.com"
unit_department = "123 Main Street, NY"
phone = "+1234567890"
email = "rommelbailon00@gmail.com"
rfa_intended_to = "To address the issue"
department_nc_exists = "IT Department"
description_of_nonconformance = "Non-conformance description here"
description_of_nonconformance_category = "Category of non-conformance"
iso_clause_ref = "ISO 9001:2015"
category = "Major"
immediate_action_correction = "Immediate action description"
acknowledged_by = "John Doe"
acknowledged_date = "2023-10-25"
cause_of_nonconformance = "Root cause of non-conformance"
con_date = "2023-10-30"
responsible_officer = "Jane Doe"
estimated_close_out_date = "2023-11-15"
# Step-by-step activities (dynamic variables for each step)
step_1_by_step_act = "Step 1 description"
step_1_responsible_person_unit = "Unit 1"
step_1_time_frame = "1 week"
step_1_resources_needed = "Resources 1"
step_1_result = "Result 1"

step_2_by_step_act = "Step 2 description"
step_2_responsible_person_unit = "Unit 2"
step_2_time_frame = "2 weeks"
step_2_resources_needed = "Resources 2"
step_2_result = "Result 2"

step_3_by_step_act = "Step 3 description"
step_3_responsible_person_unit = "Unit 3"
step_3_time_frame = "3 weeks"
step_3_resources_needed = "Resources 3"
step_3_result = "Result 3"

#form 2
effectivity_date = "October 25, 2023"
reviewed_by = "Manager"
reviewed_date = "2023-11-01"
revision_no = "01"
p1_effectivity = "2023-10-25"
p1_rev_no = "01"
p2_effectivity = "2023-10-25"
p2_rev_no = "02"
accepted_not_accepted = "Accepted"
status = "Ongoing"
initials_resp = "JD"
status_date = "2023-11-05"
nvisits = "2"
vdate = "2023-11-10"
follow_up_audit_result = "Audit successful"
ntdate = "2023-11-20"
action_taken_effective = "Yes"
auditor_name = "Jane Auditor"
a_date = "2023-11-10"
processowner_name = "John ProcessOwner"
po_date = "2023-11-15"



# Define the context for the template
context = {
    'rfa_ref_no': rfa_ref_no,
    'rfa_date_issued': rfa_date_issued,
    'originators_name_id_no': originators_name_id_no,
    'unit_department': unit_department,
    'phone': phone,
    'email': email,
    'rfa_intended_to': rfa_intended_to,
    'department_nc_exists': department_nc_exists,
    'description_of_nonconformance': description_of_nonconformance,
    'description_of_nonconformance_category': description_of_nonconformance_category,
    'iso_clause_ref': iso_clause_ref,
    'category': category,
    'immediate_action_correction': immediate_action_correction,
    'acknowledged_by': acknowledged_by,
    'acknowledged_date': acknowledged_date,
    'cause_of_nonconformance': cause_of_nonconformance,
    'con_date': con_date,
    'responsible_officer': responsible_officer,
    'estimated_close_out_date': estimated_close_out_date,
    'p1_effectivity': p1_effectivity,
    'p1_rev_no': p1_rev_no,
    'p2_effectivity': p2_effectivity,
    'p2_rev_no': p2_rev_no,
    'accepted_not_accepted': accepted_not_accepted,
    'status': status,
    'initials_resp': initials_resp,
    'status_date': status_date,
    'nvisits': nvisits,
    'vdate': vdate,
    'follow_up_audit_result': follow_up_audit_result,
    'ntdate': ntdate,
    'action_taken_effective': action_taken_effective,
    'auditor_name': auditor_name,
    'a_date': a_date,
    'processowner_name': processowner_name,
    'po_date': po_date,

    # Dynamic Step-by-step activities
    'step_1_by_step_act': step_1_by_step_act,
    'step_1_rpu': step_1_responsible_person_unit,
    'step_1_tf': step_1_time_frame,
    'step_1_rn': step_1_resources_needed,
    'step_1_result}': step_1_result,

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

# Save the rendered document
output_path = "docs/generated_doc.docx"
doc.save(output_path)
print(f"Document generated successfully and saved as {output_path}")
