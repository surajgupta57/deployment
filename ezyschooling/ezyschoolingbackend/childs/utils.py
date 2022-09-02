from django.utils.text import slugify

from core.utils import random_string_generator


def child_profile_picture_upload_path(instance, filename):
    return f"child/profile_picture/user_{instance.user.username}/{filename}"


def child_birth_certificate_upload_path(instance, filename):
    return f"child/child-birth-certificate/{instance.name}/{filename}"


def address_proof_upload_path(instance, filename):
    return f"child/address_proof/{instance.name}/{filename}"

# def medical_certificate_upload_path(instance, filename):
#     return f"child/medical_certificate/{instance.name}/{filename}"
#
def medical_fitness_certificate_upload_path(instance, filename):
    return f"child/medical_fitness_certificate/{instance.name}/{filename}"

def first_child_affidavit_upload_path(instance, filename):
    return f"child/first_child_affidavit/{instance.name}/{filename}"

def minority_proof_upload_path(instance,filename):
    return f"child/minority_proof/{instance.name}/{filename}"

def child_vaccination_card_upload_path(instance, filename):
    return f"child/child_vaccination_card/{instance.name}/{filename}"


def sibling1_alumni_proof_upload_path(instance, filename):
    return f"child/sibling1_alumni_proof/{instance.child.name}/{filename}"


def sibling2_alumni_proof_upload_path(instance, filename):
    return f"child/sibling2_alumni_proof/{instance.child.name}/{filename}"

def child_armed_force_proof_upload_path(instance, filename):
    return f"child/child_armed_force_proof/{instance.name}/{filename}"


def child_aadhar_card_path_upload_path(instance, filename):
    return f"child/child_aadhar_card_path/{instance.name}/{filename}"
