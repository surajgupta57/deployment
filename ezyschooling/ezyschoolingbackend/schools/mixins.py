from schools.models import SchoolProfile


class SchoolPerformCreateUpdateMixin:

    def perform_create(self, serializer):
        slug = self.kwargs.get("slug")
        school = SchoolProfile.objects.get(slug=slug)
        serializer.save(school=school)

    def perform_update(self, serializer):
        slug = self.kwargs.get("slug")
        school = SchoolProfile.objects.get(slug=slug)
        serializer.save(school=school)
