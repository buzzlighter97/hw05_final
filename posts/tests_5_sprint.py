from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Post, User, Group
from django.urls import reverse


class TestsOfFifthSprint(TestCase):
    def setUp(self):
        self.authorised_client = Client()
        self.non_authorised_client = Client()

        self.non_authorised_user = User.objects.create_user(
            username="non_authorised_user"
        )
        self.authorised_user = User.objects.create_user(username="authorised_user")
        self.authorised_client.force_login(self.authorised_user)

        self.test_group_1 = Group.objects.create(
            title="Тестовая группа 1",
            slug="testgroup1",
            description="Это группа для тестирования 1",
        )
        self.test_group_2 = Group.objects.create(
            title="Тестовая группа 2",
            slug="testgroup2",
            description="Это группа для тестирования 2",
        )

    def check_post_in_page(self, url, text, user, group):
        """Checks that the post in url has
        text, user and group atributes"""

        response = self.authorised_client.get(url)
        paginator = response.context.get("paginator")
        if paginator is not None:
            self.assertEqual(paginator.count, 1)
            post = response.context["page"][0]
        else:
            post = response.context["post"]
        self.assertEqual(post.text, text)
        self.assertEqual(post.author, user)
        self.assertEqual(post.group, group)

    def test_profile_page(self):
        """Test that profile page is created
        after registration"""

        response_profile = self.authorised_client.get(
            reverse("profile", kwargs={"username": self.authorised_user})
        )
        self.assertEqual(response_profile.status_code, 200)

    def test_auth_user_new_post(self):
        """Test that authorised user is
        able to create new post"""
        posts_count_before = self.authorised_user.posts.all().count()
        response_new = self.authorised_client.post(
            reverse("new_post"),
            data={"text": "test new post", "group": self.test_group_1.id},
            follow=True,
        )
        posts_count_after = self.authorised_user.posts.all().count()

        test_post = Post.objects.all().first()
        response_post = self.client.get(
            reverse(
                "post", kwargs={"username": "authorised_user", "post_id": test_post.id}
            )
        )

        self.assertEqual(response_new.status_code, 200)
        self.assertEqual(posts_count_after - posts_count_before, 1)
        self.check_post_in_page(
            reverse(
                "post", kwargs={"username": "authorised_user", "post_id": test_post.id}
            ),
            test_post.text,
            test_post.author,
            test_post.group,
        )

    def test_non_auth_redirect(self):
        """Test that non authorised user is
        redirected to login page"""

        login = reverse("login")
        new = reverse("new_post")
        posts_count_before = Post.objects.all().count()
        response_new = self.non_authorised_client.get(new, follow=True)
        posts_count_after = Post.objects.all().count()

        self.assertRedirects(response_new, f"{login}?next={new}")
        self.assertEqual(posts_count_after - posts_count_before, 0)

    def test_new_post_visible(self):
        """Test that the new post is
        visible on all linked pages"""

        test_post = Post.objects.create(
            author=self.authorised_user, text="test text", group=self.test_group_1
        )

        pages_list = [
            reverse("index"),
            reverse("profile", kwargs={"username": test_post.author.username}),
            reverse(
                "post",
                kwargs={"username": test_post.author.username, "post_id": test_post.id},
            ),
            reverse("group", kwargs={"slug": self.test_group_1.slug}),
        ]
        for url in pages_list:
            self.check_post_in_page(
                url, test_post.text, test_post.author, test_post.group
            )

    def test_auth_user_edit_visible(self):
        """Test that the edited post is
        visible on all linked pages"""

        test_post = Post.objects.create(
            author=self.authorised_user, text="test text", group=self.test_group_1
        )
        pages_list = [
            reverse("index"),
            reverse("profile", kwargs={"username": test_post.author.username}),
            reverse(
                "post",
                kwargs={"username": test_post.author.username, "post_id": test_post.id},
            ),
            reverse("group", kwargs={"slug": self.test_group_2.slug}),
        ]
        response_edit_post = self.authorised_client.post(
            reverse(
                "post_edit",
                kwargs={"username": test_post.author.username, "post_id": test_post.id},
            ),
            data={"text": "edited text", "group": self.test_group_2.id},
            follow=True,
        )
        test_post = Post.objects.get(id=test_post.id)
        for url in pages_list:
            self.check_post_in_page(
                url, test_post.text, test_post.author, test_post.group
            )
