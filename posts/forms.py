from django.forms import ModelForm, Textarea
from .models import Post, Comment


class PostForm(ModelForm):
    class Meta:
        model = Post
        fields = ["group", "text", "image"]
        help_texts = {
            "group": "Выберите группу для поста",
            "text": "Введите текст поста",
            "image": "Добавьте картинку",
        }


class CommentForm(ModelForm):
    class Meta:
        model = Comment
        fields = ["text"]
        help_texts = {"text": "Введите текст комментария"}
        widgets = {"text": Textarea()}
