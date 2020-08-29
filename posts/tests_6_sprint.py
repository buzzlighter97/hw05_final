from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from .models import Post, User, Group, Follow, Comment
from django.urls import reverse
import time
from django.core.files.uploadedfile import SimpleUploadedFile


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

    def test_img_in_post(self):
        """Tests that the added image
        is in the post"""

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )

        img = SimpleUploadedFile(
            name="some.gif", content=small_gif, content_type="image/gif"
        )
        response_new = self.authorised_client.post(
            reverse("new_post"),
            {"text": "test text", "group": self.test_group_1.id, "image": img},
        )
        test_post = Post.objects.all().first()
        response_post = self.authorised_client.get(
            reverse(
                "post",
                kwargs={"username": test_post.author.username, "post_id": test_post.id},
            )
        )
        self.assertContains(response_post, "img")

    def test_img_in_profile_and_group(self):
        """Tests that added image of the post is
        visible on the profile and on the group pages"""

        small_gif = (
            b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x00\x00\x00\x21\xf9\x04"
            b"\x01\x0a\x00\x01\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02"
            b"\x02\x4c\x01\x00\x3b"
        )

        img = SimpleUploadedFile(
            name="some.gif", content=small_gif, content_type="image/gif"
        )
        response_new = self.authorised_client.post(
            reverse("new_post"),
            {"text": "test text", "group": self.test_group_1.id, "image": img},
        )
        test_post = Post.objects.all().first()
        response_profile = self.authorised_client.get(
            reverse("profile", kwargs={"username": test_post.author.username})
        )
        response_group = self.authorised_client.get(
            reverse("group", kwargs={"slug": self.test_group_1.slug})
        )

        self.assertContains(response_profile, "img")
        self.assertContains(response_group, "img")

    def test_file_is_image(self):
        """Tests that added file is an image file"""

        img = SimpleUploadedFile(
            name="some.txt", content=b"abc", content_type="text/plane"
        )
        response_new = self.authorised_client.post(
            reverse("new_post"),
            {"text": "test text", "group": self.test_group_1.id, "image": img},
        )
        text = "Загрузите правильное изображение. Файл, который вы загрузили, поврежден или не является изображением."
        self.assertFormError(response_new, "form", "image", [text])

    def test_cache(self):
        '''Tests that cache is saving
        index page for 20 sec'''

        response_index = self.authorised_client.get(reverse('index'))
        response_new = self.authorised_client.post(
            reverse("new_post"),
            {"text": "test text 1", "group": self.test_group_1.id},
        )
        self.assertNotContains(response_index, 'test text')

        time.sleep(20)

        response_index = self.authorised_client.get(reverse('index'))
        self.assertContains(response_index, 'test text')

    def test_auth_follow(self):
        """Tests that the authorised user
        is able to follow and unfollow
        another user"""

        response_follow = self.authorised_client.get(
            reverse("profile_follow", kwargs={"username": "non_authorised_user"})
        )
        following = Follow.objects.filter(
            author=self.non_authorised_user, user=self.authorised_user
        ).exists()
        self.assertTrue(following)

        response_unfollow = self.authorised_client.get(
            reverse("profile_unfollow", kwargs={"username": "non_authorised_user"})
        )
        following = Follow.objects.filter(
            author=self.non_authorised_user, user=self.authorised_user
        ).exists()
        self.assertFalse(following)

    def new_post_follow_visible(self):
        """Tests that the new post
        is visible on the follow pages of followers
        and is not visible on the follow pages of 
        non-followers"""

        another_auth_client = Client()
        another_auth_user = User.objects.create(username="another_auth_user")
        another_auth_client.force_login(another_auth_user)

        response_follow = self.authorised_client.get(
            reverse("profile_follow", kwargs={"username": "non_authorised_user"})
        )
        post_auth_user = Post.objects.create(
            text="test text auth",
            author=self.non_authorised_user,
            group=self.test_group_1,
        )

        follow_response = self.authorised_client.get(reverse("follow_index"))
        not_follow_response = another_auth_client.get(reverse("follow_index"))

        self.assertContains(follow_response, "test text auth")
        self.assertNotContains(not_follow_response, "test text auth")

    def auth_comment(self):
        """Tests that the authorised user
        is able to add a comment and unauthorised
        is not"""

        test_post = Post.objects.create(text="test text", author=self.authorised_user)
        auth_comment = self.authorised_client.post(
            reverse(
                "add_comment",
                kwargs={"username": self.authorised_user, "post_id": test_post.pk},
            ),
            {
                "post": test_post,
                "author": self.authorised_user,
                "text": "test_auth_comment",
            },
        )

        non_auth_comment = self.non_authorised_client.post(
            reverse(
                "add_comment",
                kwargs={"username": "non_authorised_user", "post_id": test_post.pk},
            ),
            {
                "post": test_post,
                "author": self.authorised_user,
                "text": "test_non_auth_comment",
            },
        )

        test_post_response = response_post = self.authorised_client.get(
            reverse(
                "post", kwargs={"username": "authorised_user", "post_id": test_post.id}
            )
        )

        self.assertContains(test_post_response, "test_auth_comment")
        self.assertNotContains(test_post_response, "test_non_auth_comment")
