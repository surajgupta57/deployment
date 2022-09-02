import os
import urllib.request
from datetime import *
from io import BytesIO

import fitz
import googlemaps
import requests
from boto3 import Session
from pdf2image import convert_from_path
import xhtml2pdf.pisa as pisa
from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.http import HttpResponse
from django.template.loader import get_template
import geopy.distance

from parents.models import ParentProfile
from schools.models import DistancePoint
import logging
logger = logging.getLogger(__name__)
# from schools.models import DistancePoint, AdmissionSession


def check_empty_values(x):
    for i in x:
        if i in ["", None]:
            return False
    return True


def get_distance(a, b):
    API_KEY = settings.GOOGLE_MAP_API_KEY
    gmaps = googlemaps.Client(key=API_KEY)
    tomorrow = datetime.now().date() + relativedelta(days=1)
    dept_time = datetime.combine(tomorrow, time(3, 0))
    result = gmaps.distance_matrix(
        origins=a, destinations=[b], departure_time=dept_time
    )
    return result["rows"][0]["elements"][0]["distance"]["value"] / 1000


def get_aerial_distance(a, b):
    return geopy.distance.distance(a, b).km


def calculate_distance_points(app):
    school_coordinates = (app.school.latitude, app.school.longitude)
    child_coordinates1 = (app.form.latitude, app.form.longitude)
    child_coordinates2 = (app.form.latitude_secondary, app.form.longitude_secondary)
    distance = min(
        get_aerial_distance(school_coordinates, child_coordinates1),
        get_aerial_distance(school_coordinates, child_coordinates2),
    )
    app.calculated_distance = distance
    app.save()
    match = DistancePoint.objects.filter(school=app.school).filter(
        start__lte=distance, end__gte=distance
    )
    if match.exists():
        return match.first().point
    else:
        return 0


def calculate_points(app):
    point = app.school.points.first()
    child = app.child
    form = app.form

    total_points = 0
    distance_points = calculate_distance_points(app)
    if distance_points:
        app.distance_points = distance_points
        total_points += distance_points

    if child.armed_force_points:
        app.children_of_armed_force_points = point.children_of_armed_force_points
        total_points += app.children_of_armed_force_points

    if child.student_with_special_needs_points:
        app.student_with_special_needs_points = point.student_with_special_needs_points
        total_points += app.student_with_special_needs_points

    if child.minority_points:
        app.minority_points = point.minority_points
        total_points += app.minority_points

    if child.gender == "female":
        app.girl_child_point = point.girl_child_points
        total_points += app.girl_child_point

    if form.single_parent:
        app.single_parent_point = point.single_parent_points
        total_points += app.single_parent_point

    if child.is_christian:
        app.christian_points = point.is_christian_points
        total_points += app.christian_points

    if form.first_child:
        app.first_born_child_points = point.first_born_child_points
        total_points += app.first_born_child_points

    if form.single_child:
        app.single_child_points = point.single_child_points
        total_points += app.single_child_points

    if form.first_girl_child:
        app.first_girl_child_points = point.first_girl_child_points
        total_points += app.first_girl_child_points

    if form.single_child and child.gender == "female":
        app.single_girl_child_points = point.single_girl_child_points
        total_points += app.single_girl_child_points

    if form.staff_ward:
        given_points = 0
        if not child.orphan and given_points < point.staff_ward_points:
            if (
                    form.mother_staff_ward_school_name == app.school
                    or form.father_staff_ward_school_name == app.school
            ):
                given_points = point.staff_ward_points

        if child.orphan and given_points < point.staff_ward_points:
            if form.guardian_staff_ward_school_name == app.school:
                given_points = point.staff_ward_points

        app.staff_ward_points = given_points
        total_points += app.staff_ward_points

    if (
            form.sibling1_alumni_school_name == app.school
            or form.sibling2_alumni_school_name == app.school
    ):
        app.siblings_studied_points = point.siblings_points
        total_points += app.siblings_studied_points

    if not child.orphan:
        if (
                form.father.alumni_school_name == app.school
                or form.mother.alumni_school_name == app.school
        ):
            app.parents_alumni_points = point.parent_alumni_points
            total_points += app.parents_alumni_points

    if form.transport_facility_required:
        app.transport_facility_points = point.transport_facility_points
        total_points += app.transport_facility_points

    if not child.orphan:
        if form.father.covid_vaccination_certificate:
            app.father_covid_vacination_certifiacte_points = (
                point.father_covid_vacination_certifiacte_points
            )
            total_points += app.father_covid_vacination_certifiacte_points

        if form.mother.covid_vaccination_certificate:
            app.mother_covid_vacination_certifiacte_points = (
                point.mother_covid_vacination_certifiacte_points
            )
            total_points += app.mother_covid_vacination_certifiacte_points

    if child.orphan:
        if form.guardian.covid_vaccination_certificate:
            app.guardian_covid_vacination_certifiacte_points = (
                point.guardian_covid_vacination_certifiacte_points
            )
            total_points += app.guardian_covid_vacination_certifiacte_points

    if not child.orphan:
        if form.father.frontline_helper:
            app.father_covid_19_frontline_warrior_points = (
                point.father_covid_19_frontline_warrior_points
            )
            total_points += app.father_covid_19_frontline_warrior_points

        if form.mother.frontline_helper:
            app.mother_covid_19_frontline_warrior_points = (
                point.mother_covid_19_frontline_warrior_points
            )
            total_points += app.mother_covid_19_frontline_warrior_points

    if child.orphan:
        if form.guardian.frontline_helper:
            app.guardian_covid_19_frontline_warrior_points = (
                point.guardian_covid_19_frontline_warrior_points
            )
            total_points += app.guardian_covid_19_frontline_warrior_points

    if child.intre_state_transfer:
        app.state_transfer_points = point.state_transfer_points
        total_points += app.state_transfer_points

    app.total_points = total_points
    app.save()


def evaluate_distance_points(pref, school):
    school_coordinates = (school.latitude, school.longitude)
    child_coordinates1 = (pref.latitude, pref.longitude)
    child_coordinates2 = (pref.latitude_secondary, pref.longitude_secondary)
    distance = min(
        get_aerial_distance(school_coordinates, child_coordinates1),
        get_aerial_distance(school_coordinates, child_coordinates2),
    )

    match = DistancePoint.objects.filter(school=school).filter(
        start__lte=distance, end__gte=distance
    )
    if match.exists():
        return match.first().point
    else:
        return 0


def evaluate_points(pref, school):
    total_points = 0
    children_of_armed_force_points = 0
    single_child_points = 0
    siblings_points = 0
    parent_alumni_points = 0
    staff_ward_points = 0
    first_born_child_points = 0
    first_girl_child_points = 0
    single_girl_child_points = 0
    is_christian_points = 0
    girl_child_points = 0
    single_parent_points = 0
    minority_points = 0
    student_with_special_needs_points = 0
    transport_facility_points = 0
    distance_points = evaluate_distance_points(pref, school)

    point = school.points.first()
    total_points += distance_points

    if pref.children_of_armed_force_points:
        children_of_armed_force_points = point.children_of_armed_force_points
        total_points += children_of_armed_force_points

    if pref.single_child_points:
        single_child_points = point.single_child_points
        total_points += single_child_points

    if pref.siblings_points:
        siblings_points = point.siblings_points
        total_points += siblings_points

    if pref.parent_alumni_points:
        parent_alumni_points = point.parent_alumni_points
        total_points += parent_alumni_points

    if pref.staff_ward_points:
        staff_ward_points = point.staff_ward_points
        total_points += staff_ward_points

    if pref.first_born_child_points:
        first_born_child_points = point.first_born_child_points
        total_points += first_born_child_points

    if pref.first_girl_child_points:
        first_girl_child_points = point.first_girl_child_points
        total_points += first_girl_child_points

    if pref.single_girl_child_points:
        single_girl_child_points = point.single_girl_child_points
        total_points += single_girl_child_points

    if pref.is_christian_points:
        is_christian_points = point.is_christian_points
        total_points += is_christian_points

    if pref.girl_child_points:
        girl_child_points = point.girl_child_points
        total_points += girl_child_points

    if pref.single_parent_points:
        single_parent_points = point.single_parent_points
        total_points += single_parent_points

    if pref.minority_points:
        minority_points = point.minority_points
        total_points += minority_points

    if pref.student_with_special_needs_points:
        student_with_special_needs_points = point.student_with_special_needs_points
        total_points += student_with_special_needs_points

    if pref.transport_facility_points:
        transport_facility_points = point.transport_facility_points
        total_points += transport_facility_points

    return {
        "total_points": total_points,
        "children_of_armed_force_points": children_of_armed_force_points,
        "single_child_points": single_child_points,
        "siblings_points": siblings_points,
        "parent_alumni_points": parent_alumni_points,
        "staff_ward_points": staff_ward_points,
        "first_born_child_points": first_born_child_points,
        "first_girl_child_points": first_girl_child_points,
        "single_girl_child_points": single_girl_child_points,
        "is_christian_points": is_christian_points,
        "girl_child_points": girl_child_points,
        "single_parent_points": single_parent_points,
        "minority_points": minority_points,
        "student_with_special_needs_points": student_with_special_needs_points,
        "transport_facility_points": transport_facility_points,
        "distance_points": distance_points,
    }


def sibling1_alumni_proof_upload_path(instance, filename):
    return f"admission-form/sibling1_alumni_proof/{instance.child.name}/{filename}"


def sibling2_alumni_proof_upload_path(instance, filename):
    return f"admission-form/sibling2_alumni_proof/{instance.child.name}/{filename}"


def transfer_certificate_upload_path(instance, filename):
    return f"admission-form/transfer_certificate/{instance.child.name}/{filename}"


def report_card_upload_path(instance, filename):
    return f"admission-form/report_card/{instance.child.name}/{filename}"


def non_collab_receipt_upload_path(instance, filename):
    return f"admission-form/non_collab_receipt/{instance.child.name}/{filename}"


def family_photo_upload_path(instance, filename):
    return f"admission-form/family_photo/{instance.child.name}/{filename}"


def distance_affidavit_upload_path(instance, filename):
    return f"admission-form/distance_affidavit/{instance.child.name}/{filename}"


def baptism_certificate_upload_path(instance, filename):
    return f"admission-form/baptism_certificate/{instance.child.name}/{filename}"


def parent_signature_upload_path(instance, filename):
    return f"admission-form/parent_signature/{instance.child.name}/{filename}"


def differently_abled_upload_path(instance, filename):
    return f"admission-form/differently_abled/{instance.child.name}/{filename}"


def single_parent_proof_upload_path(instance, filename):
    return f"admission-form/single_parent_proof/{instance.child.name}/{filename}"


def caste_category_certificate_upload_path(instance, filename):
    return f"admission-form/caste_category_certificate/{instance.child.name}/{filename}"


class Render:
    @staticmethod
    def render(path, params):
        template = get_template(path)
        html = template.render(params)
        response = BytesIO()
        pdf = pisa.pisaDocument(BytesIO(html.encode("UTF-8")), response)
        if not pdf.err:
            return HttpResponse(response.getvalue(), content_type="application/pdf")
        else:
            return HttpResponse("Error Rendering PDF", status=400)

    def link_callback(uri, rel):
        """
        Convert HTML URIs to absolute system paths so xhtml2pdf can access those
        resources
        """
        # use short variable names
        sUrl = settings.STATIC_URL  # Typically /static/
        sRoot = settings.STATIC_ROOT  # Typically /home/userX/project_static/
        mUrl = settings.MEDIA_URL  # Typically /static/media/
        mRoot = settings.MEDIA_ROOT  # Typically /home/userX/project_static/media/

        # convert URIs to absolute system paths
        if uri.startswith(mUrl):
            path = os.path.join(mRoot, uri.replace(mUrl, ""))
        elif uri.startswith(sUrl):
            path = os.path.join(sRoot, uri.replace(sUrl, ""))
        else:
            return uri  # handle absolute uri (ie: http://some.tld/foo.png)

        # make sure that file exists
        if not os.path.isfile(path):
            raise Exception("media URI must start with %s or %s" % (sUrl, mUrl))
        return path


def get_current_session():
    # if AdmissionSession.objects.all().order_by('-id')[:2][1] and AdmissionSession.objects.all().order_by('-id')[:2][0]:
    #     return AdmissionSession.objects.all().order_by('-id')[:2][1].name
    # else:
    return "2021-2022"


def download_file(download_url, filename):
    """
        This is use to generate png files from the given pdf.
        Parameter: -
            download_url - pdf file path to download it.
            filename - pdf file path where to save it.
    """
    response = urllib.request.urlopen(download_url)
    file = open(filename, "wb")
    file.write(response.read())
    file.close()


def s3BucketPDFFiles(child_id, filepath):
    """
        This is use to generate png files from the given pdf.
        Parameter: -
            filepath - gives pdf file path
    """
    all_files = []
    pdf_name = ((filepath.split(".com/")[1]).split("/"))[1]
    _, filename = os.path.split(filepath)
    file = f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{child_id}/' + filename
    download_file(filepath, file)

    # To open the fitz file.
    # Use saved pdf file path and perform further operation which ever necessary to convert it to png.
    # For Fitz it will iterate on per page of pdf to generate in the given file type

    zoom_x = 2.0  # horizontal zoom
    zoom_y = 2.0  # vertical zoom
    mat = fitz.Matrix(zoom_x, zoom_y)
    images = fitz.open(file)  # open document
    list_of_pages = [*range(0, images.pageCount, 1)]
    new_images = []
    for page_number in list_of_pages:
        new_images.append({
            'id': page_number,
            'pdf': images.load_page(page_number)
        })

    def pdfSorting(e):
        return e['id']

    new_images.sort(key=pdfSorting)

    for page in new_images:  # iterate through the pages
        pix = page['pdf'].get_pixmap(matrix=mat)
        pix.save(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{child_id}/' + pdf_name + "_%i.png" % page['id'])
        pix = None
    for root, directories, files in os.walk(
            f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{child_id}/', topdown=False
    ):
        for name in files:
            if name.endswith(".png") and name.startswith(pdf_name):
                all_files.append({
                    'id': files.index(name),
                    'url': os.path.join(root, name)
                })

    images.close()
    return all_files


def bucketPdfToImage(app):
    if not os.path.isdir(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{app.child.id}'):
        os.makedirs(f'{settings.MEDIA_ROOT}/form_pdf_image_folder/{app.child.id}', mode=0o666)

    if (
            app.child.medical_certificate
            and str(app.child.medical_certificate.url).endswith(".pdf")
    ):

        app.child.medical_certificate = list(
            s3BucketPDFFiles(app.child.id, str(app.child.medical_certificate.url))
        )
    else:
        if not app.child.medical_certificate:
            app.child.medical_certificate = None
        else:
            if app.child.medical_certificate:
                app.child.medical_certificate = [
                    app.child.medical_certificate.url
                ]

    if (
            app.registration_data.child_birth_certificate
            and str(app.registration_data.child_birth_certificate.url).endswith(".pdf")
    ):

        app.registration_data.child_birth_certificate = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_birth_certificate.url)
        )
    else:
        if not app.registration_data.child_birth_certificate:
            app.registration_data.child_birth_certificate = None

        else:
            if app.registration_data.child_birth_certificate:
                app.registration_data.child_birth_certificate = [
                    app.registration_data.child_birth_certificate.url
                ]

    if (
            app.registration_data.child_aadhaar_card_proof
            and str(app.registration_data.child_aadhaar_card_proof.url).endswith(".pdf")
    ):

        app.registration_data.child_aadhaar_card_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_aadhaar_card_proof.url)
        )
    else:
        if not app.registration_data.child_aadhaar_card_proof:
            app.registration_data.child_aadhaar_card_proof = None
        else:
            if app.registration_data.child_aadhaar_card_proof:
                app.registration_data.child_aadhaar_card_proof = [
                    app.registration_data.child_aadhaar_card_proof.url
                ]

    if (
            app.registration_data.child_address_proof
            and str(app.registration_data.child_address_proof.url).endswith(".pdf")
    ):

        app.registration_data.child_address_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_address_proof.url)
        )
    else:
        if not app.registration_data.child_address_proof:
            app.registration_data.child_address_proof = None
        else:
            if app.registration_data.child_address_proof:
                app.registration_data.child_address_proof = [
                    app.registration_data.child_address_proof.url
                ]

    if (
            app.registration_data.child_address_proof2
            and str(app.registration_data.child_address_proof2.url).endswith(".pdf")
    ):

        app.registration_data.child_address_proof2 = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_address_proof2.url)
        )
    else:
        if not app.registration_data.child_address_proof2:
            app.registration_data.child_address_proof2 = None
        else:
            if app.registration_data.child_address_proof2:
                app.registration_data.child_address_proof2 = [
                    app.registration_data.child_address_proof2.url
                ]
    if (
            app.registration_data.parent_signature_upload
            and str(app.registration_data.parent_signature_upload.url).endswith(".pdf")
    ):
        app.registration_data.parent_signature_upload = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.parent_signature_upload.url)
        )
    else:
        if not app.registration_data.parent_signature_upload:
            app.registration_data.parent_signature_upload = None
        else:
            if app.registration_data.parent_signature_upload:
                app.registration_data.parent_signature_upload = [
                    app.registration_data.parent_signature_upload.url
                ]

    if (
            app.registration_data.child_medical_certificate
            and str(app.registration_data.child_medical_certificate.url).endswith(".pdf")
    ):

        app.registration_data.child_medical_certificate = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_medical_certificate.url)
        )
    else:
        if not app.registration_data.child_medical_certificate:
            app.registration_data.child_medical_certificate = None
        else:
            if app.registration_data.child_medical_certificate:
                app.registration_data.child_medical_certificate = [
                    app.registration_data.child_medical_certificate.url
                ]

    if (
            app.registration_data.child_first_child_affidavit
            and str(app.registration_data.child_first_child_affidavit.url).endswith(".pdf")
    ):

        app.registration_data.child_first_child_affidavit = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_first_child_affidavit.url)
        )
    else:
        if not app.registration_data.child_first_child_affidavit:
            app.registration_data.child_first_child_affidavit = None
        else:
            if app.registration_data.child_first_child_affidavit:
                app.registration_data.child_first_child_affidavit = [
                    app.registration_data.child_first_child_affidavit.url
                ]

    if (
            app.registration_data.child_vaccination_card
            and str(app.registration_data.child_vaccination_card.url).endswith(".pdf")
    ):

        app.registration_data.child_vaccination_card = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_vaccination_card.url)
        )
    else:
        if not app.registration_data.child_vaccination_card:
            app.registration_data.child_vaccination_card = None
        else:
            if app.registration_data.child_vaccination_card:
                app.registration_data.child_vaccination_card = [
                    app.registration_data.child_vaccination_card.url
                ]

    if (
            app.registration_data.child_minority_proof
            and str(app.registration_data.child_minority_proof.url).endswith(".pdf")
    ):

        app.registration_data.child_minority_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_minority_proof.url)
        )
    else:
        if not app.registration_data.child_minority_proof:
            app.registration_data.child_minority_proof = None
        else:
            if app.registration_data.child_minority_proof:
                app.registration_data.child_minority_proof = [
                    app.registration_data.child_minority_proof.url
                ]

    if (
            app.registration_data.child_armed_force_proof
            and str(app.registration_data.child_armed_force_proof.url).endswith(".pdf")
    ):

        app.registration_data.child_armed_force_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.child_armed_force_proof.url)
        )
    else:
        if not app.registration_data.child_armed_force_proof:
            app.registration_data.child_armed_force_proof = None
        else:
            if app.registration_data.child_armed_force_proof:
                app.registration_data.child_armed_force_proof = [
                    app.registration_data.child_armed_force_proof.url
                ]

    if (
            app.registration_data.single_parent_proof
            and str(app.registration_data.single_parent_proof.url).endswith(".pdf")
    ):

        app.registration_data.single_parent_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.single_parent_proof.url)
        )
    else:
        if not app.registration_data.single_parent_proof:
            app.registration_data.single_parent_proof = None
        else:
            if app.registration_data.single_parent_proof:
                app.registration_data.single_parent_proof = [
                    app.registration_data.single_parent_proof.url
                ]

    if (
            app.registration_data.report_card
            and str(app.registration_data.report_card.url).endswith(".pdf")
    ):

        app.registration_data.report_card = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.report_card.url)
        )
    else:
        if not app.registration_data.report_card:
            app.registration_data.report_card = None
        else:
            if app.registration_data.report_card:
                app.registration_data.report_card = [app.registration_data.report_card.url]

    if (
            app.registration_data.transfer_certificate
            and str(app.registration_data.transfer_certificate.url).endswith(".pdf")
    ):

        app.registration_data.transfer_certificate = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.transfer_certificate.url)
        )
    else:
        if not app.registration_data.transfer_certificate:
            app.registration_data.transfer_certificate = None
        else:
            if app.registration_data.transfer_certificate:
                app.registration_data.transfer_certificate = [
                    app.registration_data.transfer_certificate.url
                ]

    if (
            app.registration_data.sibling1_alumni_proof
            and str(app.registration_data.sibling1_alumni_proof.url).endswith(".pdf")
    ):

        app.registration_data.sibling1_alumni_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.sibling1_alumni_proof.url)
        )
    else:
        if not app.registration_data.sibling1_alumni_proof:
            app.registration_data.sibling1_alumni_proof = None
        else:
            if app.registration_data.sibling1_alumni_proof:
                app.registration_data.sibling1_alumni_proof = [
                    app.registration_data.sibling1_alumni_proof.url
                ]

    if (
            app.registration_data.sibling2_alumni_proof
            and str(app.registration_data.sibling2_alumni_proof.url).endswith(".pdf")
    ):

        app.registration_data.sibling2_alumni_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.sibling2_alumni_proof.url)
        )
    else:
        if not app.registration_data.sibling2_alumni_proof:
            app.registration_data.sibling2_alumni_proof = None
        else:
            if app.registration_data.sibling2_alumni_proof:
                app.registration_data.sibling2_alumni_proof = [
                    app.registration_data.sibling2_alumni_proof.url
                ]

    if (
            app.registration_data.distance_affidavit
            and str(app.registration_data.distance_affidavit.url).endswith(".pdf")
    ):

        app.registration_data.distance_affidavit = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.distance_affidavit.url)
        )
    else:
        if not app.registration_data.distance_affidavit:
            app.registration_data.distance_affidavit = None
        else:
            if app.registration_data.distance_affidavit:
                app.registration_data.distance_affidavit = [
                    app.registration_data.distance_affidavit.url
                ]

    if (
            app.registration_data.baptism_certificate
            and str(app.registration_data.baptism_certificate.url).endswith(".pdf")
    ):

        app.registration_data.baptism_certificate = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.baptism_certificate.url)
        )
    else:
        if not app.registration_data.baptism_certificate:
            app.registration_data.baptism_certificate = None
        else:
            if app.registration_data.baptism_certificate:
                app.registration_data.baptism_certificate = [
                    app.registration_data.baptism_certificate.url
                ]

    if (
            app.registration_data.differently_abled_proof
            and str(app.registration_data.differently_abled_proof.url).endswith(".pdf")
    ):

        app.registration_data.differently_abled_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.differently_abled_proof.url)
        )
    else:
        if not app.registration_data.differently_abled_proof:
            app.registration_data.differently_abled_proof = None
        else:
            if app.registration_data.differently_abled_proof:
                app.registration_data.differently_abled_proof = [
                    app.registration_data.differently_abled_proof.url
                ]

    if (
            app.registration_data.caste_category_certificate
            and str(app.registration_data.caste_category_certificate.url).endswith(".pdf")
    ):

        app.registration_data.caste_category_certificate = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.caste_category_certificate.url)
        )
    else:
        if not app.registration_data.caste_category_certificate:
            app.registration_data.caste_category_certificate = None
        else:
            if app.registration_data.caste_category_certificate:
                app.registration_data.caste_category_certificate = [
                    app.registration_data.caste_category_certificate.url
                ]

    if (
            app.registration_data.father_special_ground_proof
            and str(app.registration_data.father_special_ground_proof.url).endswith(".pdf")
    ):

        app.registration_data.father_special_ground_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.father_special_ground_proof.url)
        )
    else:
        if not app.registration_data.father_special_ground_proof:
            app.registration_data.father_special_ground_proof = None
        else:
            if app.registration_data.father_special_ground_proof:
                app.registration_data.father_special_ground_proof = [
                    app.registration_data.father_special_ground_proof.url
                ]

    if (
            app.registration_data.father_parent_aadhar_card
            and str(app.registration_data.father_parent_aadhar_card.url).endswith(".pdf")
    ):

        app.registration_data.father_parent_aadhar_card = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.father_parent_aadhar_card.url)
        )
    else:
        if not app.registration_data.father_parent_aadhar_card:
            app.registration_data.father_parent_aadhar_card = None
        else:
            if app.registration_data.father_parent_aadhar_card:
                app.registration_data.father_parent_aadhar_card = [
                    app.registration_data.father_parent_aadhar_card.url
                ]

    if (
            app.registration_data.father_pan_card_proof
            and str(app.registration_data.father_pan_card_proof.url).endswith(".pdf")
    ):

        app.registration_data.father_pan_card_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.father_pan_card_proof.url)
        )
    else:
        if not app.registration_data.father_pan_card_proof:
            app.registration_data.father_pan_card_proof = None
        else:
            if app.registration_data.father_pan_card_proof:
                app.registration_data.father_pan_card_proof = [
                    app.registration_data.father_pan_card_proof.url
                ]

    if (
            app.registration_data.father_alumni_proof
            and str(app.registration_data.father_alumni_proof.url).endswith(".pdf")
    ):

        app.registration_data.father_alumni_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.father_alumni_proof.url)
        )
    else:
        if not app.registration_data.father_alumni_proof:
            app.registration_data.father_alumni_proof = None
        else:
            if app.registration_data.father_alumni_proof:
                app.registration_data.father_alumni_proof = [
                    app.registration_data.father_alumni_proof.url
                ]

    if (
            app.registration_data.father_covid_vaccination_certificate
            and str(app.registration_data.father_covid_vaccination_certificate.url).endswith(".pdf")
    ):

        app.registration_data.father_covid_vaccination_certificate = list(
                s3BucketPDFFiles(app.child.id,
                                 app.registration_data.father_covid_vaccination_certificate.url
            )
        )
    else:
        if not app.registration_data.father_covid_vaccination_certificate:
            app.registration_data.father_covid_vaccination_certificate = None
        else:
            if app.registration_data.father_covid_vaccination_certificate:
                app.registration_data.father_covid_vaccination_certificate = [
                    app.registration_data.father_covid_vaccination_certificate.url
                ]

    if (
            app.registration_data.mother_special_ground_proof
            and str(app.registration_data.mother_special_ground_proof.url).endswith(".pdf")
    ):

        app.registration_data.mother_special_ground_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.mother_special_ground_proof.url)
        )
    else:
        if not app.registration_data.mother_special_ground_proof:
            app.registration_data.mother_special_ground_proof = None
        else:
            if app.registration_data.mother_special_ground_proof:
                app.registration_data.mother_special_ground_proof = [
                    app.registration_data.mother_special_ground_proof.url
                ]

    if (
            app.registration_data.mother_parent_aadhar_card
            and str(app.registration_data.mother_parent_aadhar_card.url).endswith(".pdf")
    ):

        app.registration_data.mother_parent_aadhar_card = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.mother_parent_aadhar_card.url)
        )
    else:
        if not app.registration_data.mother_parent_aadhar_card:
            app.registration_data.mother_parent_aadhar_card = None
        else:
            if app.registration_data.mother_parent_aadhar_card:
                app.registration_data.mother_parent_aadhar_card = [
                    app.registration_data.mother_parent_aadhar_card.url
                ]

    if (
            app.registration_data.mother_pan_card_proof
            and str(app.registration_data.mother_pan_card_proof.url).endswith(".pdf")
    ):

        app.registration_data.mother_pan_card_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.mother_pan_card_proof.url)
        )
    else:
        if not app.registration_data.mother_pan_card_proof:
            app.registration_data.mother_pan_card_proof = None
        else:
            if app.registration_data.mother_pan_card_proof:
                app.registration_data.mother_pan_card_proof = [
                    app.registration_data.mother_pan_card_proof.url
                ]

    if (
            app.registration_data.mother_alumni_proof
            and str(app.registration_data.mother_alumni_proof.url).endswith(".pdf")
    ):

        app.registration_data.mother_alumni_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.mother_alumni_proof.url)
        )
    else:
        if not app.registration_data.mother_alumni_proof:
            app.registration_data.mother_alumni_proof = None
        else:
            if app.registration_data.mother_alumni_proof:
                app.registration_data.mother_alumni_proof = [
                    app.registration_data.mother_alumni_proof.url
                ]

    if (
            app.registration_data.mother_covid_vaccination_certificate
            and str(app.registration_data.mother_covid_vaccination_certificate.url).endswith(".pdf")
    ):

        app.registration_data.mother_covid_vaccination_certificate = list(
                s3BucketPDFFiles(app.child.id,
                                 app.registration_data.mother_covid_vaccination_certificate.url
            )
        )
    else:
        if not app.registration_data.mother_covid_vaccination_certificate:
            app.registration_data.mother_covid_vaccination_certificate = None
        else:
            if app.registration_data.mother_covid_vaccination_certificate:
                app.registration_data.mother_covid_vaccination_certificate = [
                    app.registration_data.mother_covid_vaccination_certificate.url
                ]

    if (
            app.registration_data.guardian_special_ground_proof
            and str(app.registration_data.guardian_special_ground_proof.url).endswith(".pdf")
    ):

        app.registration_data.guardian_special_ground_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.guardian_special_ground_proof.url)
        )
    else:
        if not app.registration_data.guardian_special_ground_proof:
            app.registration_data.guardian_special_ground_proof = None
        else:
            if app.registration_data.guardian_special_ground_proof:
                app.registration_data.guardian_special_ground_proof = [
                    app.registration_data.guardian_special_ground_proof.url
                ]

    if (
            app.registration_data.guardian_parent_aadhar_card
            and str(app.registration_data.guardian_parent_aadhar_card.url).endswith(".pdf")
    ):

        app.registration_data.guardian_parent_aadhar_card = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.guardian_parent_aadhar_card.url)
        )
    else:
        if not app.registration_data.guardian_parent_aadhar_card:
            app.registration_data.guardian_parent_aadhar_card = None
        else:
            if app.registration_data.guardian_parent_aadhar_card:
                app.registration_data.guardian_parent_aadhar_card = [
                    app.registration_data.guardian_parent_aadhar_card.url
                ]

    if (
            app.registration_data.guardian_pan_card_proof
            and str(app.registration_data.guardian_pan_card_proof.url).endswith(".pdf")
    ):

        app.registration_data.guardian_pan_card_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.guardian_pan_card_proof.url)
        )
    else:
        if not app.registration_data.guardian_pan_card_proof:
            app.registration_data.guardian_pan_card_proof = None
        else:
            if app.registration_data.guardian_pan_card_proof:
                app.registration_data.guardian_pan_card_proof = [
                    app.registration_data.guardian_pan_card_proof.url
                ]

    if (
            app.registration_data.guardian_alumni_proof
            and str(app.registration_data.guardian_alumni_proof.url).endswith(".pdf")
    ):

        app.registration_data.guardian_alumni_proof = list(
            s3BucketPDFFiles(app.child.id, app.registration_data.guardian_alumni_proof.url)
        )
    else:
        if not app.registration_data.guardian_alumni_proof:
            app.registration_data.guardian_alumni_proof = None
        else:
            if app.registration_data.guardian_alumni_proof:
                app.registration_data.guardian_alumni_proof = [
                    app.registration_data.guardian_alumni_proof.url
                ]

    if (
            app.registration_data.guardian_covid_vaccination_certificate
            and str(app.registration_data.guardian_covid_vaccination_certificate.url).endswith(".pdf")
    ):

        app.registration_data.guardian_covid_vaccination_certificate = list(
                s3BucketPDFFiles(app.child.id,
                                 app.registration_data.guardian_covid_vaccination_certificate.url
            )
        )
    else:
        if not app.registration_data.guardian_covid_vaccination_certificate:
            app.registration_data.guardian_covid_vaccination_certificate = None
        else:
            if app.registration_data.guardian_covid_vaccination_certificate:
                app.registration_data.guardian_covid_vaccination_certificate = [
                    app.registration_data.guardian_covid_vaccination_certificate.url
                ]
    return app


hsm_user_id = settings.WHATSAPP_HSM_USER_ID
hsm_user_password = settings.WHATSAPP_HSM_USER_PASSWORD


def atomic_cart_whatsapp_msg(phone_no):
    msg_template = f"Dear Parent\nYou shortlisted some schools yesterday on Ezyschooling but have not yet completed the application process.\n\n75000+ parents have already applied through Ezyschooling!\nSubmit your application form before the seats get filled in your dream schools: https://ezyschooling.com/admissions/selected/schools \n\nIf you have any doubts, feel free to contact us on 91-8766340464.\n\nRegards\nEzyschooling"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(phone_no) == 10:
        phone_no = "91" + phone_no
    request_body = {
        'method': 'SendMessage',
        'format': 'json',
        'send_to': phone_no,
        'v': '1.1',
        'auth_scheme': 'plain',
        'isHSM': True,
        'msg_type': 'HSM',
        'msg': msg_template,
        'userid': hsm_user_id,
        'password': hsm_user_password}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        requests.post(endpoint, headers=headers, data=request_body)
        logger.info(f"Message send to {phone_no}")
    except:
        logger.info(f"No Detail found")

def send_form_submit_whatsapp_msg(phone_no, user_slug):
    applications_link = f"https://ezyschooling.com/profile/{user_slug}/submittedApplications"
    msg_template = f"Hello Parent, \nThank you for choosing Ezyschooling to submit the school application form. Your application has been submitted to the school and now you don’t need to pay any application form charges at the school.\n\nDownload your application form for your reference: {applications_link}\n\nAlso, the school will be contacting you shortly to arrange a visit to the school. In case you have any doubts, feel free to contact us on 91-8766340464.\n\nWe will keep you updated regarding the application status through email and WhatsApp as well.\n\nRegards\nEzyschooling"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(phone_no) == 10:
        phone_no = "91" + phone_no
    request_body = {
        'method': 'SendMessage',
        'format': 'json',
        'send_to': phone_no,
        'v': '1.1',
        'auth_scheme': 'plain',
        'isHSM': True,
        'msg_type': 'HSM',
        'msg': msg_template,
        'userid': hsm_user_id,
        'password': hsm_user_password}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        requests.post(endpoint, headers=headers, data=request_body)
        logger.info(f"Message send to {phone_no}")
    except:
        logger.info(f"No Detail found")

def send_not_selected_whatsapp_msg(phone_no, school): #rejected msg
    msg_template = f"Dear Parent, \n\nYour application has been rejected by {school}. You can still explore and apply to some other great schools through Ezyschooling: https://ezyschooling.com/admissions\n\nIn case you have any doubts, feel free to contact us on 91-8766340464.\n\nRegards\nEzyschooling"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(phone_no) == 10:
        phone_no = "91" + phone_no
    request_body = {
        'method': 'SendMessage',
        'format': 'json',
        'send_to': phone_no,
        'v': '1.1',
        'auth_scheme': 'plain',
        'isHSM': True,
        'msg_type': 'HSM',
        'msg': msg_template,
        'userid': hsm_user_id,
        'password': hsm_user_password}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        requests.post(endpoint, headers=headers, data=request_body)
        logger.info(f"Message send to {phone_no}")
    except:
        logger.info(f"No Detail found")


def send_selected_whatsapp_msg(phone_no, school): #accepted msg

    msg_template = f"Dear Parent, \n\nYour application has been accepted to {school}. Congratulations from the Ezyschooling family!\n\nYou can now visit or contact the school and secure the seat for your child after completing all the admission formalities.\n\nRegards,\nEzyschooling"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(phone_no) == 10:
        phone_no = "91" + phone_no
    request_body = {
        'method': 'SendMessage',
        'format': 'json',
        'send_to': phone_no,
        'v': '1.1',
        'auth_scheme': 'plain',
        'isHSM': True,
        'msg_type': 'HSM',
        'msg': msg_template,
        'userid': str(hsm_user_id),
        'password': str(hsm_user_password)}
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        requests.post(endpoint, headers=headers, data=request_body)
    except Exception as e:
        pass


def send_2_week_feedback_form_whatsapp_msg(phone_no):
    feedback_link = f"https://form.jotform.com/220783649056463"
    msg_template = f"*Hello Parent*,\n\nThank you for choosing Ezyschooling! We constantly strive towards providing the highest quality service to you and care deeply about how our platform can better serve your needs. \n\nWe would be obliged if you could spare a few minutes to fill up the feedback form attached to the following link: {feedback_link}\n\n*Regards*,\n*Ezyschooling*"
    endpoint = 'http://media.smsgupshup.com/GatewayAPI/rest'
    if len(phone_no) == 10:
        phone_no = "91" + phone_no
    request_body = {
        'method': 'SendMessage',
        'format': 'json',
        'send_to': phone_no,
        'v': '1.1',
        'auth_scheme': 'plain',
        'isHSM': True,
        'msg_type': 'HSM',
        'msg': msg_template,
        'userid': hsm_user_id,
        'password': hsm_user_password}

    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    try:
        requests.post(endpoint, headers=headers, data=request_body)
        logger.info(f"Message send to {phone_no}")
    except:
        logger.info(f"No Detail found")
def atomic_cart_whatsapp(user_id):
    from accounts.models import User
    from notification.models import WhatsappSubscribers
    user_obj = User.objects.get(id=user_id)
    if user_obj and WhatsappSubscribers.objects.filter(user=user_obj,is_Subscriber=True).exists():
        number = WhatsappSubscribers.objects.get(user=user_obj)
        atomic_cart_whatsapp_msg(number.phone_number)
        logger.info(f"Whatsapp Message sent to {number.phone_number}")
    else:
        logger.info(f"No Detail found")
