from django import forms

from .models import *


class ArticleForm(forms.Form):
    title = forms.CharField(
        max_length = 128,
        required = True,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'id': 'article-input-title',
                # 'v-model': 'title.value',
            }
        )
    )
    field = forms.ChoiceField(
        choices = ARTICLE_FIELD_CHOICES,
        required = True,
        widget = forms.Select(
            attrs = {
                'class': 'form-select',
                'id': 'article-input-field',
                'v-model': 'field.value',
            }
        )
    )
    fieldname = forms.CharField(
        max_length = 128,
        required = False,
        widget = forms.TextInput(
            attrs = {
                'class': 'form-control',
                'id': 'article-input-fieldname',
                'v-model': 'fieldname.value',
            }
        )
    )
    definition = forms.CharField(
        required = True,
        widget = forms.Textarea(
            attrs = {
                'class': 'form-control',
                'id': 'article-input-definition',
                'v-model': 'definition.value',
                'rows': 10,
            }
        )
    )
    description = forms.CharField(
        required = False,
        widget = forms.Textarea(
            attrs = {
                'class': 'form-control',
                'id': 'article-input-description',
                'v-model': 'description.value',
                'rows': 20,
            }
        )
    )


class ArticleDeleteForm(forms.Form):
    deltype = forms.ChoiceField(
        label = '삭제 유형',
        label_suffix = '',
        choices = DELETE_TYPE_CHOICES,
        widget = forms.Select(
            attrs = {
                'class': 'form-select',
                'id': 'deltype',
                'v-model': 'remove.type',
            }
        )
    )
    delwhy = forms.ChoiceField(
        label = '삭제 사유',
        label_suffix = '',
        choices = DELETE_WHY_CHOICES,
        widget = forms.Select(
            attrs = {
                'class': 'form-select',
                'id': 'delwhy',
                'v-model': 'remove.why',
            }
        )
    )
    delwhydetail = forms.CharField(
        label = '사유 상세',
        label_suffix = '',
        widget = forms.Textarea(
            attrs = {
                'class': 'form-control',
                'id': 'delwhy',
                'v-model': 'remove.whydetail',
                'rows': 5,
            }
        )
    )
    BAN_CHOICES = [
        (True, 'True'),
        (False, 'False'),
    ]
    banheadword = forms.ChoiceField(
        label = '표제어 재등록 금지',
        label_suffix = '',
        choices = BAN_CHOICES,
        widget = forms.RadioSelect(
            attrs = {
                'id': 'banheadword',
                'v-model': 'remove.banheadword',
            }
        )
    )
    banuser = forms.ChoiceField(
        label = '편집자 사용 정지',
        label_suffix = '',
        choices = BAN_CHOICES,
        widget = forms.RadioSelect(
            attrs = {
                'id': 'banuser',
                'v-model': 'remove.banuser',
            }
        )
    )
