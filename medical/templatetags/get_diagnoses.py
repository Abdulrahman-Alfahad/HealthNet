from django import template
from medical.models import Diagnosis
from hospital.models import TreatmentSession

register = template.Library()


@register.assignment_tag
def get_diagnoses(item):
    if isinstance(item, Diagnosis):
        return [item]
    elif isinstance(item, TreatmentSession):
        return item.diagnosis_set.all()
    else:
        return []
