from django import forms

class UploadPDFForm(forms.Form):
    pdf_file = forms.FileField(label="Upload PDF")
