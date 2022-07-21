from django.db import models
from django.db.models.functions import Lower

from user.models import User

# Create your models here.

# Dictionary
ARTICLE_FIELD_CHOICES = [
    ('00', 'Economics / Finance / Investment'),
    ('01', 'Econometrics / Statistics'),
    ('02', 'Computer Engineering / Data Science'),
    ('99', 'etc'),
]

ARTICLE_FIELD_CHOICES_DICT = {c[0]: c[1] for c in ARTICLE_FIELD_CHOICES}

# delete
DELETE_TYPE_CHOICES = [
    ('00', '현재 버전 삭제'),
    ('01', '모든 버전 삭제'),
    ('02', '표제어 삭제'),
]

DELETE_TYPE_CHOICES_DICT = {c[0]: c[1] for c in DELETE_TYPE_CHOICES}

DELETE_WHY_CHOICES = [
    ('00', '사유1'),
    ('01', '사유2'),
    ('02', '사유3'),
    ('99', 'etc'),
]

DELETE_WHY_CHOICES_DICT = {c[0]: c[1] for c in DELETE_WHY_CHOICES}


class Headword(models.Model):
    name = models.CharField(max_length=128, null=False, blank=False, unique=True)
    is_published = models.BooleanField(null=False, blank=False, default=False)
    is_banned = models.BooleanField(null=False, blank=False, default=False)

    class Meta:
        models.UniqueConstraint(
            Lower('name'),
            name = 'lowercase of name',
        )

# Article
class Article(models.Model):
    # headword = models.CharField(max_length=128, null=False, blank=False)
    title = models.ForeignKey(
        Headword,
        related_name = 'article',
        on_delete = models.CASCADE,
    )
    field = models.CharField(
        max_length = 2,
        choices = ARTICLE_FIELD_CHOICES,
        null = True, blank = True,
    )
    fieldname = models.CharField(max_length=128, null=False, blank=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields = ['title','fieldname'],
                name = 'unique article',
            ),
        ]


# History
class History(models.Model):
    # status
    is_draft = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now_add=True)

    is_cancelled = models.BooleanField(default=False)
    cancelled_by = models.ForeignKey(
        User,
        related_name = 'cancel',
        on_delete = models.CASCADE,
        null = True, blank = True
    )
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancelled_why = models.CharField(max_length=2, null=True, blank=True)
    cancelled_why_detail = models.TextField(null=True, blank=True)

    # description
    editor = models.ForeignKey(
        User,
        related_name = 'update',
        on_delete = models.CASCADE,
    )
    article = models.ForeignKey(
        Article,
        related_name = 'history',
        on_delete = models.CASCADE,
    )
    abstract = models.TextField(null=False, blank=False)
    definition = models.TextField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    keywords = models.ManyToManyField(
        Headword,
        blank=True, symmetrical=False,
        related_name='tagged_by',
    )

    # data = models.JSONField()

    class Meta:
        get_latest_by = 'updated_at'
