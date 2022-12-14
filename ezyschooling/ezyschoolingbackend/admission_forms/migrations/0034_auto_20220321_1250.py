# Generated by Django 2.2.10 on 2022-03-21 07:20

import admission_forms.utils
import childs.utils
from django.db import migrations, models
import parents.utils


class Migration(migrations.Migration):

    dependencies = [
        ('admission_forms', '0033_auto_20220214_1402'),
    ]

    operations = [
        migrations.AlterField(
            model_name='commonregistrationform',
            name='baptism_certificate',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.baptism_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='caste_category_certificate',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.caste_category_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='differently_abled_proof',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.differently_abled_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='distance_affidavit',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.distance_affidavit_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='report_card',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.report_card_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='sibling1_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.sibling1_alumni_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='sibling2_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.sibling2_alumni_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='single_parent_proof',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.single_parent_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationform',
            name='transfer_certificate',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.transfer_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='baptism_certificate',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.baptism_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='caste_category_certificate',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.caste_category_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_aadhaar_card_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.child_aadhar_card_path_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_address_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.address_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_address_proof2',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.address_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_armed_force_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.child_armed_force_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_birth_certificate',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.child_birth_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_first_child_affidavit',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.first_child_affidavit_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_medical_certificate',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.medical_fitness_certificate_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_minority_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.minority_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='child_vaccination_card',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.child_vaccination_card_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='differently_abled_proof',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.differently_abled_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='distance_affidavit',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.distance_affidavit_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='father_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='father_covid_vaccination_certificate',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='father_pan_card_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_pan_card_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='father_parent_aadhar_card',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_addhar_card_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='father_special_ground_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_special_ground_proof),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='guardian_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='guardian_covid_vaccination_certificate',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='guardian_pan_card_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_pan_card_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='guardian_parent_aadhar_card',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_addhar_card_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='guardian_special_ground_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_special_ground_proof),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='mother_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='mother_covid_vaccination_certificate',
            field=models.FileField(blank=True, null=True, upload_to='images'),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='mother_pan_card_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_pan_card_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='mother_parent_aadhar_card',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_addhar_card_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='mother_special_ground_proof',
            field=models.FileField(blank=True, null=True, upload_to=parents.utils.parent_special_ground_proof),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='report_card',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.report_card_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='sibling1_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.sibling1_alumni_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='sibling2_alumni_proof',
            field=models.FileField(blank=True, null=True, upload_to=childs.utils.sibling2_alumni_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='single_parent_proof',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.single_parent_proof_upload_path),
        ),
        migrations.AlterField(
            model_name='commonregistrationformafterpayment',
            name='transfer_certificate',
            field=models.FileField(blank=True, null=True, upload_to=admission_forms.utils.transfer_certificate_upload_path),
        ),
    ]
