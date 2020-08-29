from django.shortcuts import render, get_object_or_404, get_list_or_404
from django.views.generic import CreateView
from .forms import PostForm, CommentForm
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow
from django.shortcuts import redirect
import datetime as dt
from django.core.paginator import Paginator


def index(request):
    post_list = Post.objects.all()
    paginator = Paginator(post_list, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(request, "index.html", {"page": page, "paginator": paginator})


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)

    posts_list = group.groups_posts.all()
    paginator = Paginator(posts_list, 10)

    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)
    return render(
        request, "group.html", {"group": group, "page": page, "paginator": paginator}
    )


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if not form.is_valid():
        form_title = "Добавить запись"
        submit_button = "Добавить"
        return render(
            request,
            "new_post.html",
            {"form": form, "submit_button": submit_button, "form_title": form_title},
        )
    post = form.save(commit=False)
    post.author = request.user
    post.save()
    return redirect("index")


def profile(request, username):

    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    following = (
        request.user.is_authenticated
        and Follow.objects.filter(author=author, user=request.user).exists()
    )

    posts_count = len(post_list)
    followers_count = Follow.objects.filter(author=author).count
    following_count = Follow.objects.filter(user=author).count

    context = {
        "page": page,
        "paginator": paginator,
        "author": author,
        "posts_count": posts_count,
        "following": following,
        "followers_count": followers_count,
        "following_count": following_count,
    }

    return render(request, "profile.html", context)


def post(request, username, post_id):

    author = get_object_or_404(User, username=username)
    posts_count = author.posts.count()
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    comments = post.comments.all()
    form = CommentForm(request.POST or None)

    followers_count = Follow.objects.filter(author=author).count
    following_count = Follow.objects.filter(user=author).count

    context = {
        "author": author,
        "post": post,
        "posts_count": posts_count,
        "comments": comments,
        "form": form,
        "followers_count": followers_count,
        "following_count": following_count,
    }

    return render(request, "post.html", context)


@login_required
def post_edit(request, username, post_id):

    post = get_object_or_404(Post, pk=post_id, author__username=username)
    if request.user != post.author:
        return redirect("post", username=username, post_id=post_id)
    form = PostForm(request.POST or None, files=request.FILES or None, instance=post)
    if not form.is_valid():
        form_title = "Редактировать запись"
        submit_button = "Сохранить"
        context = {
            "post": post,
            "form": form,
            "submit_button": submit_button,
            "form_title": form_title,
        }
        return render(request, "new_post.html", context)
    post = form.save(commit=False)
    post.author = request.user
    post.group = form.cleaned_data["group"]
    post.text = form.cleaned_data["text"]
    post.save()
    return redirect("post", username=post.author.username, post_id=post.pk)


def page_not_found(request, exception):
    return render(request, "misc/404.html", {"path": request.path}, status=404)


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, author__username=username, pk=post_id)
    form = CommentForm(request.POST or None)
    if not form.is_valid():
        author = get_object_or_404(User, username=username)
        posts_count = author.posts.count()
        comments = post.comments.all()
        followers_count = Follow.objects.filter(author=author).count
        following_count = Follow.objects.filter(user=author).count

        context = {
            "author": author,
            "post": post,
            "posts_count": posts_count,
            "comments": comments,
            "form": form,
            "followers_count": followers_count,
            "following_count": following_count,
        }

        return render(request, "post.html", context)
    comment = form.save(commit=False)
    comment.author = request.user
    comment.post = post
    comment.save()
    return redirect("post", username=post.author.username, post_id=post.pk)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(posts, 10)
    page_number = request.GET.get("page")
    page = paginator.get_page(page_number)

    context = {"page": page, "paginator": paginator, "page_number": page_number}
    return render(request, "follow.html", context)


@login_required
def profile_follow(request, username):
    user = request.user
    author = get_object_or_404(User, username=username)
    if user != author:
        follow = Follow.objects.get_or_create(user=user, author=author)
    return redirect("profile", username=username)


@login_required
def profile_unfollow(request, username):
    user = request.user
    author = User.objects.get(username=username)
    follow = Follow.objects.filter(user=user, author=author)
    follow.delete()
    return redirect("profile", username=username)
