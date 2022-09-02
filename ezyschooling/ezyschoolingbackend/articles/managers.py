from django.db import models


class ExpertArticleQuerySet(models.QuerySet):
    """Personalized queryset created to improve model usability"""

    def get_published(self):
        """Returns only the published items in the current queryset."""
        return self.filter(status="P")

    def get_drafts(self):
        """Returns only the items marked as DRAFT in the current queryset."""
        return self.filter(status="D")

    def get_list_items(self):
        return self.only(
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "slug",
            "board",
            "board__id",
            "board__name",
            "board__min_age",
            "board__max_age",
            "board__slug",
            "board__thumbnail",
            "sub_category",
            "sub_category__id",
            "sub_category__name",
            "sub_category__slug",
            "sub_category__thumbnail",
            "created_by",
            "created_by__id",
            "created_by__name",
            "created_by__profile_picture",
            "views",
            "timestamp",
        )

    def get_detail_items(self):
        return self.only(
            "id",
            "title",
            "mini_title",
            "thumbnail",
            "slug",
            "board",
            "board__id",
            "board__name",
            "board__min_age",
            "board__max_age",
            "board__slug",
            "board__thumbnail",
            "sub_category",
            "sub_category__id",
            "sub_category__name",
            "sub_category__slug",
            "sub_category__thumbnail",
            "created_by",
            "created_by__id",
            "created_by__name",
            "created_by__profile_picture",
            "description",
            "views",
            "tags",
            "timestamp",
        )

    def get_foreignkey_select_related(self):
        return self.select_related("board", "sub_category", "created_by")

    def get_list_api_items(self):
        return self.get_published().get_list_items().get_foreignkey_select_related()

    def get_staff_user_list_api_items(self):
        return self.get_list_items().get_foreignkey_select_related()

    def get_detail_api_items(self):
        return self.get_published().get_detail_items().get_foreignkey_select_related()

    def get_staff_user_detail_api_items(self):
        return self.get_detail_items().get_foreignkey_select_related()


class ExpertArticleCommentQuerySet(models.QuerySet):
    """Personalized queryset created to improve model usability"""

    def get_list_items(self):
        return self.only(
            "id",
            "comment",
            "article",
            "timestamp",
            "parent",
            "parent__id",
            "parent__name",
            "parent__photo",
            "parent__slug",
            "expert",
            "expert__id",
            "expert__user",
            "expert__name",
            "expert__slug",
            "expert__profile_picture",
            "expert__is_expert_panel",
            "anonymous_user",
        )

    def like_comment_count(self):
        return self.annotate(
            likes_count=models.Count("likes", distinct=True),
            children_comment_count=models.Count(
                "user_expert_article_comment_childrens", distinct=True
            ),
        )

    def get_parent_expert_select_related(self):
        return self.select_related("parent", "expert")

    def get_list_api_items(self):
        return (
            self.get_list_items()
            .get_parent_expert_select_related()
            .like_comment_count()
        )
