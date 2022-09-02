# from os import setgroups

from rest_framework import serializers

from miscs.models import *


class ContactUsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactUs
        fields = [
            "user",
            "name",
            "email",
            "phone_number",
            "message",
        ]


class CarouselCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = CarouselCategory
        fields = [
            "id",
            "name",
            "slug",
        ]


class CarouselSerializer(serializers.ModelSerializer):

    category = CarouselCategorySerializer()

    class Meta:
        model = Carousel
        fields = [
            "id",
            "title",
            "image",
            "small_image",
            "link",
            "button_text",
            "category",
            "order",
        ]


class EzyschoolingActivitySerializer(serializers.ModelSerializer):

    class Meta:
        model = Activity
        fields = [
            "id",
            "videos",
            "image",
            "link",
            "button_text",
            "order",
        ]


class EzySchoolingNewsArticleSerializer(serializers.ModelSerializer):

    class Meta:
        model = EzySchoolingNewsArticle
        fields = [
            "id",
            "image",
            "link",
            "order",
        ]


class CompetitionCarouselCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = CompetitionCarouselCategory
        fields = [
            "id",
            "name",
            "slug",
        ]


class CompetitionCarouselSerializer(serializers.ModelSerializer):

    category = CompetitionCarouselCategorySerializer()

    class Meta:
        model = CompetitionCarousel
        fields = [
            "id",
            "parent_name",
            "child_name",
            "slug",
            "category",
            "image",
        ]


class OnlineEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = OnlineEvent
        fields = [
            "title",
            "url",
            "description",
            "speaker_name",
            "speaker_photo",
            "event_date",
            "start_time",
            "end_time"
        ]


class AchieverSerializer(serializers.ModelSerializer):
    class Meta:
        model = Achiever
        fields = [
            "child_name",
            "parent_name",
            "phone",
            "description",
        ]

    def validate_parent_name(self, value):
        return value.title()

    def validate_child_name(self, value):
        return value.title()


class TalentHuntSubmissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentHuntSubmission
        fields = [
            "id",
            "title",
            "referrer",
            "video",
            "photo",
            "slug",
            "child_name",
            "parent_name",
            "phone",
            "email",
            "description",
        ]

        extra_kwargs = {
            'slug': {
                'read_only': True
            }
        }

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["likes_count"] = instance.likes.count()
        response["view_count"] = instance.views.count()
        return response


class TalentHuntSubmissionsDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = TalentHuntSubmission
        fields = [
            "title",
            "video",
            "photo",
            "child_name",
            "parent_name",
            "phone",
            "email",
            "description",
            "is_winner",
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["likes_count"] = instance.likes.count()
        response["referrals"] = instance.referrals.count()
        response["view_count"] = instance.views.count()
        if "request" in self.context and self.context["request"].user \
                and self.context["request"].user.is_authenticated:
            response["like_status"] = instance.like_status
        return response


class FaqAnswerSerializer(serializers.ModelSerializer):

    class Meta:
        model = FaqAnswer
        fields = (
            "answer",
        )


class FaqCategorySerializer(serializers.ModelSerializer):

    class Meta:
        model = FaqCategory
        fields = (
            "title",
        )


class FaqQuestionSerializer(serializers.ModelSerializer):
    faq_answer = FaqAnswerSerializer(many=True)
    category = FaqCategorySerializer()

    class Meta:
        model = FaqQuestion
        fields = (
            "title",
            "faq_answer",
            "category",
        )


class AdmissionGuidanceSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionGuidance
        fields = (
            "parent_name",
            "phone",
            "email",
            "dob",
            "target_region",
            "message",
            "budget",
            "slot"
        )

    def validate_parent_name(self, value):
        return value.title()

    def validate_target_region(self, value):
        return value.title()


class AdmissionGuidanceSlotSerializer(serializers.ModelSerializer):
    class Meta:
        model = AdmissionGuidanceSlot
        fields = [
            "id",
            "day",
            "time_slot",
            "event_date"
        ]

    def to_representation(self, instance):
        response = super().to_representation(instance)
        response["day"] = instance.get_day_display()
        response["time_slot"] = instance.time_slot.strftime("%I:%M %p")
        response["event_date"] = instance.event_date.strftime("%d-%m-%Y")
        return response


class AdmissionAlertSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdmissionAlert
        fields = [
            "name",
            "email",
            "phone_no",
            "region",
        ]

class AdmissionGuidanceProgrammeSerializer(serializers.ModelSerializer):

    class Meta:
        model = AdmissionGuidanceProgramme
        fields = [
            "name",
            "email",
            "phone_no",
            "region",
        ]


class SurveyChoiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = SurveyChoices
        fields = [
            "id",
            "name",
        ]

class SurveyQuestionSerializer(serializers.ModelSerializer):
    choices = SurveyChoiceSerializer(many=True)

    class Meta:
        model = SurveyQuestions
        fields = [
            "id",
            "label",
            "choices",
        ]

class SurveyCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = SurveyResponses
        fields = [
            "question",
            "answer",
            "taker",
        ]


class WebinarRegistrationSeralizer(serializers.ModelSerializer):

    class Meta:
        model = WebinarRegistrations
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "school_name",
            "designation",
            "city"
        ]

class SponsorsRegistrationsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SponsorsRegistrations
        fields = [
            "id",
            "name",
            "email",
            "phone",
            "companyname",
            "website_link"
        ]

class PastAndCurrentImpactinarsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastAndCurrentImpactinars
        fields = [
            "id",
            "title",
            "descriptions",
            "is_current",
            "video_link",
            "photo",
            "held_on"
        ]


class InvitedPrincipalsSerializer(serializers.ModelSerializer):
    class Meta:
        model = InvitedPrincipals
        fields = [
            "id",
            "name",
            "designation",
            "school_name",
            "photo",
            "about_principal"
        ]

class TestimonialsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Testimonials
        fields = [
            "id",
            "name",
            "message",
            "designation",
            "is_school",
            "photo"
        ]


class OurSponsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = OurSponsers
        fields = [
            "id",
            "name",
            "photo",
            "website_link",
        ]


class EzyschoolingEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model= EzyschoolingEmployees
        fields=[
            "id",
            "name",
           "photo",
           "designation",
           "linkedinurl",
        ]

class UnsubscribeEmailSerializer(serializers.ModelSerializer):
   class Meta:
       model = UnsubscribeEmail
       fields = [
           "email",
       ]
