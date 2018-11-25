import json
import random
import logging
import requests
import argparse
from time import time
from Queue import Queue
from threading import Thread


ENV_URL = 'http://sample.com/api/'
USER_ENDPOINT = ENV_URL + 'get-customer-list'
POST_ENDPOINT = ENV_URL + 'get-post-list'
COMMENT_ENDPOINT = ENV_URL + 'add-comment'

COMMENT_CONTENT = 'COMMENT MEHMET KAYKISIZ'
NAME = 'MEHMET KAYKISIZ'


class User(object):
    def __init__(self, user_id, token):
        self.user_id = user_id
        self.token = token


class Post(object):
    def __init__(self, post_id, title, details, created_date):
        self.post_id = post_id
        self.title = title
        self.details = details
        self.created_date = created_date


class Comment(object):
    def __init__(self, token, post_id, comment, name):
        self.token = token
        self.post_id = post_id
        self.comment = comment
        self.name = name


class Commenter(object):
    def __init__(self):
        self.all_users = self.get_random_users()
        self.all_posts = self.get_random_posts()
        self.USER_LIMIT, self.POST_LIMIT = self.check_args()
        super(Commenter, self).__init__()

    @staticmethod
    def get_random_users():
        users = []
        response = requests.get(USER_ENDPOINT)
        if response.ok:
            user_info_list = json.loads(response.content)
            for user_info in user_info_list:
                users.append(User(user_info.get('id'), user_info.get('token')))
        return users

    @staticmethod
    def get_random_posts():
        posts = []
        response = requests.get(POST_ENDPOINT)
        if response.ok:
            post_info_list = json.loads(response.content)
            for post_info in post_info_list:
                posts.append(Post(post_info.get('id'), post_info.get('title'), post_info.get('details'),
                                  post_info.get('created_date')))
        return posts

    @staticmethod
    def check_args():
        parser = argparse.ArgumentParser()
        parser.add_argument('--user_limit', help='User limit for per post', type=int, default=0)
        parser.add_argument('--post_limit', help='Post limit', type=int, default=0)
        args = parser.parse_args()
        return args.user_limit, args.post_limit

    @staticmethod
    def send_comment(queue):
        while True:
            comment = queue.get()
            data = {
                'token': comment.token,
                'postId': comment.post_id,
                'comment': comment.comment,
                'name': comment.name
            }
            response = requests.post(COMMENT_ENDPOINT, data)
            queue.task_done()
            if not response.ok:
                logging.exception("[SEND COMMENT]: Request not succeeded.")
                raise Exception(response.text)
            content = json.loads(response.content)
            if not content.get('success'):
                logging.exception("[SEND COMMENT]: Err: {}".format(content.get('msg')))
                raise Exception(content.get('msg'))

    def run(self):
        users_for_per_post_queue = []
        posts_for_comments = random.sample(self.all_posts, self.POST_LIMIT)
        for index, post in enumerate(posts_for_comments):
            users_for_per_post_queue.append(Queue())
            # i did post based grouping but this may vary depending on business needs.
            t = Thread(target=self.send_comment, args=(users_for_per_post_queue[index],))
            t.daemon = True
            t.start()

            users_for_post = random.sample(self.all_users, self.USER_LIMIT)
            for user in users_for_post:
                comment = Comment(user.token, post.post_id, COMMENT_CONTENT, NAME)
                users_for_per_post_queue[index].put(comment)

        for queue in users_for_per_post_queue:
            queue.join()


if __name__ == "__main__":
    """
    Required to "requests" library on this project with python.2.7,
    please follow next line;
    
    $ pip install requests
    
    Run command:
    
    python manage.py commenter.py --user_limit=100 --post_limit=3 
    
    """
    start_time = time()
    Commenter().run()
    logging.info("lasted %s seconds" % (time() - start_time))
