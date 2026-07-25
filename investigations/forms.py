from django import forms


class StartForm(forms.Form):
    start = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )
    end = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"})
    )


class ReviewForm(forms.Form):
    revision = forms.IntegerField(widget=forms.HiddenInput)
    text = forms.CharField(
        max_length=4000,
        widget=forms.Textarea(attrs={"rows": 4}),
        label="Engineer assessment",
    )
