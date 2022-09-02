def applied_resume_upload_path(instance, filename):
    return f"jobs/applied/{instance.email}/{filename}"
