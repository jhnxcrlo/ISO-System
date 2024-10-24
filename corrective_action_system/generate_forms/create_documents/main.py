import pandas as pd
from datetime import datetime
from docxtpl import DocxTemplate

doc = DocxTemplate("docs/en-template-my-info.docx")
my_name = "Frank Andrade"
my_phone = "(123) 456-789"
my_email = "frank@gmail.com"
my_address = "123 Main Street, NY"
today_date = datetime.today().strftime("%d %b, %Y")

context = {'my_name': my_name, 'my_phone': my_phone, 'my_email': my_email, 'my_address': my_address,
              'today_date': today_date}

doc.render(context)
doc.save(f"generated_doc.docx")