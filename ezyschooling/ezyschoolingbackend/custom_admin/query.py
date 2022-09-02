def child_cart_query():
    query = """
            SELECT parents_parentprofile.name,parents_parentprofile.email,parents_parentprofile.phone,
            childs_child.name,schools_schoolprofile.name,parents_parentaddress.street_address,parents_parentaddress.city,
            parents_parentaddress.pincode,parents_parentaddress.monthly_budget,schools_schoolclasses.name,to_char(admission_forms_childschoolcart.timestamp, 'DD/MM/YYYY'),
            accounts_user.id,
            to_char(admission_forms_childschoolcart.timestamp, 'YYYYMMDD')
            FROM admission_forms_childschoolcart
            INNER JOIN admission_forms_commonregistrationform
            ON admission_forms_commonregistrationform.id = admission_forms_childschoolcart.form_id
            INNER JOIN accounts_user
            ON accounts_user.id = admission_forms_commonregistrationform.user_id
            INNER JOIN schools_schoolprofile
            ON schools_schoolprofile.id = admission_forms_childschoolcart.school_id
            INNER JOIN parents_parentprofile
            ON parents_parentprofile.id = accounts_user.current_parent
            INNER JOIN parents_parentaddress
            ON parents_parentaddress.parent_id = parents_parentprofile.id
            INNER JOIN childs_child
            ON childs_child.id = admission_forms_childschoolcart.child_id
            INNER JOIN schools_schoolclasses
            ON schools_schoolclasses.id = childs_child.class_applying_for_id
            ORDER BY to_char(admission_forms_childschoolcart.timestamp, 'YYYYMMDD') ASC
            """
    return query



def address_not_present_cart_query(tuple_data):
        
    return """
            SELECT parents_parentprofile.name,parents_parentprofile.email,parents_parentprofile.phone,
            childs_child.name,schools_schoolprofile.name,admission_forms_commonregistrationform.street_address,admission_forms_commonregistrationform.city,
            admission_forms_commonregistrationform.pincode,schools_schoolclasses.name,to_char(admission_forms_childschoolcart.timestamp, 'DD/MM/YYYY'),to_char(admission_forms_childschoolcart.timestamp, 'YYYYMMDD')
            FROM admission_forms_childschoolcart
            INNER JOIN admission_forms_commonregistrationform
            ON admission_forms_commonregistrationform.id = admission_forms_childschoolcart.form_id
            INNER JOIN accounts_user
            ON accounts_user.id = admission_forms_commonregistrationform.user_id
            INNER JOIN schools_schoolprofile
            ON schools_schoolprofile.id = admission_forms_childschoolcart.school_id
            INNER JOIN parents_parentprofile
            ON parents_parentprofile.id = accounts_user.current_parent
            INNER JOIN childs_child
            ON childs_child.id = admission_forms_childschoolcart.child_id
            INNER JOIN schools_schoolclasses
            ON schools_schoolclasses.id = childs_child.class_applying_for_id
            WHERE accounts_user.id  NOT IN {tuple}
            ORDER BY to_char(admission_forms_childschoolcart.timestamp, 'YYYYMMDD') ASC
            """.format(tuple=tuple_data)

def school_enquiry_parent_profile_present():
    return """
            SELECT DISTINCT schools_schoolenquiry.parent_name,schools_schoolenquiry.phone_no,
            schools_schoolenquiry.query,schools_schoolenquiry.email,schools_schoolprofile.name,
            parents_parentaddress.city,parents_parentaddress.pincode,parents_parentaddress.monthly_budget,
            to_char(schools_schoolenquiry.timestamp, 'DD/MM/YYYY'),accounts_user.email,to_char(schools_schoolenquiry.timestamp, 'YYYYMMDD') 
            FROM accounts_user
            INNER JOIN schools_schoolenquiry
            ON schools_schoolenquiry.email=accounts_user.email
            INNER JOIN schools_schoolprofile ON
            schools_schoolenquiry.school_id=schools_schoolprofile.id
            INNER JOIN parents_parentprofile
            ON accounts_user.id = parents_parentprofile.user_id
            INNER JOIN parents_parentaddress
            ON parents_parentaddress.parent_id = parents_parentprofile.id
            ORDER BY to_char(schools_schoolenquiry.timestamp, 'YYYYMMDD') ASC
           """
def school_enquiry_existing_parent_data():
    return """
            SELECT DISTINCT schools_schoolenquiry.parent_name,schools_schoolenquiry.phone_no,
            schools_schoolenquiry.query,schools_schoolenquiry.email,schools_schoolprofile.name,
            to_char(schools_schoolenquiry.timestamp, 'DD/MM/YYYY'),to_char(schools_schoolenquiry.timestamp, 'YYYYMMDD')
            FROM accounts_user
            INNER JOIN schools_schoolenquiry
            ON schools_schoolenquiry.email=accounts_user.email
            INNER JOIN schools_schoolprofile ON
            schools_schoolenquiry.school_id=schools_schoolprofile.id
            INNER JOIN parents_parentprofile
            ON accounts_user.id = parents_parentprofile.user_id
            INNER JOIN parents_parentaddress
            ON parents_parentaddress.parent_id = parents_parentprofile.id
            ORDER BY  to_char(schools_schoolenquiry.timestamp, 'YYYYMMDD') ASC
           """
def school_enquiry_all_data():
    return """
            SELECT DISTINCT schools_schoolenquiry.parent_name,schools_schoolenquiry.phone_no,
            schools_schoolenquiry.query,schools_schoolenquiry.email,schools_schoolprofile.name,
            to_char(schools_schoolenquiry.timestamp, 'DD/MM/YYYY'),to_char(schools_schoolenquiry.timestamp, 'YYYYMMDD') 
            FROM schools_schoolenquiry
            INNER JOIN schools_schoolprofile ON
            schools_schoolenquiry.school_id=schools_schoolprofile.id
            ORDER BY to_char(schools_schoolenquiry.timestamp, 'YYYYMMDD') ASC
           """
